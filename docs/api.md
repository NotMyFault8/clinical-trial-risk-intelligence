# Research API v0.3.0

The local FastAPI service exposes the frozen trial portfolio, the saved V3 CHIA
extraction experiment and its completed AI secondary review. All routes are
read-only. The dashboard at `/` opens on **Extraction results**; the **Trial
portfolio** tab contains the historical trial queue.

## Extraction and AI review routes

| GET route | Content |
|---|---|
| `/extraction/evaluation` | Five system comparisons, identical-prefix primary scores, full-text secondary scores, bootstrap intervals and release status |
| `/extraction/review` | Codex (AI) review metadata, aggregate counts and summaries of all 12 cases |
| `/extraction/review/cases/review-01` | One case's source, gold spans, A/B system identities, predictions, exact-match checks, omissions and AI findings |
| `/extraction/report` | Complete experiment summary as `text/markdown` |
| `/extraction/review/report` | Complete AI secondary review as `text/markdown` |

The case endpoint accepts `review-01` through `review-12` for this saved review.
An unknown well-formed case ID returns 404; an invalid ID format returns 422.
The review routes expose only the AI secondary review.

```sh
curl http://127.0.0.1:8000/extraction/evaluation
curl http://127.0.0.1:8000/extraction/review
curl http://127.0.0.1:8000/extraction/review/cases/review-01
```

Metrics use fractions between zero and one. Primary scores compare 100 documents
from 50 trials / 50 groups on the same maximum 1,800-character source prefix.
The revised LLM + NER pipeline has 88% format validity, 27.5% precision and 36.3%
exact span F1. Its exact F1 remains below token NER alone at 37.7%. Schema validity
measures output format; an exact source quote is not evidence of correct labels.
The numerical release checks all fail and `live_extraction_enabled` is false.

The API serves recorded results without model inference or access to raw CHIA
archives. AI case details retain source offsets and the full set of benchmark
errors. CHIA v2 source excerpts and annotations are attributed to Kury et al.,
[CHIA v2](https://doi.org/10.6084/m9.figshare.11855817.v2), CC BY 4.0. These results
do not establish clinical eligibility logic or prospective validity.

## Existing portfolio routes

| GET route | Content |
|---|---|
| `/portfolio?limit=50` | Frozen 2021 resolved-outcome research portfolio |
| `/trials/NCT00000000/report` | Baseline packet, deterministic report and extraction provenance, when the trial is in the portfolio |
| `/evaluation` | Saved risk-model holdout evaluation |
| `/health` | Readiness of the historical portfolio and its model artifacts |
| `/monitoring` | API version, in-memory request/error counts and latency summaries |
| `/docs` | Interactive OpenAPI documentation |
| `/openapi.json` | Machine-readable API contract |

Portfolio reports use the existing cohort extraction cache. Their
`extraction_provenance.v3_applied_to_this_trial` flag is false: a V3 benchmark
improvement does not mean that portfolio trials have been re-extracted. V3
comparisons are available through `latest_benchmark_url`.

## Artifact availability and packaging

Extraction routes work independently of the historical portfolio's model weights.
They require these saved files under `reports/extraction/llm_v3/`:

- `fresh_evaluation.json`, `fresh_manifest.json` and `freeze.json`;
- `ai_second_review.json`, `summary.md` and `ai_second_review.md`.

`scripts/prepare_release.py` includes those files in the serving bundle and
records their checksums. The container mounts that bundle's reports directory
read-only, as shown in [the runbook](reproducibility.md).

A missing, unreadable or invalid research artifact returns 503 with a stable error
code and the artifact name. Local filesystem paths are not returned:

```json
{
  "detail": {
    "code": "research_artifact_unavailable",
    "artifact": "fresh_evaluation.json",
    "message": "The saved research artifact is missing, unreadable or invalid."
  }
}
```

The service stores no request bodies or trial identifiers. It does not accept
arbitrary trial text or invoke an LLM through these endpoints.

## Verification

The v0.3.0 update passed 37 non-integration tests. Live HTTP checks returned 200
for the five new routes and the existing portfolio, report, evaluation, health,
monitoring and OpenAPI routes. Served micro scores match the saved experiment,
and the six V3 serving-bundle artifacts match their recorded checksums. See the
[verification record](../reports/api/v0_3_verification.json).
