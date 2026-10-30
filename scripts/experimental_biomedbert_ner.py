"""Leakage-safe fine-tuning of BiomedBERT on CHIA development groups only.

Uses a standard BIO head as an explicit, reproducible baseline. CHIA's nested,
overlapping and discontinuous annotations are flattened for training by keeping
the longest overlapping contiguous mention, but the original exact-span scorer
is retained at evaluation so this limitation remains visible.
"""
from __future__ import annotations

from collections import defaultdict
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader
from sklearn.model_selection import GroupKFold
from transformers import AutoModelForTokenClassification, AutoTokenizer

from experimental_hybrid_ner import KINDS, metrics

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
MAX_LENGTH = 256
STRIDE = 64
EPOCHS = 3
BATCH_SIZE = 8
LABELS = ["O"] + [f"{prefix}-{kind}" for kind in KINDS for prefix in ("B", "I")]
LABEL2ID = {label: i for i, label in enumerate(LABELS)}
ID2LABEL = {i: label for label, i in LABEL2ID.items()}


def seed_everything(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def flattened_spans(record):
    spans = []
    for item in record["gold"]:
        if len(item["spans"]) != 1:
            continue
        start, end = item["spans"][0]
        spans.append((start, end, item["kind"]))
    # BIO can represent only one flat label per token. Prefer the longer span
    # where annotations overlap, following published CHIA NER preprocessing.
    accepted = []
    for candidate in sorted(spans, key=lambda x: (-(x[1] - x[0]), x[0], x[2])):
        if any(candidate[0] < end and start < candidate[1] for start, end, _ in accepted):
            continue
        accepted.append(candidate)
    return sorted(accepted)


def encode_record(tokenizer, record, with_labels):
    text = record["text"]
    enc = tokenizer(
        text, max_length=MAX_LENGTH, truncation=True, stride=STRIDE,
        return_overflowing_tokens=True, return_offsets_mapping=True,
        padding=False,
    )
    spans = flattened_spans(record) if with_labels else []
    chunks = []
    for input_ids, attention_mask, offsets in zip(
        enc["input_ids"], enc["attention_mask"], enc["offset_mapping"]
    ):
        chunk = {"input_ids": input_ids, "attention_mask": attention_mask, "offsets": offsets}
        if with_labels:
            labels = [LABEL2ID["O"]] * len(input_ids)
            # Ignore special tokens and partial entities cut at chunk edges.
            labels = [(-100 if s == e else label) for (s, e), label in zip(offsets, labels)]
            by_span = []
            for start, end, kind in spans:
                members = [i for i, (s, e) in enumerate(offsets)
                           if s < e and s >= start and e <= end]
                if not members:
                    continue
                if offsets[members[0]][0] != start or offsets[members[-1]][1] != end:
                    for i, (s, e) in enumerate(offsets):
                        if s < end and e > start:
                            labels[i] = -100
                    continue
                by_span.append((members, kind))
            for members, kind in by_span:
                if any(labels[i] == -100 for i in members):
                    continue
                labels[members[0]] = LABEL2ID[f"B-{kind}"]
                for i in members[1:]:
                    labels[i] = LABEL2ID[f"I-{kind}"]
            chunk["labels"] = labels
        chunks.append(chunk)
    return chunks


def collate(batch):
    result = {}
    for key, pad_value in (("input_ids", 0), ("attention_mask", 0), ("labels", -100)):
        result[key] = pad_sequence(
            [torch.tensor(row[key], dtype=torch.long) for row in batch],
            batch_first=True, padding_value=pad_value,
        )
    return result


def decode_record(model, tokenizer, record, device):
    chunks = encode_record(tokenizer, record, with_labels=False)
    accum = defaultdict(list)
    model.eval()
    with torch.no_grad():
        for chunk in chunks:
            input_ids = torch.tensor([chunk["input_ids"]], dtype=torch.long, device=device)
            mask = torch.tensor([chunk["attention_mask"]], dtype=torch.long, device=device)
            logits = model(input_ids=input_ids, attention_mask=mask).logits[0].float().cpu().numpy()
            for (start, end), vector in zip(chunk["offsets"], logits):
                if start < end:
                    accum[(start, end)].append(vector)
    tokens = []
    for (start, end), vectors in sorted(accum.items()):
        label = ID2LABEL[int(np.mean(vectors, axis=0).argmax())]
        tokens.append((label, start, end))
    spans = []
    current_kind = None
    current_start = current_end = None
    for label, start, end in tokens:
        if label.startswith("B-"):
            if current_kind:
                spans.append((current_kind, current_start, current_end))
            current_kind = label[2:]
            current_start, current_end = start, end
        elif label.startswith("I-") and current_kind == label[2:] and start <= current_end + 2:
            current_end = end
        else:
            if current_kind:
                spans.append((current_kind, current_start, current_end))
            current_kind = None
            if label.startswith("I-"):
                # Treat an orphan I-tag as a new mention instead of dropping it.
                current_kind = label[2:]
                current_start, current_end = start, end
    if current_kind:
        spans.append((current_kind, current_start, current_end))
    return spans


def main():
    records = [r for r in json.loads((ROOT / "data/annotations/chia/benchmark.json").read_text())
               if r["split"] == "development"]
    groups = np.asarray([r["group"] for r in records])
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Loading {MODEL_ID}; device={device}; max_length={MAX_LENGTH}; stride={STRIDE}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    predictions = [None] * len(records)
    fold_summary = []
    started = time.perf_counter()

    for fold, (train_idx, heldout_idx) in enumerate(
        GroupKFold(n_splits=5).split(records, groups=groups), 1
    ):
        seed_everything(731 + fold)
        train_chunks = [chunk for i in train_idx
                        for chunk in encode_record(tokenizer, records[i], with_labels=True)]
        model = AutoModelForTokenClassification.from_pretrained(
            MODEL_ID, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID,
            ignore_mismatched_sizes=True,
        ).to(device)
        loader = DataLoader(train_chunks, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate)
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
        step_count = 0
        for epoch in range(EPOCHS):
            model.train()
            running = 0.0
            for batch in loader:
                batch = {key: value.to(device) for key, value in batch.items()}
                optimizer.zero_grad(set_to_none=True)
                loss = model(**batch).loss
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                running += float(loss.detach().cpu())
                step_count += 1
            print(f"fold {fold}/5 epoch {epoch+1}/{EPOCHS} loss={running/max(1,len(loader)):.4f}", flush=True)
        fold_preds = []
        for i in heldout_idx:
            pred = decode_record(model, tokenizer, records[i], device)
            predictions[i] = pred
            fold_preds.append(pred)
        fold_scores, _ = metrics([records[i] for i in heldout_idx], fold_preds)
        fold_summary.append({"fold": fold, "train_records": len(train_idx),
                             "heldout_records": len(heldout_idx),
                             "heldout_groups": len(set(groups[heldout_idx])),
                             "steps": step_count, "micro": fold_scores["micro"]})
        print(f"fold {fold}/5 complete: heldout_F1={fold_scores['micro']['f1']:.3f}", flush=True)
        del model, optimizer, loader, train_chunks
        if device.type == "mps":
            torch.mps.empty_cache()

    scores, errors = metrics(records, predictions)
    summary = {
        "method": "BiomedBERT token classification, five-fold grouped out-of-fold evaluation",
        "base_model": MODEL_ID,
        "training_data": "CHIA development split only; held-out trial/near-duplicate groups excluded per fold",
        "test_split_used": False,
        "device": str(device), "max_length": MAX_LENGTH, "stride": STRIDE,
        "epochs": EPOCHS, "batch_size": BATCH_SIZE,
        "training_annotation_policy": "BIO flat tags; keep longest contiguous mention in overlaps; skip discontinuous mentions",
        "evaluation_policy": "original benchmark exact type and span; nested/overlapping and discontinuous gold retained",
        "records": len(records), "trials": len(set(r["nct_id"] for r in records)),
        "groups": len(set(groups)), "folds": fold_summary, "biomedbert": scores,
        "comparison": {
            "lightweight_token_ner_oof": json.loads((ROOT / "reports/extraction/hybrid_development.json").read_text())["token_ner"]["micro"],
            "saved_zero_shot_llm_dev": json.loads((ROOT / "reports/extraction/development.json").read_text())["llm"]["micro"],
            "saved_rules_dev": json.loads((ROOT / "reports/extraction/development.json").read_text())["rules"]["micro"],
        },
        "elapsed_seconds": time.perf_counter() - started,
        "limitations": [
            "small development set; exploratory only",
            "BIO cannot faithfully express CHIA nested, overlapping or discontinuous annotations",
            "not evaluated on the frozen test split and not eligible for release",
            "base model pretraining can still overlap public biomedical source text; no label leakage from the hosted CHIA fine-tune is used",
        ],
    }
    out = ROOT / "reports/extraction"
    (out / "biomedbert_development.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "biomedbert_development_errors.json").write_text(json.dumps(errors, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
