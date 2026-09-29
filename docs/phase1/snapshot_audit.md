# Historical Snapshot Coverage Audit

Status: **web coverage verified; archive contents still require local audit**.

## Verified availability

AACT currently provides downloadable historical snapshots and warns that database/schema structure can change over time.

The public archive exposes monthly snapshots back to **2017**. Examples verified from the current download pages:
- 2017 archives exist from January through December, although dates are not always the first day of the month.
- 2018 and 2019 have regular monthly archives.
- 2020 has regular monthly archives.
- 2021 has gaps in the visible monthly sequence (for example July/August are not listed on the current page).
- 2022 also has irregularities/gaps in the visible sequence.
- 2023-2026 monthly archives are available; recent daily snapshots are also published.

Therefore code must use an explicit snapshot catalog rather than assuming every calendar month has exactly one archive.

## Format decision

Primary longitudinal ingestion candidate: **flat text export archives**.

Reason:
- selective table loading is easier;
- we can normalize changing schemas into our own PostgreSQL staging layer;
- each staged row can carry an explicit `snapshot_date`;
- we avoid repeatedly restoring many complete PostgreSQL databases.

Native PostgreSQL dumps should be retained as a validation option for schema spot-checks.

## Candidate frozen outcome snapshot

**2026-09-01** monthly archive.

This provides a stable, reproducible ascertainment cutoff. It is not yet the final label cutoff until follow-up maturity is measured.

## Feasibility pilot

First download a small cross-era set rather than the complete history. Suggested pilot:
- one early snapshot: 2018;
- one pre-pandemic snapshot: 2019;
- one pandemic-era snapshot: 2020 or 2021;
- one later snapshot: 2022 or 2023;
- frozen outcome snapshot: 2026-09-01.

For each archive record:
- exact archive filename;
- archive date;
- compressed size;
- SHA-256 checksum;
- retrieval timestamp;
- included table/file list;
- schema signature for required tables.

## Required checks

- schema drift across selected dates;
- intended versus observed table grain;
- `nct_id` uniqueness in `studies`;
- field-name/type compatibility;
- counts and missingness for start-date fields;
- number of trials already posted but still pre-start;
- number satisfying candidate 30/60/90-day prediction windows;
- outcome maturity when linked to 2026-09-01;
- storage/time estimate for monthly expansion.

## Important limitation

A historical snapshot only proves what AACT/ClinicalTrials.gov exposed by that snapshot date. It does not prove that a pretrained language model lacked later knowledge about the trial. That contamination issue must be handled separately if pretrained embeddings or LLM extraction are introduced later.
