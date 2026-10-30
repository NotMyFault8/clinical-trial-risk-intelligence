"""Small, development-only criterion parser inspired by Clinical-Trial-Parser.

Keeps criterion-level source offsets, then applies conservative grammar rules to
explicit numeric/range expressions. It does not change the production extractor
and deliberately loads only CHIA development records.
"""
from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/annotations/chia/benchmark.json"
OUT = ROOT / "reports/extraction"

UNIT = r"(?:mg\s*[/⁄]\s*d[lL]|g\s*[/⁄]\s*d[lL]|mmol\s*[/⁄]\s*l|beats?\s*[/⁄]\s*min|10\^?\d+\s*[/⁄]\s*[lL]|years?|months?|weeks?|days?|hours?|hrs?|min(?:utes?)?|kg|mg|g|mcg|μg|µg|mmhg|cm|mm|%|bpm)"
NUM = r"\d+(?:[.,]\d+)?"
RANGE_RE = re.compile(rf"(?P<low>{NUM})\s*(?:-|–|—|\bto\b)\s*(?P<high>{NUM})\s*(?P<unit>{UNIT})?", re.I)
VALUE_RE = re.compile(rf"(?P<op><=|>=|≤|≥|<|>|\bat\s+least\b|\bno\s+more\s+than\b|\bunder\b|\bover\b|\bless\s+than\b|\bgreater\s+than\b|\bor\s+more\b|\bor\s+greater\b|\bor\s+less\b)?\s*(?P<value>{NUM})\s*(?P<unit>{UNIT})?", re.I)
SPLIT_RE = re.compile(r"\n+|;|^\s*(?:[-•●▪]|\d+[.)])\s*", re.M)
HEADING_RE = re.compile(r"^\s*(inclusion|exclusion)\s+criteria\s*:?\s*$", re.I)
OP_MAP = {
    "<": "<", "<=": "<=", "≤": "<=", ">": ">", ">=": ">=", "≥": ">=",
    "at least": ">=", "no more than": "<=", "under": "<", "over": ">",
    "less than": "<", "greater than": ">", "or more": ">=", "or greater": ">=",
    "or less": "<=",
}
SUFFIX_OP_RE = re.compile(r"^\s*(or\s+more|or\s+greater|or\s+less|or\s+lower|or\s+higher)", re.I)


def split_criteria(text: str):
    """Split on line/list boundaries, retaining exact character offsets."""
    criteria = []
    section = None
    cursor = 0
    for match in SPLIT_RE.finditer(text):
        start, end = cursor, match.start()
        raw = text[start:end]
        left = len(raw) - len(raw.lstrip())
        right = len(raw.rstrip())
        if right > left:
            value = raw[left:right]
            heading = HEADING_RE.match(value)
            if heading:
                section = heading.group(1).lower()
            else:
                criteria.append({"text": value, "start": start + left,
                                 "end": start + right, "section": section})
        cursor = match.end()
    raw = text[cursor:]
    left = len(raw) - len(raw.lstrip())
    right = len(raw.rstrip())
    if right > left:
        value = raw[left:right]
        heading = HEADING_RE.match(value)
        if heading:
            section = heading.group(1).lower()
        else:
            criteria.append({"text": value, "start": cursor + left,
                             "end": cursor + right, "section": section})
    return criteria


