"""Development-only grouped-CV token NER with an optional regex comparison.

The design borrows the criterion-level, task-specific IE approach used by
Clinical-Trial-Parser: preserve criterion boundaries and source offsets, predict
entity spans, and compare against existing deterministic regex candidates.
This deliberately uses only CHIA development annotations and installed
scikit-learn; frozen test annotations never enter training or scoring.
"""
from __future__ import annotations

from collections import Counter
import json
import re
import time
from pathlib import Path

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from clinical_trial_risk.llm.extract import rules as regex_rules

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("Measurement", "Value", "Temporal")
TOKEN_RE = re.compile(r"\w+(?:[’'-]\w+)*|[^\w\s]", re.UNICODE)
BOUNDARY_RE = re.compile(r"[\n;•●▪]+")
TIME_RE = re.compile(r"\b(?:before|after|during|within|prior|following|currently|concurrent|acute|chronic|past|recent|at screening|at baseline)\b", re.I)
NUMBER_RE = re.compile(r"(?:[<>]=?|≥|≤|\bbetween\b|\bat least\b|\bno more than\b|\bunder\b|\bover\b)?\s*\d+(?:[.,]\d+)?", re.I)
UNIT_RE = re.compile(r"\b(?:years?|months?|weeks?|days?|hours?|kg|mg|g|mmhg|mmol|cm|%|ul|µl|ml|/d[lL]|\bULN\b)\b", re.I)


