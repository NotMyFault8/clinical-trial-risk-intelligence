# Approved baseline features

Every field below is read from the selected baseline archive, never a later
snapshot. Availability is the archive snapshot date. Values can change in later
registry versions; those later versions are not substituted. The serving and
training allowlists share `features/build.py`. Outcome fields cause that function
to fail. Metadata IDs, dates and sponsor names never enter the estimator.

| Model field(s) | Source | Transformation and missingness | Interpretation / risk |
|---|---|---|---|
| phase | studies.phase | Lowercase categorical; missing level | Includes legitimate N/A interventional phases |
| planned_enrollment, planned_enrollment_missing | studies.enrollment, enrollment_type | Only Anticipated/Estimated accepted; log1p numeric; otherwise missing and flag | Actual enrollment explicitly excluded |
| number_of_arms | studies.number_of_arms | log1p; training-fitted imputation | Planned design complexity proxy |
| has_dmc | studies.has_dmc | Categorical with missing level | Registry-reported oversight indicator |
| allocation, intervention_model, primary_purpose, masking | designs | Categorical; rare training levels grouped at count <5 | One design row per selected trial checked |
| gender, healthy_volunteers | eligibilities | Categorical with missing level | Historical vocabulary retained; not patient-level data |
| min_age_years, max_age_years, age_width | eligibilities.minimum_age, maximum_age | Convert units to years; N/A missing; impossible negative width missing | Approximate year conversion for days/weeks; no guessed missing limits |
| sponsor_class | sponsors.agency_class | Class of exactly one lead sponsor | Name used only for grouping, not a predictor |
| collaborator_count | sponsors.lead_or_collaborator | Count collaborator rows; log1p | Registry collaborators, not validated operational partnerships |
| condition_count | conditions.name | Distinct lowercase names, log1p | Registry naming is not a standardized diagnosis ontology |
| therapeutic_area | conditions.name | Fixed keyword hierarchy: cancer, infection, cardiovascular, metabolic, neurologic, other | Coarse proxy; multiple areas reduced by documented order; not clinical coding |
| intervention_count, intervention_type_count | interventions | Row/type counts, log1p | Counts visible at prediction time |
| has_drug, has_device, has_behavioral | interventions.intervention_type | Fixed type indicators | Absence means not listed, not independently confirmed absence |
| facility_count, country_count, has_us_site | facilities | Listed row/distinct country counts; log1p for counts | Missing table coverage stays missing; not zero future sites |
| facilities_unlisted | facilities key coverage | Missing-coverage flag | Can reflect reporting completeness and sponsor practice |
| text_words, text_lines | eligibilities.criteria | log1p word/line counts | Formatting affects counts |
| inclusion_mentions, exclusion_mentions | eligibilities.criteria | log1p heading-word occurrence counts | Mentions, not accurate criterion counts |
| numeric_mentions, threshold_mentions | eligibilities.criteria | log1p regex counts | Simple lexical proxies; no complete operator logic |
| negation_mentions, conjunction_mentions | eligibilities.criteria | log1p token counts | No scope resolution |
| lab_mentions, prior_therapy_mentions | eligibilities.criteria | log1p fixed keyword counts | Transparent, incomplete clinical lexicons |
| TF-IDF terms | eligibilities.criteria | Train-only unigram/bigram vocabulary, min_df=3, max 6,000, sublinear TF | Full source text; no pretrained language knowledge |
| 32 embedding components | eligibilities.criteria | Frozen MiniLM: 100-word chunks, 256-token cap, normalized average, train-only PCA/scaling | Token truncations counted; components are latent, not named clinical reasons |
| llm_measurement_count, llm_value_count, llm_temporal_count | baseline eligibility prefix | Counts of retained exact spans from frozen local extractor | Experimental entity types; quotation support does not establish clinical correctness |
| llm_failure, llm_truncated, llm_rejected_count | extraction provenance | Preserve failed/partial extraction rather than drop trials | Operational/coverage signals, not clinical constraints |

Numeric imputation (median plus missing indicators) and scaling are fit on training
only. Categorical encoding learns levels on training only and handles unknown
levels. Zero imputation and removing facilities are prespecified sensitivities.

Excluded from all baseline matrices: outcome status, why_stopped, actual completion,
actual enrollment, results, later registry updates, sponsor identity, trial ID,
title, ascertainment snapshot and label. The raw input schema includes only
approved source fields plus non-predictive lineage/grouping fields. No study
references are used.
