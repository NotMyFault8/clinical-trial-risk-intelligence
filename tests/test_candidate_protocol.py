import json

from clinical_trial_risk.llm.candidate_protocol import exact_score, source_chunks, validate_selection, validate_quotes


def test_repeated_evidence_is_resolved_by_candidate_id():
    text = "normal glucose; normal creatinine"
    candidates = [{"start": 0, "end": 6, "evidence": "normal"},
                  {"start": 16, "end": 22, "evidence": "normal"}]
    result = validate_selection('{"Measurement":[],"Value":[1],"Temporal":[]}', candidates, text)
    assert result["schema_valid"]
    assert result["items"] == [{"kind": "Value", "start": 16, "end": 22, "evidence": "normal"}]


def test_candidate_protocol_fails_closed_on_unknown_duplicate_and_boolean_ids():
    candidates = [{"start": 0, "end": 3, "evidence": "BMI"}]
    for raw in ('{"Measurement":[2],"Value":[],"Temporal":[]}',
                '{"Measurement":[true],"Value":[],"Temporal":[]}',
                '{"Measurement":[0],"Value":[0],"Temporal":[]}',
                '{"Measurement":[],"Value":[],"Temporal":[],"Value":[0]}',
                '```json\n{"Measurement":[0],"Value":[],"Temporal":[]}\n```'):
        result = validate_selection(raw, candidates, "BMI")
        assert not result["schema_valid"] and not result["items"]


def test_full_source_chunking_preserves_coverage_and_decimal_at_line_start():
    text = "Inclusion Criteria:\n1.5 mg/dL or more; repeated words " * 80
    chunks = source_chunks(text, 150, 30)
    assert chunks[-1][1] == len(text)
    covered = set()
    for start, end in chunks:
        assert end - start <= 150
        covered.update(range(start, end))
    assert covered == set(range(len(text)))
    assert text[0:chunks[0][1]].startswith("Inclusion Criteria:\n1.5")


def test_exact_score_keeps_discontinuous_gold_and_filters_both_prefix_sides():
    text = "BMI 30; " + "x " * 1000 + "late"
    record = {"record_id": "r", "nct_id": "n", "group": "g", "text": text,
              "gold": [{"kind": "Measurement", "spans": [[0, 3]]},
                       {"kind": "Value", "spans": [[0, 3], [4, 6]]},
                       {"kind": "Temporal", "spans": [[len(text) - 4, len(text)]]}]}
    out = {"schema_valid": True, "items": [{"kind": "Measurement", "start": 0, "end": 3},
            {"kind": "Temporal", "start": len(text) - 4, "end": len(text)}]}
    prefix, _ = exact_score([record], [out], prefix=True)
    full, _ = exact_score([record], [out])
    assert (prefix["micro"]["tp"], prefix["micro"]["fp"], prefix["micro"]["fn"]) == (1, 0, 1)
    assert (full["micro"]["tp"], full["micro"]["fp"], full["micro"]["fn"]) == (2, 0, 1)


def test_candidate_source_mismatch_is_rejected():
    result = validate_selection(json.dumps({"Measurement": [0], "Value": [], "Temporal": []}),
                                [{"start": 0, "end": 3, "evidence": "age"}], "BMI")
    assert not result["schema_valid"] and result["error"] == "candidate_source_mismatch"


def test_quote_schema_is_separate_from_grounding_and_maps_only_local_occurrences():
    text = "normal; normal; normal"
    raw = json.dumps({"Measurement": ["invented"], "Value": ["normal"], "Temporal": []})
    result = validate_quotes(raw, text, 8, len(text))
    assert result["schema_valid"]
    assert [(i["start"], i["end"]) for i in result["items"]] == [(8, 14), (16, 22)]
    assert result["rejected_quotes"] == [{"kind": "Measurement", "evidence": "invented"}]
    assert result["repeated_quotes"] == 1


def test_quote_protocol_preserves_case_and_duplicate_key_validation():
    raw = '{"Measurement":[],"Value":[],"Temporal":[],"Value":["normal"]}'
    assert not validate_quotes(raw, "normal", 0, 6)["schema_valid"]
    result = validate_quotes('{"Measurement":[],"Value":["Normal"],"Temporal":[]}', "normal", 0, 6)
    assert result["schema_valid"] and not result["items"] and result["rejected_quotes"]
