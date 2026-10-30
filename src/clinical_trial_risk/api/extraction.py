"""Read-only access to the saved V3 benchmark and AI secondary review."""
import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from clinical_trial_risk.data.cohort import ROOT

router = APIRouter(prefix="/extraction", tags=["Extraction research"])
RESULTS_DIR = ROOT / "reports/extraction/llm_v3"
EXPERIMENT_ID = "llm-v3-2026-10-30"
SOURCE = {
    "name": "CHIA v2",
    "doi": "https://doi.org/10.6084/m9.figshare.11855817.v2",
    "license": "CC BY 4.0",
}
SYSTEMS = {
    "original_llm": "Original Qwen 1.5B",
    "llm_v3": "Revised LLM + NER",
    "llm_only": "Revised LLM alone",
    "token_ner": "Token NER alone",
    "rules": "Regex rules",
}


class Metrics(BaseModel):
    tp: int = Field(ge=0)
    fp: int = Field(ge=0)
    fn: int = Field(ge=0)
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    f1: float = Field(ge=0, le=1)


class ExtractionScore(BaseModel):
    scope: str
    records: int = Field(gt=0)
    trials: int = Field(gt=0)
    groups: int = Field(gt=0)
    micro: Metrics
    per_type: dict[str, Metrics]
    document_schema_valid_rate: float = Field(ge=0, le=1)
    exact_document_match_rate: float = Field(ge=0, le=1)
    exact_documents: int = Field(ge=0)
    gold_spans_outside_scope: int = Field(ge=0)


class SystemResult(BaseModel):
    id: str
    label: str
    matched_prefix: ExtractionScore
    full_text: ExtractionScore


class EvaluationResponse(BaseModel):
    experiment_id: str
    evaluated_at: str
    mode: Literal["saved_research_results"]
    dataset: dict
    selected_pipeline: dict
    systems: list[SystemResult]
    paired_bootstrap: dict
    publication_improvement_checks_passed: bool
    release: dict
    limitations: list[str]
    links: dict[str, str]


class ReviewAggregate(Metrics):
    exact_documents: int = Field(ge=0)


class ReviewCaseSummary(BaseModel):
    case_id: str
    record_id: str
    findings: dict[str, str]
    outputs: list[dict]
    detail_url: str


class ReviewResponse(BaseModel):
    experiment_id: str
    review_type: Literal["AI_secondary_review"]
    reviewer: str
    reviewed_at: str
    reviewed_cases: int = Field(gt=0)
    clinical_eligibility_logic_validated: bool
    method: str
    source: dict[str, str]
    aggregate: dict[str, ReviewAggregate]
    cases: list[ReviewCaseSummary]
    report_url: str


class GoldEntity(BaseModel):
    kind: Literal["Measurement", "Value", "Temporal"]
    spans: list[tuple[int, int]]
    source_fragments: list[str]


class PredictionCheck(BaseModel):
    kind: Literal["Measurement", "Value", "Temporal"]
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    evidence: str
    source_quote_verified: bool
    benchmark_verdict: Literal["exact", "boundary_overlap", "type_overlap", "no_target_overlap"]
    overlapping_target_gold: list[GoldEntity]
    other_exact_annotation_types: list[str]


class AINotes(BaseModel):
    case_id: str
    finding: str
    boundary_and_omissions: str
    context: str
    evidence_quotes: list[str]


class CaseOutput(BaseModel):
    system: str
    metrics: Metrics
    exact_document: bool
    error_patterns: dict[str, int]
    prediction_checks: list[PredictionCheck]
    missing_gold: list[GoldEntity]


class CaseEvidence(BaseModel):
    case_id: str
    record_id: str
    source: str
    gold: list[GoldEntity]
    ai_notes: AINotes
    A: CaseOutput
    B: CaseOutput


class CaseResponse(BaseModel):
    experiment_id: str
    review_type: Literal["AI_secondary_review"]
    reviewer: str
    source_citation: dict[str, str]
    case: CaseEvidence


class MarkdownResponse(PlainTextResponse):
    media_type = "text/markdown"


def unavailable(artifact):
    return HTTPException(status_code=503, detail={
        "code": "research_artifact_unavailable",
        "artifact": artifact,
        "message": "The saved research artifact is missing, unreadable or invalid.",
    })


