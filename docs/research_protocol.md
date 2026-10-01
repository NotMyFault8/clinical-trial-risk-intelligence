# Locked retrospective research protocol

This protocol is written before fitting predictive models or viewing holdout
performance. The machine-readable settings are `configs/analysis_protocol.json`;
each experiment records its checksum. Source and protocol edits create a new
version, never a silently retuned final test.

## Population and information boundary

Use annual September 1 landmarks in 2018–2021, not all newly registered trials.
At the first selected landmark satisfying eligibility, the trial must be
interventional, already posted, have a planned (Anticipated/Estimated) start,
and be Not yet recruiting, Recruiting or Enrolling by invitation. The complete
reported start-date interval must lie strictly after the landmark and within
90 days. Month-only dates are intervals; they are not known month-end starts.
First eligibility is among the selected annual snapshots, not all historical
registry versions. A second cohort admits intervals overlapping the window.

All seven feature tables come from that same archive. SQL aggregates each child
before joining. Only explicitly named features enter model matrices. Actual
enrollment is missing planned enrollment. Missing listed facilities are unknown,
not evidence of zero sites. Later status is only in the separate outcomes file.
Planned starts can change and apparently pre-start Recruiting records can reflect
registry lag. This is a registry-information design, not proof no participant
had yet enrolled. Missing source versions are never repaired from live records.

## Estimand and source feasibility gate

The primary exploratory estimand is the probability of a **reported Terminated
status conditional on Completed or Terminated at the five-year snapshot**, within
this selected annual landmark population. It is not population-wide termination
probability or time-to-event risk. Completion and termination dates are not used
to invent exact event times. Source status is a snapshot observation, potentially
stale or corrected; intervening status transitions are not recovered.

| Baseline | Eligible primary | Completed | Terminated | Resolved fraction |
|---|---:|---:|---:|---:|
| 2018-09-01 | 1,349 | 434 | 108 | 40.18% |
| 2019-09-01 | 1,365 | 456 | 109 | 41.39% |
| 2020-09-01 | 1,517 | 557 | 116 | 44.36% |
| 2021-09-01 | 1,472 | 516 | 116 | 42.93% |

Five-year follow-up does not resolve selection: most baseline trials are excluded
from this binary comparison. We retain their statuses and compare baseline
distributions with the resolved sample. No automatic negative labels for ongoing,
unknown, withdrawn, suspended or missing records. A separate sensitivity treats
Withdrawn and Terminated as a combined discontinuation endpoint against Completed;
its meaning differs from the primary endpoint. Missing outcome records are counted.

**Phase-1 gate passes only for a limited retrospective research comparison.**
The downloaded archives have hashes, verified schemas and streamed CRC checking
for consumed members; trial keys and child references are checked. The sample has
217 training, 116 validation and 116 test terminations. This supports a modest
regularized experiment, not precise subgroup or clinical-effect claims. The full
cohort/status/cardinality audit is in `reports/cohort/audit.json`.

## Evaluation

Train on 2018–2019 (1,107 resolved trials); tune on half the 2020 lead-sponsor
groups; fit calibration on the other half. The sponsor hash, not labels, assigns
that partition. Freeze 2021 (632 resolved trials) for the final comparison.
Predictors and calibrators never fit on test records. Sponsor identities serve
grouping and uncertainty only, not as model inputs. Repeated sponsors across
years are allowed: this estimates future-cohort rather than new-sponsor transfer.

**This is retrospective temporal generalization, not historically deployable
pseudo-prospective validation.** Training outcomes ascertained in 2023–2024 were
not available at the 2021 test landmark. A real prospective deployment needs
training labels available before its deployment date and subsequently collected
outcomes. Neither frozen archives nor ordered baseline years solve that delay.

Primary hypothesis: adding eligibility TF-IDF to the same structured logistic
baseline improves held-out average precision (AP). Secondary comparisons: simple
counts, frozen MiniLM embeddings, validated LLM-derived span counts, and XGBoost.
Use the same primary trials, labels and splits. Four candidates per family;
preprocessing and vocabulary fit on training only. Do not require improvements.
Pretrained-model experiments are retrospective tools: training contamination
cannot be excluded and model release dates are not known training cutoffs.

Select regularization/boosting configuration by tuning AP. Fit a prespecified
Platt calibrator on the disjoint calibration partition. Report raw, Platt and
isotonic diagnostics without picking a calibrator from test performance. The
published primary probability uses Platt. Calibration changes discrimination
only through ties or a possible negative slope; report that slope. The fixed
classification threshold is 0.5; top-5/10/20% queues are more relevant to review.

Report AP, ROC-AUC, precision, recall, F1, balanced accuracy, Brier, ten-bin
calibration and top-K recall/precision/lift. Quantify paired AP/Brier differences
with 1,000 sponsor-cluster bootstrap replicates, reusing each sampled set for
both models. Sparse/one-class subgroups get counts and undefined metrics, not
invented estimates. No test-driven model promotion or additional tuning.

Audit phase, sponsor class, geography, enrollment and temporal drift. Sensitivities
use the locked settings and are explicitly secondary: broader date eligibility,
combined withdrawal endpoint, removal of facilities, zero numeric imputation,
and removing test texts nearly identical to training texts. Explain coefficients
or tree attributions as associations, not effects of operational interventions.

## Text and reporting release boundary

Compare rule and local LLM extraction against a pinned human-annotated CHIA
benchmark. CHIA is an external Phase-IV corpus; its labels do not validate every
possible structured constraint, clinical logic or this cohort's entire domain.
Use exact source spans, retain failures and missingness, isolate benchmark tests,
and publish schema/span error rates and latency. Do not interpret extractor
confidence as clinical validity. No API trial data are sent to hosted LLMs.

A deterministic evidence report is the default. Generated text cannot revise
typed probabilities or introduce outcomes into baseline reports. Automated
numeric/source tests do not replace independent semantic or usefulness review.
If that review is unavailable, keep free-form generation experimental and do not
claim its release gate passed. Optional retrieval/fine-tuning are not required.

## Reporting qualification gate (frozen before predictive holdout scoring)

The extraction development pilot failed. Before any 2021 predictive score was inspected, `configs/extraction_release.json` froze final extraction thresholds and the rule that failed-gate LLM features are ineligible for the local serving model. They remain in the prespecified exploratory comparison on the same trials. Model selection for the demonstrator uses the highest tuning AP among qualified components. This qualification does not change the primary TF-IDF hypothesis or its evaluation.
