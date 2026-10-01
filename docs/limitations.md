# Scope and unresolved evidence

- **Outcome selection:** only about 40–44% of eligible annual-landmark trials are
  Completed/Terminated at five years. Conditional estimates do not apply to the
  entire newly starting trial population. Other statuses are retained, not
  silently treated as negative labels.
- **Historical availability:** records are historical, but training labels mature
  after the holdout baseline date. This is retrospective temporal generalization,
  not an actually deployable model at the historical landmark.
- **Annual sampling:** selected September snapshots miss trials entering a short
  pre-start window between landmarks. First eligibility means first among those
  selected snapshots. No population-wide incident-trial claim.
- **Registry reporting:** planned dates, reported statuses and listed facilities
  can be incomplete, stale or revised. Exact event times and intervening status
  transitions are not reconstructed. Baseline Recruiting records may already have
  enrolled participants despite a future planned start.
- **Small effective sample:** 217 training and 116 holdout terminations limit
  subgroup precision and model complexity. Sponsor-cluster intervals condition on
  fitted models and do not represent all estimation uncertainty.
- **Interpretability:** coefficients/TreeSHAP are associations. Embedding PCA
  dimensions are not named clinical mechanisms. No intervention effects, patient
  treatment recommendations, trial-cancellation decisions or causal claims.
- **Pretrained models:** source-only prompts and frozen snapshots cannot prove
  freedom from pretraining contamination. Training cutoffs are undocumented here.
  Modern pretrained tools are not simulated as historically available.
- **Extraction:** published CHIA annotations are external Phase-IV data. Exact
  span tests do not validate full clinical logic, units normalization or the local
  target domain. The frozen extractor failed its release thresholds. Four test
  exclusion files share the generic text “NA” with development; no substantive
  annotated criterion overlap was found by the exact-text check. One test target
  annotation has mismatched source offsets; this was disclosed, not corrected
  after observing performance.
- **Generation:** automated numeric/citation checks do not establish semantic
  faithfulness or usefulness. Independent review forms are prepared but unfilled.
  Free-form generation is experimental and withheld; templates are served.
- **Deployment:** a local read-only research app/container is not a clinically
  validated production deployment. No cloud service, fine-tuning, RAG, new expert
  annotation, employment attribution, business impact or cost savings is claimed.

The research code and negative experiments can be useful while a component fails
its release gate. Full pre-context completion still requires independent target-
domain/report evaluation; genuine prospective validation would require later
outcomes and an appropriate deployment study rather than more retrospective tuning.
