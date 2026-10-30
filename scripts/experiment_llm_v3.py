"""Reproducible local candidate-guided LLM experiment with a new CHIA holdout.

Stages: prepare (texts only), develop (grouped OOF), freeze, evaluate (one time).
All model calls stay on the local Mac. Full raw requests/responses are cached in
ignored artifacts. Published predictions retain source offsets and cache hashes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import time
import zipfile

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

from clinical_trial_risk.llm.candidate_protocol import (
    KINDS, exact_score, source_chunks, summarize_counts, validate_selection, validate_quotes,
)
from clinical_trial_risk.llm.extract import Extractor, rules, visible_text
from experimental_hybrid_ner import decode, features, tags_for, tokenize
from experimental_criterion_parser import parse_numbers, split_criteria

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/extraction/llm_v3"
DATA = ROOT / "data/annotations/chia"
CACHE = ROOT / "artifacts/extraction_v3_cache"
PROMPT = ROOT / "prompts/extract_candidates_v3.txt"
QUOTE_PROMPT = ROOT / "prompts/extract_quotes_v3.txt"
MODELS = {"1.5b": "qwen-4bit", "7b": "qwen7-4bit"}
MAX_CANDIDATES = 48
MAX_TOKENS = 512


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def development_records():
    # The historical benchmark file contains both splits. Only development rows
    # are ever used for fitting, retrieval examples, or OOF model selection.
    return [r for r in json.loads((DATA / "benchmark.json").read_text()) if r["split"] == "development"]


def prepare(fresh_groups):
    if (OUT / "fresh_manifest.json").exists():
        print("Fresh manifest already exists; preserving selection.", flush=True)
        return
    archive = DATA / "chia_with_scope.zip"
    assert digest(archive) == json.loads((ROOT / "configs/chia_source.json").read_text())["sha256"]
    historical = json.loads((DATA / "benchmark.json").read_text())
    used = {r["nct_id"] for r in historical}
    with zipfile.ZipFile(archive) as z:
        # Do not read .ann files in preparation: selection uses source text only.
        texts = {name[:-4]: z.read(name).decode("utf-8") for name in sorted(z.namelist()) if name.endswith(".txt")}
    ids = sorted({name.split("_")[0] for name in texts})
    combined = ["\n".join(text for name, text in texts.items() if name.split("_")[0] == n) for n in ids]
    vectorizer = HashingVectorizer(analyzer="char", ngram_range=(4, 5), n_features=2**18, alternate_sign=False)
    mat = vectorizer.transform(combined)
    similarity = (mat @ mat.T).tocoo()
    parent = list(range(len(ids)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, value in zip(similarity.row, similarity.col, similarity.data):
        if a < b and value >= .9:
            parent[find(int(b))] = find(int(a))
    groups = {n: ids[find(i)] for i, n in enumerate(ids)}
    used_groups = {groups[n] for n in used}
    available = set(groups.values()) - used_groups
    selected = set(sorted(available, key=lambda n: hashlib.sha256(("llm-v3-fresh-2026-10-30:" + n).encode()).hexdigest())[:fresh_groups])
    records = [{"record_id": name, "nct_id": name.split("_")[0], "group": groups[name.split("_")[0]],
                "text": text, "split": "fresh_v3"} for name, text in texts.items() if groups[name.split("_")[0]] in selected]
    assert not ({r["nct_id"] for r in records} & used)
    assert not (selected & used_groups)
    manifest = {"created_at": stamp(), "source_sha256": digest(archive),
                "selection": "50 unused near-duplicate components, ordered by SHA256(llm-v3-fresh-2026-10-30:<group>)",
                "annotations_read_for_selection": False, "similarity_threshold": .9,
                "excluded_historical_trials": len(used), "excluded_historical_groups": len(used_groups),
                "groups": len(selected), "trials": len({r["nct_id"] for r in records}), "records": len(records),
                "members": [{k: r[k] for k in ("record_id", "nct_id", "group")} |
                            {"text_sha256": hashlib.sha256(r["text"].encode()).hexdigest()} for r in records]}
    write_json(DATA / "llm_v3_fresh_text.json", records)
    write_json(OUT / "fresh_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "members"}, indent=2), flush=True)


class CandidateBuilder:
    """Supervised token spans + training lexicon + conservative grammar spans."""

    def __init__(self, train):
        self.train_groups = sorted({r["group"] for r in train})
        xx, yy, lexicon = [], [], defaultdict(set)
        for record in train:
            tokens = tokenize(record["text"])
            xx.extend(features(record["text"], tokens))
            yy.extend(tags_for(record, tokens)[0])
            for entity in record["gold"]:
                if len(entity["spans"]) != 1:
                    continue
                start, end = entity["spans"][0]
                value = record["text"][start:end]
                if 2 <= len(value) <= 120 and re.search(r"[A-Za-z]", value):
                    lexicon[value.lower()].add(entity["kind"])
        self.ner = make_pipeline(DictVectorizer(), LogisticRegression(C=2., max_iter=500, class_weight="balanced", solver="lbfgs"))
        self.ner.fit(xx, yy)
        self.lexicon = [(re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.I), kinds)
                        for term, kinds in sorted(lexicon.items())]
        self.examples = []
        for record in train:
            for start, end in source_chunks(record["text"], max_chars=650, overlap=80):
                gold = [(g["kind"], g["spans"][0][0], g["spans"][0][1]) for g in record["gold"]
                        if len(g["spans"]) == 1 and start <= g["spans"][0][0] < g["spans"][0][1] <= end]
                if not gold or len(gold) > 15:
                    continue
                self.examples.append({"record": record, "start": start, "end": end, "gold": gold})
        self.retrieval = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=30000)
        self.example_vectors = self.retrieval.fit_transform([e["record"]["text"][e["start"]:e["end"]] for e in self.examples])

    def candidates(self, text):
        candidates = {}

        def add(kind, start, end, origin):
            if not 0 <= start < end <= len(text):
                return
            while start < end and text[start].isspace():
                start += 1
            while start < end and text[end - 1].isspace():
                end -= 1
            if start >= end:
                return
            row = candidates.setdefault((start, end), {"start": start, "end": end, "evidence": text[start:end], "hints": set(), "origins": set()})
            row["hints"].add(kind)
            row["origins"].add(origin)

        tokens = tokenize(text)
        ner_items = []
        if tokens:
            for kind, start, end in decode(tokens, self.ner.predict(features(text, tokens))):
                add(kind, start, end, "token_ner")
                ner_items.append({"kind": kind, "start": start, "end": end, "evidence": text[start:end]})
        for pattern, kinds in self.lexicon:
            for match in pattern.finditer(text):
                for kind in kinds:
                    add(kind, match.start(), match.end(), "development_lexicon")
        for item in rules(text)["items"]:
            add(item["kind"], item["start"], item["end"], "legacy_regex")
        for criterion in split_criteria(text):
            for value in parse_numbers(criterion):
                start, end = value["start"], value["end"]
                kind = "Temporal" if value.get("constraint_type") == "temporal_window" else "Value"
                add(kind, start, end, "numeric_grammar")
                suffix = re.match(r"\s+or\s+(?:more|greater|less|lower|higher|older|younger)\b", text[end:], re.I)
                if suffix:
                    add(kind, start, end + suffix.end(), "grammar_complete_boundary")
        # Add complete temporal windows; broad spans remain candidates, not facts.
        temporal = r"\b(?:within|during|for|in|at least|at the time of|at|before|after|prior to)\s+(?:the\s+)?(?:last\s+|past\s+|previous\s+)?(?:\d+(?:\.\d+)?|one|two|three|four|six|twelve)\s+(?:hours?|h|days?|weeks?|months?|years?)(?:\s+(?:prior to|before|after|of|following|preceding)\s+[^,;\n.]{1,65})?"
        for match in re.finditer(temporal, text, re.I):
            add("Temporal", match.start(), match.end(), "temporal_grammar")
        # Adjacent modifiers create explicit alternative boundaries for the LLM.
        for item in list(candidates.values()):
            a, b = item["start"], item["end"]
            if "Measurement" in item["hints"]:
                prefix = re.search(r"\b(?:(?:serum|plasma|fasting|total|systolic|diastolic|blood|body)\s+){1,3}$", text[max(0, a - 45):a], re.I)
                if prefix:
                    add("Measurement", max(0, a - 45) + prefix.start(), b, "measurement_boundary")
                suffix = re.match(r"\s+(?:levels?|count|test|score)\b", text[b:], re.I)
                if suffix:
                    add("Measurement", a, b + suffix.end(), "measurement_boundary")
        rows = [{**r, "hints": sorted(r["hints"]), "origins": sorted(r["origins"])} for _, r in sorted(candidates.items())]
        return rows, {"schema_valid": True, "items": ner_items}

    @staticmethod
    def user_message(text, start, end, candidates):
        return json.dumps({"source": text[start:end], "candidates": [
            {"id": i, "span": [c["start"] - start, c["end"] - start], "text": c["evidence"], "hints": c["hints"]}
            for i, c in enumerate(candidates)]}, ensure_ascii=False)

    def example_messages(self, target, mode="ids"):
        scores = (self.example_vectors @ self.retrieval.transform([target]).T).toarray().ravel()
        messages, used_groups = [], set()
        for index in np.argsort(-scores, kind="stable"):
            example = self.examples[index]
            record, start, end = example["record"], example["start"], example["end"]
            if record["group"] in used_groups:
                continue
            used_groups.add(record["group"])
            candidates = {}
            for item in rules(record["text"][start:end])["items"]:
                a, b = start + item["start"], start + item["end"]
                candidates[(a, b)] = {"start": a, "end": b, "evidence": record["text"][a:b], "hints": [item["kind"]]}
            for kind, a, b in example["gold"]:
                candidates[(a, b)] = {"start": a, "end": b, "evidence": record["text"][a:b], "hints": [kind]}
            rows = [c for _, c in sorted(candidates.items())]
            answer = {k: [] for k in KINDS}
            gold = set(example["gold"])
            for i, c in enumerate(rows):
                for kind in KINDS:
                    if (kind, c["start"], c["end"]) in gold:
                        answer[kind].append(i)
                        break
            content = self.user_message(record["text"], start, end, rows)
            if mode == "quotes":
                content = json.dumps({"SOURCE": record["text"][start:end]}, ensure_ascii=False)
                answer = {k: list(dict.fromkeys(record["text"][a:b] for kind, a, b in example["gold"] if kind == k)) for k in KINDS}
            messages.extend([{"role": "user", "content": content},
                             {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)}])
            if len(used_groups) == 2:
                break
        return messages

    def requests(self, record, mode="ids"):
        rows, ner_output = self.candidates(record["text"])
        requests = []
        for start, end in source_chunks(record["text"]):
            contained = [c for c in rows if start <= c["start"] and c["end"] <= end]
            if not contained and mode == "ids":
                continue
            examples = self.example_messages(record["text"][start:end], mode)
            offsets = [0] if mode == "quotes" else range(0, len(contained), MAX_CANDIDATES)
            for offset in offsets:
                candidates = contained[offset:offset + MAX_CANDIDATES]
                content = self.user_message(record["text"], start, end, candidates)
                prompt = PROMPT
                if mode == "quotes":
                    prompt = QUOTE_PROMPT
                    content = json.dumps({"SOURCE": record["text"][start:end], "fallible_hints":
                                          [{"text": c["evidence"], "types": c["hints"]} for c in candidates]}, ensure_ascii=False)
                messages = [{"role": "system", "content": prompt.read_text()}] + examples + [{"role": "user", "content": content}]
                requests.append({"record_id": record["record_id"], "text": record["text"],
                                 "start": start, "end": end, "candidates": candidates, "messages": messages})
        # Baseline for candidate recall: all hinted types at each boundary.
        pool = {"schema_valid": True, "items": [{"kind": kind, **{k: c[k] for k in ("start", "end", "evidence")}}
                                                for c in rows for kind in c["hints"]]}
        return requests, ner_output, pool


class LocalModel:
    def __init__(self, name, mode="ids"):
        from mlx_lm import load
        self.name = name
        self.mode = mode
        path = ROOT / "artifacts/pretrained" / MODELS[name]
        self.provenance = {"name": name, "path": str(path.relative_to(ROOT)),
                           "weights": {p.name: digest(p) for p in path.glob("*.safetensors")},
                           "generation": "greedy; max_tokens=512; no repair or fallback"}
        self.model, self.tokenizer = load(str(path))
        CACHE.mkdir(parents=True, exist_ok=True)

    def run(self, requests):
        from mlx_lm import batch_generate
        from mlx_lm.sample_utils import make_sampler
        pending, results = [], [None] * len(requests)
        def validate(raw, request):
            if self.mode == "quotes":
                return validate_quotes(raw, request["text"], request["start"], request["end"])
            return validate_selection(raw, request["candidates"], request["text"])
        for i, request in enumerate(requests):
            key = hashlib.sha256(json.dumps({"messages": request["messages"], "model": self.provenance}, sort_keys=True).encode()).hexdigest()
            path = CACHE / (key + ".json")
            if path.exists():
                cached = json.loads(path.read_text())
                results[i] = {**cached, **validate(cached["raw"], request), "cache_key": key}
            else:
                tokens = self.tokenizer.apply_chat_template(request["messages"], tokenize=True, add_generation_prompt=True)
                pending.append((i, path, tokens, key))
        print(f"Model {self.name}: requests={len(requests)} pending={len(pending)}", flush=True)
        for batch_start in range(0, len(pending), 8):
            batch = pending[batch_start:batch_start + 8]
            started = time.perf_counter()
            generation = batch_generate(self.model, self.tokenizer, [e[2] for e in batch],
                max_tokens=MAX_TOKENS, sampler=make_sampler(temp=0),
                completion_batch_size=8, prefill_batch_size=2, verbose=False)
            seconds = time.perf_counter() - started
            for (i, path, tokens, key), raw in zip(batch, generation.texts, strict=True):
                cached = {"raw": raw, "input_tokens": len(tokens), "output_tokens": len(self.tokenizer.encode(raw)),
                          "amortized_seconds": seconds / len(batch), "created_at": stamp(), "model": self.provenance,
                          "messages": requests[i]["messages"]}
                write_json(path, cached)
                results[i] = {**cached, **validate(raw, requests[i]), "cache_key": key}
            print(f"{self.name}: {min(batch_start + 8, len(pending))}/{len(pending)} requests, batch={seconds:.1f}s", flush=True)
        return results


def predict(records, builder, model):
    requests, ner_outputs, pools = [], [], []
    for record in records:
        current, ner, pool = builder.requests(record, model.mode)
        requests.extend(current)
        ner_outputs.append(ner)
        pools.append(pool)
    results = model.run(requests)
    by_record = defaultdict(list)
    for request, result in zip(requests, results, strict=True):
        by_record[request["record_id"]].append(result)
    outputs = []
    for record in records:
        chunks = by_record[record["record_id"]]
        items = {(i["kind"], i["start"], i["end"]): i for c in chunks for i in c["items"]}
        outputs.append({"record_id": record["record_id"], "schema_valid": all(c["schema_valid"] for c in chunks),
                        "items": [i for _, i in sorted(items.items())], "request_count": len(chunks),
                        "failed_requests": sum(not c["schema_valid"] for c in chunks),
                        "cache_keys": [c["cache_key"] for c in chunks]})
    operating = {"requests": len(results), "valid_requests": sum(r["schema_valid"] for r in results),
                 "raw_request_schema_valid_rate": sum(r["schema_valid"] for r in results) / len(results) if results else None,
                 "no_candidate_documents": sum(o["request_count"] == 0 for o in outputs),
                 "input_tokens": sum(r["input_tokens"] for r in results), "output_tokens": sum(r["output_tokens"] for r in results),
                 "cached_or_original_amortized_seconds": sum(r["amortized_seconds"] for r in results),
                 "invalid_reasons": dict(Counter(r["error"] for r in results if not r["schema_valid"])),
                 "rejected_quote_count": sum(len(r.get("rejected_quotes", [])) for r in results),
                 "repeated_local_quote_count": sum(r.get("repeated_quotes", 0) for r in results),
                 "hosted_api_calls": 0}
    return outputs, ner_outputs, pools, operating


def score_all(records, outputs):
    return {scope: exact_score(records, outputs, prefix=scope == "matched_prefix")[0]
            for scope in ("matched_prefix", "full_text")}


def combine_outputs(llm, ner, policy):
    if policy == "llm_only":
        return llm
    if policy != "union":
        raise ValueError(policy)
    combined = []
    for a, b in zip(llm, ner, strict=True):
        items = {(i["kind"], i["start"], i["end"]): i for i in a["items"] + b["items"]}
        # Preserve LLM format failures; adding NER spans cannot make them pass.
        combined.append({**a, "items": [i for _, i in sorted(items.items())], "fusion": "union"})
    return combined


def ablate():
    records = development_records()
    ner = [None] * len(records)
    for train_idx, held_idx in GroupKFold(5).split(records, groups=[r["group"] for r in records]):
        builder = CandidateBuilder([records[i] for i in train_idx])
        for i in held_idx:
            ner[i] = builder.candidates(visible_text(records[i]["text"]))[1]
    variants = {}
    for tag in list(MODELS) + [n + "_quotes" for n in MODELS]:
        path = OUT / f"development_{tag}_predictions.json"
        if not path.exists():
            continue
        llm = json.loads(path.read_text())
        variants[tag] = {policy: exact_score(records, combine_outputs(llm, ner, policy), prefix=True)[0]
                         for policy in ("llm_only", "union")}
    write_json(OUT / "fusion_development.json", {"created_at": stamp(), "selection_data": "development grouped OOF only",
               "ner": exact_score(records, ner, prefix=True)[0], "variants": variants,
               "note": "Union never converts invalid LLM documents to schema-valid documents"})
    for tag, choices in variants.items():
        for policy, score in choices.items():
            print(tag, policy, score["micro"], flush=True)


def develop(name, mode="ids"):
    records = development_records()
    groups = np.asarray([r["group"] for r in records])
    outputs, ner_outputs, pools = ([None] * len(records) for _ in range(3))
    model = LocalModel(name, mode)
    folds = []
    for fold, (train_idx, held_idx) in enumerate(GroupKFold(5).split(records, groups=groups), 1):
        train, held = [records[i] for i in train_idx], [records[i] for i in held_idx]
        assert not ({r["group"] for r in train} & {r["group"] for r in held})
        builder = CandidateBuilder(train)
        # Primary development comparison uses exactly the original input prefix.
        bounded = [{**r, "text": visible_text(r["text"])} for r in held]
        predicted, ner, pool, operating = predict(bounded, builder, model)
        for j, index in enumerate(held_idx):
            outputs[index], ner_outputs[index], pools[index] = predicted[j], ner[j], pool[j]
        summary = score_all(held, predicted)
        folds.append({"fold": fold, "train_groups": builder.train_groups,
                      "heldout_groups": sorted({r["group"] for r in held}), "scores": summary, "operating": operating})
        print(f"DEVELOP {name} fold={fold} {summary['matched_prefix']['micro']}", flush=True)
    result = {"created_at": stamp(), "model": model.provenance, "mode": mode, "stage": "grouped_five_fold_development",
              "prompt_sha256": digest(QUOTE_PROMPT if mode == "quotes" else PROMPT),
              "llm": score_all(records, outputs), "token_ner": score_all(records, ner_outputs),
              "candidate_pool": score_all(records, pools), "folds": folds,
              "historical_llm": json.loads((ROOT / "reports/extraction/development.json").read_text())["llm"],
              "annotation_use": "Each fold's candidate lexicon, NER and retrieval examples use training groups only",
              "inference_input": "original visible_text prefix; full_text score here counts the resulting outside-prefix omissions",
              "human_review_completed": False}
    tag = name if mode == "ids" else name + "_quotes"
    write_json(OUT / f"development_{tag}.json", result)
    write_json(OUT / f"development_{tag}_predictions.json", outputs)
    print(json.dumps({k: v for k, v in result.items() if k not in ("folds", "historical_llm")}, indent=2), flush=True)


def code_hashes():
    paths = [Path(__file__), PROMPT, QUOTE_PROMPT,
             ROOT / "src/clinical_trial_risk/llm/candidate_protocol.py",
             ROOT / "src/clinical_trial_risk/llm/extract.py", ROOT / "prompts/extract_v1.txt",
             ROOT / "configs/pretrained.json", ROOT / "configs/chia_source.json",
             ROOT / "scripts/experimental_hybrid_ner.py", ROOT / "scripts/experimental_criterion_parser.py"]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def freeze():
    if (OUT / "freeze.json").exists():
        raise RuntimeError("Freeze already exists; preserve the original experimental protocol")
    tags = list(MODELS) + [name + "_quotes" for name in MODELS]
    results = {name: json.loads((OUT / f"development_{name}.json").read_text()) for name in tags
               if (OUT / f"development_{name}.json").exists()}
    if not results:
        raise RuntimeError("Run grouped development first")
    fusion = json.loads((OUT / "fusion_development.json").read_text())
    selected, policy = max(((tag, policy) for tag in results for policy in ("llm_only", "union")),
                          key=lambda pair: fusion["variants"][pair[0]][pair[1]]["micro"]["f1"])
    selected_prompt = QUOTE_PROMPT if results[selected].get("mode") == "quotes" else PROMPT
    assert results[selected].get("prompt_sha256", digest(selected_prompt)) == digest(selected_prompt)
    protocol = {"frozen_at": stamp(), "selected_model": results[selected]["model"]["name"],
                "selected_mode": results[selected].get("mode", "ids"), "selected_development_tag": selected,
                "selected_fusion": policy, "fusion_development_sha256": digest(OUT / "fusion_development.json"),
                "selected_model_provenance": results[selected]["model"],
                "selection": "highest grouped-OOF development exact micro F1 over completed model/format variants and llm_only/union fusion, in matched legacy prefix",
                "development_results_sha256": {name: digest(OUT / f"development_{name}.json") for name in results},
                "fresh_manifest_sha256": digest(OUT / "fresh_manifest.json"), "code_sha256": code_hashes(),
                "development_benchmark_sha256": digest(DATA / "benchmark.json"),
                "release_thresholds": json.loads((ROOT / "configs/extraction_release.json").read_text()),
                "publish_improvement_rule": "On the new holdout, all of document schema rate, micro precision, exact micro F1 exceed the original LLM in the same legacy prefix scope",
                "secondary_scope": "full source; include all discontinuous and nested gold entities",
                "primary_inputs": "Both systems receive exactly visible_text(source), maximum 1800 characters",
                "fresh_gold_used_during_development": False,
                "human_review_policy": "Prepare a human score sheet; AI review cannot mark human review complete",
                "pretraining_contamination": "Public CHIA/source text may be present in pretrained weights; cannot exclude"}
    write_json(OUT / "freeze.json", protocol)
    print(json.dumps(protocol, indent=2), flush=True)


def fresh_gold(text_records):
    records = []
    with zipfile.ZipFile(DATA / "chia_with_scope.zip") as z:
        for record in text_records:
            gold, discrepancies = [], []
            for line in z.read(record["record_id"] + ".ann").decode().splitlines():
                if not line.startswith("T"):
                    continue
                fields = line.split("\t")
                kind, positions = fields[1].split(" ", 1)
                if kind in KINDS:
                    spans = [list(map(int, part.split())) for part in positions.split(";")]
                    gold.append({"kind": kind, "spans": spans})
                    actual = " ".join(record["text"][a:b] for a, b in spans)
                    if len(fields) > 2 and actual != fields[2]:
                        discrepancies.append({"entity_id": fields[0], "kind": kind, "spans": spans})
            records.append({**record, "gold": gold, "annotation_offset_discrepancies": discrepancies})
    return records


def bootstrap(records, baseline, candidate):
    errors = [exact_score(records, outputs, prefix=True)[1] for outputs in (baseline, candidate)]
    groups = sorted({r["group"] for r in records})
    aggregate = []
    for rows in errors:
        values = defaultdict(Counter)
        for row in rows:
            values[row["group"]].update({k: row[k] for k in ("tp", "fp", "fn")})
        aggregate.append(np.asarray([[values[g][k] for k in ("tp", "fp", "fn")] for g in groups]))
    rng = np.random.default_rng(31030)
    deltas = []
    for _ in range(2000):
        chosen = rng.integers(0, len(groups), size=len(groups))
        pair = [summarize_counts(dict(zip(("tp", "fp", "fn"), matrix[chosen].sum(axis=0).tolist()))) for matrix in aggregate]
        deltas.append([pair[1][metric] - pair[0][metric] for metric in ("precision", "f1")])
    return {metric: {"delta_95_percentile_interval": np.quantile(np.asarray(deltas)[:, i], [.025, .975]).tolist()}
            for i, metric in enumerate(("precision", "f1"))} | {"resamples": 2000, "unit": "near_duplicate_trial_group", "seed": 31030}


def human_packet(records, baseline, candidate):
    # Predeclared sampling rule: first 12 trials by hash, one document per trial.
    by_trial = defaultdict(list)
    for i, record in enumerate(records):
        by_trial[record["nct_id"]].append(i)
    chosen = sorted(by_trial, key=lambda n: hashlib.sha256(("human-v3:" + n).encode()).hexdigest())[:12]
    cases, key = [], []
    for case_number, nct in enumerate(chosen, 1):
        indices = sorted(by_trial[nct], key=lambda i: hashlib.sha256(records[i]["record_id"].encode()).hexdigest())
        index = indices[0]
        record = records[index]
        swap = int(hashlib.sha256(nct.encode()).hexdigest(), 16) % 2
        systems = [baseline[index], candidate[index]]
        cases.append({"case_id": f"review-{case_number:02}", "record_id": record["record_id"], "source": visible_text(record["text"]),
                      "review_scope": "matched original input prefix", "original_source_characters": len(record["text"]),
                      "A": systems[swap]["items"], "B": systems[1 - swap]["items"],
                      "reviewer_name": None, "domain_expertise": None, "reviewed_at": None,
                      "A_type_correct": None, "A_boundary_correct": None, "B_type_correct": None, "B_boundary_correct": None,
                      "missing_entities": None, "negation_context_preserved": None, "notes": None, "preferred": None})
        key.append({"case_id": cases[-1]["case_id"], "A": "llm_v3" if swap else "original_llm", "B": "original_llm" if swap else "llm_v3"})
    write_json(OUT / "human_review_packet.json", {"status": "pending_real_human_review", "completed_cases": 0,
               "sampling": "12 trials by SHA256(human-v3:<trial>); one document per trial by record-ID hash",
               "scope": "CHIA external benchmark; does not satisfy target-cohort clinical review",
               "instruction": "A real reviewer must fill scores. Do not substitute AI review for human adjudication. Avoid the key until scores are frozen.", "cases": cases})
    write_json(OUT / "human_review_key.json", key)


def evaluate():
    report_path = OUT / "fresh_evaluation.json"
    if report_path.exists():
        raise RuntimeError("Fresh evaluation already exists; no test-driven rerun")
    protocol = json.loads((OUT / "freeze.json").read_text())
    assert protocol["code_sha256"] == code_hashes(), "Code changed after freeze"
    assert protocol["fresh_manifest_sha256"] == digest(OUT / "fresh_manifest.json")
    assert protocol["development_benchmark_sha256"] == digest(DATA / "benchmark.json")
    manifest = json.loads((OUT / "fresh_manifest.json").read_text())
    assert manifest["source_sha256"] == digest(DATA / "chia_with_scope.zip")
    records = json.loads((DATA / "llm_v3_fresh_text.json").read_text())
    expected = {m["record_id"]: m for m in manifest["members"]}
    assert len(expected) == len(records)
    for record in records:
        assert hashlib.sha256(record["text"].encode()).hexdigest() == expected[record["record_id"]]["text_sha256"]
        assert record["group"] == expected[record["record_id"]]["group"]
    train = development_records()
    assert not ({r["nct_id"] for r in train} & {r["nct_id"] for r in records})
    builder = CandidateBuilder(train)
    model = LocalModel(protocol["selected_model"], protocol["selected_mode"])
    assert model.provenance == protocol["selected_model_provenance"], "Weights/configuration changed after model selection"
    bounded = [{**r, "text": visible_text(r["text"])} for r in records]
    llm_only, ner, pools, operating = predict(bounded, builder, model)
    full_llm_only, full_ner, full_pools, full_operating = predict(records, builder, model)
    predicted = combine_outputs(llm_only, ner, protocol["selected_fusion"])
    full_predicted = combine_outputs(full_llm_only, full_ner, protocol["selected_fusion"])
    del model
    import gc
    import mlx.core as mx
    gc.collect()
    mx.clear_cache()
    baseline = Extractor().run([r["text"] for r in records])
    compact_baseline = [{k: o[k] for k in ("schema_valid", "items", "run_id", "input_tokens", "output_tokens", "amortized_seconds")} for o in baseline]
    # Persist model outputs before any fresh annotations are read.
    predictions_path = OUT / "fresh_predictions.json"
    write_json(predictions_path, {"saved_before_gold_read_at": stamp(), "llm_v3": predicted,
                                 "llm_v3_full_text": full_predicted,
                                 "llm_only": llm_only, "llm_only_full_text": full_llm_only,
                                 "original_llm": compact_baseline, "token_ner": ner, "candidate_pool": pools,
                                 "token_ner_full_text": full_ner, "candidate_pool_full_text": full_pools})
    records = fresh_gold(records)
    rule_outputs = [rules(r["text"]) for r in records]
    scores = {name: score_all(records, outputs) for name, outputs in
              (("llm_v3", predicted), ("llm_only", llm_only), ("original_llm", baseline), ("token_ner", ner), ("rules", rule_outputs), ("candidate_pool", pools))}
    scores["rules"]["matched_prefix"] = exact_score(records, [rules(visible_text(r["text"])) for r in records], prefix=True)[0]
    for name, outputs in (("llm_v3", full_predicted), ("llm_only", full_llm_only), ("token_ner", full_ner), ("candidate_pool", full_pools)):
        scores[name]["full_text"] = exact_score(records, outputs)[0]
    primary = scores["llm_v3"]["matched_prefix"]
    old = scores["original_llm"]["matched_prefix"]
    gate = protocol["release_thresholds"]
    checks = {"schema": primary["document_schema_valid_rate"] >= gate["test_min_schema_valid_rate"],
              "precision": primary["micro"]["precision"] >= gate["test_min_micro_precision"],
              "f1": primary["micro"]["f1"] >= gate["test_min_micro_f1"], "target_cohort_human_review": False}
    improvement = {"schema": primary["document_schema_valid_rate"] > old["document_schema_valid_rate"],
                   "precision": primary["micro"]["precision"] > old["micro"]["precision"],
                   "f1": primary["micro"]["f1"] > old["micro"]["f1"]}
    result = {"evaluated_at": stamp(), "freeze_sha256": digest(OUT / "freeze.json"),
              "predictions_sha256": digest(predictions_path), "model": protocol["selected_model"], "mode": protocol["selected_mode"], "fusion": protocol["selected_fusion"],
              "scores": scores, "operating": {"matched_prefix": operating, "full_text": full_operating}, "improvement_checks": improvement,
              "improved_on_all_three": all(improvement.values()), "release_checks": checks,
              "semantic_release_passed": all(checks.values()), "human_review_completed": False,
              "paired_bootstrap": bootstrap(records, baseline, predicted),
              "gold_offset_discrepancies": [{"record_id": r["record_id"], "entities": r["annotation_offset_discrepancies"]}
                                            for r in records if r["annotation_offset_discrepancies"]],
              "environment": {name: importlib.metadata.version(name) for name in ("mlx", "mlx-lm", "transformers", "numpy", "scikit-learn")},
              "limitations": ["single newly held-out public CHIA sample, not a prospective or target-cohort clinical validation",
                              "pretraining contamination cannot be excluded", "contiguous candidates cannot represent discontinuous entities",
                              "candidate hints may bias the LLM; quote mode can propose additional spans", "human review prepared but not performed",
                              "schema pass and source fidelity are not clinical semantic accuracy"]}
    write_json(report_path, result)
    write_json(OUT / "fresh_errors.json", {"llm_v3": exact_score(records, predicted, prefix=True)[1],
                                           "original_llm": exact_score(records, baseline, prefix=True)[1]})
    human_packet(records, baseline, predicted)
    print(json.dumps(result, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "develop", "ablate", "freeze", "evaluate"))
    parser.add_argument("--model", choices=MODELS, default="1.5b")
    parser.add_argument("--mode", choices=("ids", "quotes"), default="ids")
    parser.add_argument("--fresh-groups", type=int, default=50)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.phase == "prepare":
        prepare(args.fresh_groups)
    elif args.phase == "develop":
        develop(args.model, args.mode)
    elif args.phase == "freeze":
        freeze()
    elif args.phase == "ablate":
        ablate()
    else:
        evaluate()


if __name__ == "__main__":
    main()