def read_json(name):
    try:
        value = json.loads((RESULTS_DIR / name).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return value
    except (OSError, UnicodeError, ValueError):
        raise unavailable(name) from None


@router.get("/evaluation", response_model=EvaluationResponse,
            summary="Compare the frozen V3 extraction systems")
def evaluation():
    result = read_json("fresh_evaluation.json")
    manifest = read_json("fresh_manifest.json")
    protocol = read_json("freeze.json")
    try:
        thresholds = protocol["release_thresholds"]
        return EvaluationResponse(
            experiment_id=EXPERIMENT_ID, evaluated_at=result["evaluated_at"],
            mode="saved_research_results",
            dataset={**SOURCE, "records": manifest["records"], "trials": manifest["trials"],
                     "groups": manifest["groups"], "primary_input_max_characters": 1800,
                     "primary_scope": "Identical original source prefix for all systems"},
            selected_pipeline={"model": result["model"], "output_mode": result["mode"],
                               "fusion": result["fusion"], "selection": "Grouped development exact F1"},
            systems=[SystemResult(id=name, label=label, **result["scores"][name])
                     for name, label in SYSTEMS.items()],
            paired_bootstrap=result["paired_bootstrap"],
            publication_improvement_checks_passed=result["improved_on_all_three"],
            release={"semantic_release_passed": result["semantic_release_passed"],
                     "numeric_checks": {key: result["release_checks"][key] for key in ("schema", "precision", "f1")},
                     "numeric_thresholds": {"schema": thresholds["test_min_schema_valid_rate"],
                                            "precision": thresholds["test_min_micro_precision"],
                                            "f1": thresholds["test_min_micro_f1"]},
                     "live_extraction_enabled": False},
            limitations=result["limitations"],
            links={"report": "/extraction/report", "ai_review": "/extraction/review"},
        )
    except (KeyError, TypeError, ValueError):
        raise unavailable("V3 evaluation schema") from None


@router.get("/review", response_model=ReviewResponse,
            summary="Read the completed AI secondary review of 12 cases")
def review():
    data = read_json("ai_second_review.json")
    try:
        cases = []
        for case in data["cases"]:
            cases.append(ReviewCaseSummary(
                case_id=case["case_id"], record_id=case["record_id"],
                findings={key: case["ai_notes"][key] for key in ("finding", "boundary_and_omissions", "context")},
                outputs=[{"label": label, "system": case[label]["system"],
                          "metrics": Metrics(**case[label]["metrics"]).model_dump(),
                          "exact_document": case[label]["exact_document"]} for label in ("A", "B")],
                detail_url=f"/extraction/review/cases/{case['case_id']}",
            ))
        if len(cases) != data["reviewed_cases"]:
            raise ValueError("Review case count mismatch")
        return ReviewResponse(
            experiment_id=EXPERIMENT_ID, source=SOURCE, cases=cases,
            report_url="/extraction/review/report",
            **{key: data[key] for key in ("review_type", "reviewer", "reviewed_at", "reviewed_cases",
                                         "clinical_eligibility_logic_validated", "method", "aggregate")},
        )
    except (KeyError, TypeError, ValueError):
        raise unavailable("AI secondary review schema") from None


@router.get("/review/cases/{case_id}", response_model=CaseResponse,
            summary="Inspect source text, predictions and AI findings for one case")
def review_case(case_id: str = Path(pattern=r"^review-\d{2}$")):
    data = read_json("ai_second_review.json")
    try:
        for case in data["cases"]:
            if case["case_id"] == case_id:
                return CaseResponse(experiment_id=EXPERIMENT_ID, review_type=data["review_type"],
                                    reviewer=data["reviewer"], source_citation=SOURCE, case=case)
    except (KeyError, TypeError, ValueError):
        raise unavailable("AI secondary review schema") from None
    raise HTTPException(404, "Case is outside the saved AI secondary review")


def markdown(name):
    try:
        return MarkdownResponse((RESULTS_DIR / name).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        raise unavailable(name) from None


@router.get("/report", response_class=MarkdownResponse, summary="Read the V3 experiment report")
def experiment_report():
    return markdown("summary.md")


@router.get("/review/report", response_class=MarkdownResponse, summary="Read the complete AI secondary review report")
def review_report():
    return markdown("ai_second_review.md")