def tokenize(text: str):
    return [(m.group(), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]


def word_shape(word: str) -> str:
    chars = []
    for c in word:
        kind = "A" if c.isupper() else "a" if c.islower() else "0" if c.isdigit() else c
        if not chars or chars[-1] != kind:
            chars.append(kind)
    return "".join(chars)[:12]


def features(text: str, tokens):
    out = []
    boundaries = [m.end() for m in BOUNDARY_RE.finditer(text)]
    for i, (word, start, end) in enumerate(tokens):
        low = word.lower()
        f = {
            "bias": 1,
            "word": low,
            "shape": word_shape(word),
            "prefix2": low[:2], "prefix3": low[:3],
            "suffix2": low[-2:], "suffix3": low[-3:],
            "is_upper": word.isupper(), "is_title": word.istitle(),
            "has_digit": any(c.isdigit() for c in word),
            "is_punct": bool(re.fullmatch(r"\W+", word)),
            "near_number": bool(NUMBER_RE.search(text[max(0, start - 40):min(len(text), end + 40)])),
            "near_unit": bool(UNIT_RE.search(text[max(0, start - 40):min(len(text), end + 40)])),
            "near_temporal": bool(TIME_RE.search(text[max(0, start - 60):min(len(text), end + 60)])),
            "criterion_start": any(start >= p and start - p <= 32 and not text[p:start].strip()
                                    for p in boundaries),
            "criterion_end": any(p <= end and end - p <= 2
                                 for p in (m.start() for m in BOUNDARY_RE.finditer(text))),
        }
        for delta in (-2, -1, 1, 2):
            j = i + delta
            if 0 <= j < len(tokens):
                neighbour = tokens[j][0].lower()
                f[f"w{delta}"] = neighbour
                if abs(delta) == 1:
                    f[f"shape{delta}"] = word_shape(tokens[j][0])
            else:
                f[f"w{delta}"] = "<BOS>" if j < 0 else "<EOS>"
        out.append(f)
    return out


def tags_for(record, tokens):
    labels = ["O"] * len(tokens)
    aligned = 0
    for item in record["gold"]:
        # CHIA includes discontinuous entities. Each segment is tagged as a
        # separate contiguous segment and the published exact scorer remains
        # responsible for counting the whole discontinuous item as a miss.
        for start, end in item["spans"]:
            first = next((i for i, (_, s, _) in enumerate(tokens) if s == start), None)
            last = next((i for i, (_, _, e) in enumerate(tokens) if e == end), None)
            if first is None or last is None or first > last:
                continue
            if any(labels[j] != "O" for j in range(first, last + 1)):
                continue
            labels[first] = "B-" + item["kind"]
            for j in range(first + 1, last + 1):
                labels[j] = "I-" + item["kind"]
            aligned += 1
    return labels, aligned


def decode(tokens, labels):
    spans = []
    i = 0
    while i < len(tokens):
        label = labels[i]
        if not label.startswith("B-"):
            i += 1
            continue
        kind = label[2:]
        j = i + 1
        while j < len(tokens) and labels[j] == "I-" + kind:
            j += 1
        spans.append((kind, tokens[i][1], tokens[j - 1][2]))
        i = j
    return spans


def exact_gold(record):
    result = set()
    for item in record["gold"]:
        segs = tuple(tuple(s) for s in item["spans"])
        # Existing benchmark's exact scorer treats discontinuous gold as FN
        # for this contiguous-span task; retain the same convention.
        result.add((item["kind"], segs))
    return result


def metrics(records, predictions):
    counts = {k: Counter() for k in KINDS}
    errors = []
    for record, pred in zip(records, predictions):
        gold = exact_gold(record)
        predicted = {(kind, ((start, end),)) for kind, start, end in pred}
        for kind in KINDS:
            g = {x for x in gold if x[0] == kind}
            p = {x for x in predicted if x[0] == kind}
            counts[kind].update(tp=len(g & p), fp=len(p - g), fn=len(g - p))
        errors.append({
            "record_id": record["record_id"],
            "false_positive": sorted([list(x) for x in predicted - gold]),
            "false_negative": sorted([list(x) for x in gold - predicted]),
        })

    def summarize(c):
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        return {"tp": tp, "fp": fp, "fn": fn, "precision": precision,
                "recall": recall, "f1": 2 * precision * recall / (precision + recall)
                if precision + recall else 0.0}

    total = Counter()
    for c in counts.values():
        total.update(c)
    return {"per_type": {k: summarize(c) for k, c in counts.items()},
            "micro": summarize(total)}, errors


def main():
    records = [r for r in json.loads((ROOT / "data/annotations/chia/benchmark.json").read_text())
               if r["split"] == "development"]
    groups = np.asarray([r["group"] for r in records])
    tokenized = [tokenize(r["text"]) for r in records]
    xs = [features(r["text"], ts) for r, ts in zip(records, tokenized)]
    ys, aligned = [], 0
    for r, ts in zip(records, tokenized):
        tags, n_aligned = tags_for(r, ts)
        ys.append(tags)
        aligned += n_aligned

    # Group by the benchmark's near-duplicate cluster, not by text row.
    # Every prediction is out-of-fold; CHIA test rows never enter fitting or scoring.
    splitter = GroupKFold(n_splits=5)
    predictions = [None] * len(records)
    rule_predictions = [None] * len(records)
    fold_summary = []
    started = time.perf_counter()
    for fold, (train_idx, test_idx) in enumerate(splitter.split(records, groups=groups), 1):
        train_x = [f for i in train_idx for f in xs[i]]
        train_y = [y for i in train_idx for y in ys[i]]
        model = make_pipeline(
            DictVectorizer(),
            LogisticRegression(C=2.0, max_iter=250, class_weight="balanced", solver="lbfgs"),
        )
        model.fit(train_x, train_y)
        fold_predictions = []
        for i in test_idx:
            if not xs[i]:
                predictions[i] = []
                rule_predictions[i] = []
                fold_predictions.append([])
                continue
            predicted_tags = model.predict(xs[i])
            spans = decode(tokenized[i], predicted_tags)
            predictions[i] = spans
            rule_predictions[i] = [
                (item["kind"], item["start"], item["end"])
                for item in regex_rules(records[i]["text"])["items"]
            ]
            fold_predictions.append(spans)
        fold_scores, _ = metrics([records[i] for i in test_idx], fold_predictions)
        fold_summary.append({"fold": fold, "train_records": len(train_idx),
                             "heldout_records": len(test_idx), "heldout_groups": len(set(groups[test_idx])),
                             "micro": fold_scores["micro"]})
        print(f"fold {fold}/5: train_tokens={len(train_y)} heldout_records={len(test_idx)} "
              f"micro_f1={fold_scores['micro']['f1']:.3f}", flush=True)

    scores, errors = metrics(records, predictions)
    rule_scores, rule_errors = metrics(records, rule_predictions)
    combined_predictions = [
        sorted(set(model_spans + rule_spans))
        for model_spans, rule_spans in zip(predictions, rule_predictions)
    ]
    combined_scores, combined_errors = metrics(records, combined_predictions)
    baseline = json.loads((ROOT / "reports/extraction/development.json").read_text())
    summary = {
        "method": "criterion-aware token NER, grouped five-fold out-of-fold evaluation",
        "features": "local token context, token shape, numerical/unit/temporal cues, criterion boundaries",
        "postprocessing": "BIO span decoding with original source character offsets; optional union with existing deterministic regex candidates",
        "training_data": "CHIA development split only; grouped by near-duplicate cluster",
        "test_split_used": False,
        "records": len(records), "trials": len(set(r["nct_id"] for r in records)),
        "groups": len(set(groups)), "gold_segments_token_aligned": aligned,
        "folds": fold_summary, "token_ner": scores,
        "regex_candidates_rerun": rule_scores,
        "hybrid_union": combined_scores,
        "comparison": {"saved_llm_dev_micro": baseline["llm"]["micro"],
                       "saved_rules_dev_micro": baseline["rules"]["micro"]},
        "elapsed_seconds": time.perf_counter() - started,
        "limitations": [
            "small development corpus; exploratory only",
            "character-level exact scoring penalizes token-boundary mismatches",
            "discontinuous CHIA entities remain false negatives under the benchmark convention",
            "no pretrained biomedical encoder; local environment has no SciSpaCy/BioBERT model",
            "not evaluated on the frozen test split and not eligible for release",
        ],
    }
    out_dir = ROOT / "reports/extraction"
    (out_dir / "hybrid_development.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out_dir / "hybrid_development_errors.json").write_text(json.dumps({
        "token_ner": errors, "regex_candidates": rule_errors, "hybrid_union": combined_errors,
    }, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
