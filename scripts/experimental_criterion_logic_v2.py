"""Second-round experiment: attach conservative logic to criterion parses.

Builds on experimental_criterion_parser.py's criterion boundaries and numeric
grammar. Adds explicit AND/OR links between parsed bounds and recognizes
"N of M" cardinality phrases without guessing whether the source means exactly
N or at least N. CHIA development split only.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from experimental_criterion_parser import DATA, OUT, parse_numbers, split_criteria  # noqa: E402

CARDINALITY_RE = re.compile(r"\b(?P<prefix>plus|at\s+least|any|all)?\s*(?P<required>\d+)\s+of\s+(?P<total>\d+)\b", re.I)
COMPARATOR_PHRASE_RE = re.compile(r"\bor\s+(?:more|greater|less|lower|higher)\b", re.I)
CONNECTOR_RE = re.compile(r"\b(and|or)\b", re.I)


def connect_constraints(text, constraints, source_offset):
    constraints = sorted(constraints, key=lambda c: c["start"])
    links = []
    for left, right in zip(constraints, constraints[1:]):
        between = text[left["end"] - source_offset:right["start"] - source_offset]
        # “or greater” is the comparison operator attached to the left bound;
        # remove it before looking for the Boolean link to the next bound.
        connector_text = COMPARATOR_PHRASE_RE.sub(" ", between)
        connectors = [m.group(1).lower() for m in CONNECTOR_RE.finditer(connector_text)]
        links.append({"left_start": left["start"], "right_start": right["start"],
                      "operator": connectors[-1] if connectors else "unlinked",
                      "source_between": between.strip()})
    return constraints, links


def main():
    records = [r for r in json.loads(DATA.read_text()) if r["split"] == "development"]
    report_rows = []
    total_criteria = total_numeric = total_constraints = 0
    offset_checks = offset_valid = 0
    cardinality_offset_checks = cardinality_offset_valid = 0
    links_count, cardinality_count = Counter(), Counter()
    for record in records:
        criteria = split_criteria(record["text"])
        total_criteria += len(criteria)
        enriched = []
        for criterion in criteria:
            card_match = CARDINALITY_RE.search(criterion["text"])
            cardinality = None
            if card_match:
                prefix = (card_match.group("prefix") or "").lower().strip()
                card_start = criterion["start"] + card_match.start()
                card_end = criterion["start"] + card_match.end()
                cardinality = {
                    "required_count": int(card_match.group("required")),
                    "total_count": int(card_match.group("total")),
                    "source_phrase": card_match.group(0),
                    "start": card_start,
                    "end": card_end,
                    "count_semantics": "minimum" if prefix == "at least" else "all" if prefix == "all" else "minimum_or_exact_unresolved",
                    "qualifier": prefix or None,
                }
                cardinality_offset_checks += 1
                cardinality_offset_valid += record["text"][card_start:card_end] == card_match.group(0)
                cardinality_count["count_rules"] += 1
                cardinality_count[f"{cardinality['required_count']}_of_{cardinality['total_count']}"] += 1
            constraints = parse_numbers(criterion)
            if cardinality:
                constraints = [c for c in constraints if not
                               (c["start"] < cardinality["end"] and c["end"] > cardinality["start"])]
            constraints, links = connect_constraints(criterion["text"], constraints, criterion["start"])
            if constraints or cardinality:
                total_numeric += bool(constraints)
                total_constraints += len(constraints)
                for link in links:
                    links_count[link["operator"]] += 1
                for constraint in constraints:
                    offset_checks += 1
                    offset_valid += record["text"][constraint["start"]:constraint["end"]] == constraint["evidence"]
                enriched.append({**criterion, "constraints": constraints,
                                 "logic_links": links, "cardinality": cardinality})
        report_rows.append({"record_id": record["record_id"],
                            "document_type": "exclusion" if record["record_id"].endswith("_exc") else "inclusion",
                            "criteria_count": len(criteria), "parsed_criteria": enriched})

    # Surface examples that show the new relationship/cardinality output.
    examples = []
    for row in report_rows:
        for criterion in row["parsed_criteria"]:
            if criterion["cardinality"] or criterion["logic_links"]:
                examples.append({"record_id": row["record_id"], "document_type": row["document_type"],
                                 "criterion": criterion["text"],
                                 "constraints": criterion["constraints"],
                                 "logic_links": criterion["logic_links"],
                                 "cardinality": criterion["cardinality"]})
            if len(examples) >= 20:
                break
        if len(examples) >= 20:
            break

    result = {
        "method": "criterion-level numeric grammar plus conservative Boolean/cardinality linking",
        "inspiration": "Clinical-Trial-Parser's criterion segmentation and grammar-based relation parsing",
        "split": "CHIA development only; frozen test split not used for fitting or scoring",
        "records": len(records), "criteria": total_criteria,
        "criteria_with_numeric_constraints": total_numeric,
        "numeric_constraints": total_constraints,
        "evidence_offsets_valid": offset_valid,
        "evidence_offset_valid_rate": offset_valid / offset_checks if offset_checks else 0.0,
        "cardinality_offsets_valid": cardinality_offset_valid,
        "cardinality_offset_valid_rate": cardinality_offset_valid / cardinality_offset_checks if cardinality_offset_checks else 0.0,
        "boolean_link_counts": dict(links_count), "cardinality_counts": dict(cardinality_count),
        "examples": examples,
        "limitations": [
            "AND/OR links are lexical links only; full nested Boolean scope is not reconstructed",
            "N-of-M phrases are surfaced while exact versus minimum semantics remain unresolved",
            "not validated against gold logical relations; CHIA spans do not label normalized logic",
            "negation and inclusion/exclusion polarity are not composed into a decision rule",
            "experimental only; not wired into production",
        ],
        "records_detail": report_rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "criterion_logic_v2_development.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("records_detail", "examples")},
                     ensure_ascii=False, indent=2))
    print("\nEXAMPLES")
    print(json.dumps(examples[:8], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