def parse_numbers(criterion):
    text = criterion["text"]
    found = []
    occupied = []
    for match in RANGE_RE.finditer(text):
        unit = match.group("unit")
        # Bare numeric ranges are accepted only where the local phrase names a
        # likely quantitative variable (e.g. age 30-55, BMI 30-40).
        context = text[max(0, match.start() - 50):match.start()].lower()
        if not unit and not re.search(r"\b(age|bmi|weight|score|weeks?|months?|years?)\b", context):
            continue
        evidence = match.group(0).strip()
        leading = len(match.group(0)) - len(match.group(0).lstrip())
        found.append({"constraint_type": "numeric_range", "operator": "between", "lower": float(match.group("low").replace(",", ".")),
                      "upper": float(match.group("high").replace(",", ".")),
                      "unit": unit, "evidence": evidence,
                      "start": criterion["start"] + match.start() + leading,
                      "end": criterion["start"] + match.start() + leading + len(evidence)})
        occupied.append(match.span())
    for match in VALUE_RE.finditer(text):
        if any(a <= match.start() < b for a, b in occupied):
            continue
        op = (match.group("op") or "").strip().lower()
        unit = match.group("unit")
        suffix = SUFFIX_OP_RE.match(text[match.end():])
        if not op and suffix:
            op = suffix.group(1).lower()
        # Avoid turning arbitrary counts/dates into eligibility bounds.
        context = text[max(0, match.start() - 50):match.start()].lower()
        if not op and not unit:
            continue
        temporal = bool(re.search(r"\b(within|within\s+(?:the\s+)?(?:last|past)|during|prior\s+to|before|in\s+the\s+past)\s*$", context))
        duration = bool(re.search(r"\b(for|at\s+least)\s*$", context))
        operator = OP_MAP.get(op, ">=" if duration else "within" if temporal else "=")
        raw_evidence = match.group(0)
        evidence = raw_evidence.strip()
        leading = len(raw_evidence) - len(raw_evidence.lstrip())
        found.append({"constraint_type": "temporal_window" if temporal else "numeric_threshold",
                      "operator": operator,
                      "value": float(match.group("value").replace(",", ".")),
                      "unit": unit, "evidence": evidence,
                      "start": criterion["start"] + match.start() + leading,
                      "end": criterion["start"] + match.start() + leading + len(evidence),
                      "variable_context": context[-50:].strip(),
                      "operator_evidence": suffix.group(1) if suffix and op == suffix.group(1).lower() else op or ("for" if duration else "within" if temporal else "explicit unit only")})
    found.sort(key=lambda x: x["start"])
    return found


def main():
    records = [r for r in json.loads(DATA.read_text()) if r["split"] == "development"]
    rows = []
    by_unit, by_operator = Counter(), Counter()
    criterion_count = numeric_criteria = parsed_constraints = offset_matches = 0
    for record in records:
        criteria = split_criteria(record["text"])
        criterion_count += len(criteria)
        parsed = []
        for criterion in criteria:
            constraints = parse_numbers(criterion)
            if constraints:
                numeric_criteria += 1
                parsed_constraints += len(constraints)
                offset_matches += sum(record["text"][c["start"]:c["end"]] == c["evidence"] for c in constraints)
                by_operator.update(c["operator"] for c in constraints)
                by_unit.update((c["unit"] or "(unit omitted)").lower() for c in constraints)
                parsed.append({**criterion, "constraints": constraints})
        rows.append({"record_id": record["record_id"], "document_type":
                     "exclusion" if record["record_id"].endswith("_exc") else "inclusion",
                     "criteria_count": len(criteria), "numeric_criteria": parsed})

    sample_rows = []
    for row in rows:
        for criterion in row["numeric_criteria"]:
            if len(sample_rows) >= 20:
                break
            sample_rows.append({"record_id": row["record_id"], **criterion})
        if len(sample_rows) >= 20:
            break
    result = {
        "method": "criterion segmentation with conservative numeric grammar rules",
        "inspiration": "Clinical-Trial-Parser: preserve inclusion/exclusion criteria boundaries, then parse explicit numerical requirements",
        "split": "CHIA development only; frozen test split not used for fitting or scoring",
        "records": len(records), "criteria": criterion_count,
        "criteria_with_numeric_parse": numeric_criteria,
        "parsed_constraints": parsed_constraints,
        "evidence_offsets_valid": offset_matches,
        "evidence_offset_valid_rate": offset_matches / parsed_constraints if parsed_constraints else 0.0,
        "operator_counts": dict(by_operator), "unit_counts": dict(by_unit),
        "samples": sample_rows,
        "limitations": [
            "heuristic newline/list segmentation; nested conjunctions are not decomposed",
            "variable/value relation and negation scope are not validated",
            "normalized tuples have no CHIA gold labels, so no clinical semantic accuracy is claimed",
            "experimental only; not wired into the production extractor",
        ],
        "records_detail": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "criterion_parser_development.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("records_detail", "samples")}, ensure_ascii=False, indent=2))
    print("\nSAMPLES")
    print(json.dumps(sample_rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
