"""Source-grounded candidate selection and exact scoring for research runs.

No model output is repaired into a passing schema. Failed requests retain their
failure status; repeated evidence is located by candidate ID, never str.find.
"""
from collections import Counter
import json
import re

KINDS = ("Measurement", "Value", "Temporal")


def source_chunks(text, max_chars=900, overlap=120):
    """Cover the full source with overlap, preferring criterion boundaries."""
    if max_chars <= overlap or overlap < 0:
        raise ValueError("Require 0 <= overlap < max_chars")
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundaries = [m.end() for m in re.finditer(r"[\n;]", text[start:end])]
            useful = [b for b in boundaries if b >= max_chars // 2]
            if useful:
                end = start + useful[-1]
            else:
                space = text.rfind(" ", start + max_chars // 2, end)
                if space > start:
                    end = space
        chunks.append((start, end))
        if end == len(text):
            break
        next_start = max(start + 1, end - overlap)
        # Avoid breaking a word at the beginning of the overlap.
        while next_start < end and next_start > 0 and not text[next_start - 1].isspace():
            next_start += 1
        start = next_start
    return chunks


def unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate_key")
        obj[key] = value
    return obj


def validate_selection(raw, candidates, text):
    """Strict JSON + candidate-ID validation, with original source offsets."""
    try:
        obj = json.loads(raw.strip(), object_pairs_hook=unique_keys)
        if not isinstance(obj, dict) or set(obj) != set(KINDS):
            raise ValueError("wrong_keys")
        seen, items = set(), []
        for kind in KINDS:
            if not isinstance(obj[kind], list):
                raise ValueError("not_array")
            for index in obj[kind]:
                if type(index) is not int or not 0 <= index < len(candidates):
                    raise ValueError("invalid_candidate_id")
                if index in seen:
                    raise ValueError("duplicate_candidate_id")
                seen.add(index)
                candidate = candidates[index]
                start, end = candidate["start"], candidate["end"]
                if not 0 <= start < end <= len(text) or text[start:end] != candidate["evidence"]:
                    raise ValueError("candidate_source_mismatch")
                items.append({"kind": kind, "start": start, "end": end,
                              "evidence": candidate["evidence"]})
        return {"schema_valid": True, "items": items, "error": None}
    except (ValueError, TypeError, KeyError) as error:
        return {"schema_valid": False, "items": [], "error": str(error)}


def summarize_counts(counts):
    tp, fp, fn = (counts.get(k, 0) for k in ("tp", "fp", "fn"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision,
            "recall": recall, "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}


def validate_quotes(raw, text, start, end):
    """Original string-list schema, local grounding and explicit repeated mapping.

The output may propose spans beyond the hints. Every exact local occurrence of
an accepted quote is emitted. This is an explicit recall/precision tradeoff, not
proof each repeated occurrence has the same clinical type.
"""
    response = raw.strip()
    if response.startswith('```'):
        response = re.sub(r'^```(?:json)?\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
    try:
        obj = json.loads(response, object_pairs_hook=unique_keys)
        if not isinstance(obj, dict) or set(obj) != set(KINDS):
            raise ValueError("wrong_keys")
        if any(not isinstance(obj[k], list) or any(type(s) is not str for s in obj[k]) for k in KINDS):
            raise ValueError("expected_string_arrays")
    except (ValueError, TypeError) as error:
        return {"schema_valid": False, "items": [], "error": str(error), "rejected_quotes": [], "repeated_quotes": 0}
    items, rejected, repeated = {}, [], 0
    source = text[start:end]
    for kind in KINDS:
        for quote in obj[kind]:
            matches = list(re.finditer(re.escape(quote), source)) if quote.strip() else []
            if not matches:
                rejected.append({"kind": kind, "evidence": quote})
            repeated += len(matches) > 1
            for match in matches:
                a, b = start + match.start(), start + match.end()
                items[(kind, a, b)] = {"kind": kind, "start": a, "end": b, "evidence": text[a:b]}
    return {"schema_valid": True, "items": list(items.values()), "error": None,
            "rejected_quotes": rejected, "repeated_quotes": repeated}


def exact_score(records, outputs, prefix=False):
    """Same type/complete-offset rule for every system; no partial-match credit."""
    from .extract import visible_text
    counts = {kind: Counter() for kind in KINDS}
    errors, outside, exact_documents = [], 0, 0
    for record, output in zip(records, outputs, strict=True):
        limit = len(visible_text(record["text"])) if prefix else len(record["text"])
        gold = {(g["kind"], tuple(tuple(s) for s in g["spans"])) for g in record["gold"]
                if max(s[1] for s in g["spans"]) <= limit}
        outside += sum(max(s[1] for s in g["spans"]) > limit for g in record["gold"])
        predicted = {(p["kind"], ((p["start"], p["end"]),)) for p in output["items"] if p["end"] <= limit}
        exact_documents += predicted == gold
        for kind in KINDS:
            g, p = {x for x in gold if x[0] == kind}, {x for x in predicted if x[0] == kind}
            counts[kind].update(tp=len(p & g), fp=len(p - g), fn=len(g - p))
        errors.append({"record_id": record["record_id"], "group": record["group"],
                       "tp": len(predicted & gold), "fp": len(predicted - gold), "fn": len(gold - predicted),
                       "false_positive": sorted(predicted - gold), "false_negative": sorted(gold - predicted)})
    total = sum(counts.values(), Counter())
    return {"scope": "legacy_1800_character_prefix" if prefix else "full_text",
            "records": len(records), "trials": len({r["nct_id"] for r in records}),
            "groups": len({r["group"] for r in records}), "micro": summarize_counts(total),
            "per_type": {k: summarize_counts(v) for k, v in counts.items()},
            "document_schema_valid_rate": sum(o["schema_valid"] for o in outputs) / len(outputs),
            "exact_document_match_rate": exact_documents / len(outputs),
            "exact_documents": exact_documents,
            "documents_with_predictions": sum(bool(o["items"]) for o in outputs),
            "gold_spans_outside_scope": outside}, errors
