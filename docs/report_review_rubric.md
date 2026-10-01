# Independent report review

Status: **prepared, not performed**. Automated checks are not a substitute for
independent semantic review or a claim of improved analyst usefulness.

Use `reports/generation/blinded_review.json`. Review reports A/B against the
included verified packet; avoid reading `review_key.json` until scoring is frozen.
Formatting differences may still reveal which system produced a report, so this
is an attempted blinded comparison, not a guarantee of effective blinding.

For each report, enumerate material factual claims and record whether each is:
supported, contradicted, unsupported, or an explicitly labeled verification task.
Check that:

1. Numerical values have the correct meaning and reference population, not merely
   the same digits somewhere in the packet.
2. Model associations retain direction, units and reference scale, and are never
   presented as causes, remedies or proven intervention effects.
3. Eligibility quotes have the correct source and preserve context, negation,
   exceptions and uncertainty. A copied span can still be interpreted wrongly.
4. Missing or conflicting evidence produces abstention rather than an invented
   fact. No later outcome of the individual trial appears in a baseline report.
5. The resolved-outcome population, historical source date and lack of prospective
   validation are clear to the reader.

Rate factual support (1–5), clarity (1–5) and usefulness for locating evidence
(1–5). Record a preference or tie for the task: “Identify the three most important
items requiring source verification, and find their supporting passages.” Time
the task if feasible, record errors, and do not infer business cost savings from
preferences alone. Reviewers should record relevant domain expertise. If there
is one reviewer, disclose it; with two, code independently and adjudicate disagreements.

Any fabricated risk value or known future-information violation blocks release.
After review, report denominators, unsupported/contradicted claim rates, source
completeness, inter-reviewer disagreement where available, and paired usefulness
results. Do not replace missing reviews with LLM-as-judge scores. Preserve negative
results. Only then reconsider the free-form generator's release gate.
