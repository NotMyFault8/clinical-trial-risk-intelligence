# Historical Snapshot Coverage Audit

Status: **2018-09-01 archive inspected; later-era and outcome archives remain uninspected**.

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

## Next pilot: verified catalog entries

Inspected the signed-in AACT **Flat Text Files** catalog in Chrome. These are
listing observations. The 2018 archive has since been downloaded and inspected below; the other two remain listing-only observations.

| Role | Date | Displayed compressed size | Download entry | Listing |
|---|---|---|---|---|
| First historical predictor pilot | 2018-09-01 | 808 MB | [378](https://aact.ctti-clinicaltrials.org/snapshots/378/download) | [2018 flat files](https://aact.ctti-clinicaltrials.org/snapshots/flat/2018) |
| Later-era compatibility pilot | 2023-09-01 | 1.6 GB | [2241](https://aact.ctti-clinicaltrials.org/snapshots/2241/download) | [2023 flat files](https://aact.ctti-clinicaltrials.org/snapshots/flat/2023) |
| Candidate frozen outcome source | 2026-09-01 | 2.3 GB | [4359](https://aact.ctti-clinicaltrials.org/snapshots/4359/download) | [Recent flat files](https://aact.ctti-clinicaltrials.org/snapshots/flat) |

All three listings display “52 text files.” The inspected 2018 ZIP actually contains 42 files, demonstrating why archive contents must be verified. Displayed sizes are rounded; the three listed archives total approximately 4.7 GB compressed. Exact sizes and contents for the later two archives remain unverified.

The 2018 page contains January 11 and March 14 entries, and the 2023 page contains
January 2 and July 2 entries. This confirms that archive dates must come from an
explicit catalog rather than assumed first-of-month filenames. Earlier notes
about other years' coverage are prior observations, not rechecked in this step.

### First hands-on step completed

The **2018-09-01** ZIP was inspected directly without extracting it or loading a PostgreSQL database. Its filename, byte size, SHA-256, member inventory, core headers, table cardinalities, and candidate-window measurements are saved in `data/aact/2018-09-01/audit_results.json`. Operational execution dates/times are not recorded; source snapshot dates are retained because they define the analysis.

Then inspect 2023-09-01 for a later-era comparison and use the frozen 2026-09-01
source to examine outcome status and follow-up. These isolated dates are a
feasibility pilot only: they cannot find the first eligible snapshot across the
full monthly history, establish a final cohort, or justify model training.

The key question is: **Can the historical version show a trial before its planned
start, with usable features, and can a later frozen source establish its outcome?**

## Measured pilot: snapshot 2018-09-01

This is a single-snapshot feasibility audit, not a final cohort or outcome analysis. Counts below were measured from the downloaded archive; the live database was not queried.

| Source item | Measured value |
| --- | --- |
| Archive | 4bpc2vfyhwnjt9cz1p1xbamts1kl.zip |
| Download entry | https://aact.ctti-clinicaltrials.org/snapshots/378/download |
| Compressed bytes | 847,151,707 |
| Uncompressed bytes | 5,331,405,892 |
| Table files | 42 |
| Internal ZIP CRC check | Passed for all 42 files |
| Archive SHA-256 | dfd02e20d48b3d990ffb05c0619812e9121dbcff641f54980872591c6b0c1529 |

The ZIP is retained under `data/aact/2018-09-01/`, which Git ignores. It occupies about 808 MiB compressed; full extraction would occupy about 4.97 GiB. It was not fully extracted. SHA-256 identifies this local archive; no publisher-provided checksum was available for comparison. The website lists its snapshot date as 2018-09-01, and the newest first-posted study date in its contents is 2018-08-31.

### Study IDs and vocabulary

| Check | Result |
| --- | --- |
| Study rows | 283,078 |
| Distinct nonempty NCT IDs | 283,078 |
| Missing / excess duplicate study-ID rows | 0 / 0 |
| Interventional studies | 224,796 |
| First-posted dates after snapshot | 0 |

**study_type — all studies**

| Value | Rows |
| --- | --- |
| Interventional | 224,796 |
| Observational | 52,816 |
| Observational [Patient Registry] | 4,168 |
| N/A | 795 |
| Expanded Access | 503 |

**start_date_type — all studies**

| Value | Rows |
| --- | --- |
| Actual | 64,179 |
| Anticipated | 12,499 |
| NULL | 206,400 |

**enrollment_type — all studies**

| Value | Rows |
| --- | --- |
| Actual | 161,214 |
| Anticipated | 104,978 |
| NULL | 16,886 |

Unlike the live database’s ESTIMATED spelling, this archive uses Anticipated for planned start and enrollment types. Interventional start-date type is Anticipated for 9,981 studies, Actual for 50,666, and blank for 164,149. There are 2,974 interventional studies with a missing start date. The 30/60/90-day counts do not fill missing values from a later registry version.

### Candidate counts and exclusions

The provisional rule requires: interventional study type; valid start date; planned start type (case-normalized Anticipated or Estimated); first posting no later than 2018-09-01; and a recorded planned start strictly after 2018-09-01. In this archive all matching planned types are Anticipated. Windows include their upper endpoint.

| Sequential step | Remaining rows | Removed at this step |
| --- | --- | --- |
| All studies | 283,078 | — |
| Interventional | 224,796 | 58,282 |
| Valid start date | 221,822 | 2,974 |
| Planned start type | 9,981 | 211,841 |
| Posted by snapshot | 9,981 | 0 |
| Recorded start after snapshot | 2,729 | 7,252 |
| Recorded start within 90 days | 2,033 | 696 |

| Window | Using normalized start_date | Definitely inside using date precision | Possibly inside using date precision |
| --- | --- | --- | --- |
| 30 days | 1,378 | 705 | 1,664 |
| 60 days | 1,790 | 1,117 | 1,790 |
| 90 days | 2,033 | 1,360 | 2,033 |

The windows are nested, so they must not be added together. “Definitely” and “possibly” describe uncertainty in the reported planned date only; neither establishes that the trial actually started or meets the eventual final cohort rules.

### Date precision is a cohort-design issue

Among planned, posted interventional records with valid start dates, 4,468 report only a month and year; all 4,468 have a normalized start_date equal to that month’s last day. We treated the original month-only report as an interval from the first through the last day, rather than treating the normalized day as a known event date. All original start-date texts in this subgroup parsed as a full date or month/year.

For a window from snapshot date S through S + W, a reported interval [L, U] is definitely eligible when L > S and U <= S + W; it is possibly eligible when U > S and L <= S + W. Exact dates have L = U. These are alternative eligibility diagnostics, not new outcome labels.

Of the 2,033 normalized 90-day candidates, 1,075 have month-only start text. For example, “September 2018” is stored as 2018-09-30, yet the stated month also includes the snapshot date. It cannot prove a start strictly after September 1. For the 30-day window, “October 2018” may include October 1 (inside that window) even though its normalized October 31 lies outside. This explains why the possible 30-day count exceeds the normalized count.

Do not lock the cohort until a date-precision rule is selected. A conservative candidate is definite eligibility, with possible/normalized alternatives retained for sensitivity analysis. Preserve both start_date and start_month_year.

### Baseline status and enrollment checks

| Status at the 2018 snapshot | 90-day normalized candidates |
| --- | --- |
| Not yet recruiting | 1868 |
| Enrolling by invitation | 17 |
| Recruiting | 131 |
| Withdrawn | 11 |
| Suspended | 6 |

Eleven candidates were already Withdrawn and six Suspended. Their future planned date does not make them an ordinary not-yet-started risk population. We have flagged them, not silently removed them or assigned outcome labels. Recruiting before a planned study start is not automatically invalid; it needs interpretation of recruitment versus actual study-start timing.

| Enrollment type at snapshot | 90-day normalized candidates |
| --- | --- |
| Anticipated | 2021 |
| Actual | 12 |

All 2,033 have a nonblank enrollment value, but 12 are marked Actual. Availability in a historical snapshot does not make actual enrollment equivalent to planned enrollment. The intersections among date ambiguity, baseline status, and actual enrollment have not been measured; do not subtract these counts independently.

### Core-table coverage

| Table | Rows | Trials represented | Max rows/trial | All studies missing records | 90-day candidates missing records |
| --- | --- | --- | --- | --- | --- |
| designs | 283,078 | 283,078 | 1 | 0 | 0 |
| eligibilities | 283,078 | 283,078 | 1 | 0 | 0 |
| sponsors | 447,563 | 283,078 | 92 | 0 | 0 |
| conditions | 461,548 | 282,272 | 263 | 806 | 0 |
| interventions | 491,855 | 251,318 | 97 | 31,760 | 0 |
| facilities | 2,037,073 | 249,485 | 3,511 | 33,593 | 842 |

All six child tables have zero blank NCT-ID rows and zero orphan NCT IDs. Designs and eligibilities have exactly one row per trial. Each trial has exactly one lead sponsor. Sponsor/condition/intervention/facility repetitions are expected one-to-many relationships, not automatically duplicate entities.

The 842 candidates without facilities represent 41.42% of the 90-day normalized group. This means no facility rows were listed, not that the eventual trial necessarily had zero sites. Missing site information must remain distinct from a known zero-site design. All 2,033 candidates have nonblank eligibility criteria, age fields, gender, and healthy-volunteer values; however, minimum age is N/A for 84 and maximum age is N/A for 992. Nonblank text is not proof of a usable numerical boundary.

### Schema differences from the saved live audit

| Table | 2018 columns | Live-audit columns | Columns only in live audit |
| --- | --- | --- | --- |
| studies | 61 | 71 | baseline_type_units_analyzed, delayed_posting, expanded_access_nctid, expanded_access_status_for_nctid, fdaaa801_violation, ipd_access_criteria, ipd_time_frame, ipd_url, patient_registry, source_class |
| designs | 14 | 14 | None |
| eligibilities | 11 | 14 | adult, child, older_adult |
| sponsors | 5 | 5 | None |
| conditions | 4 | 4 | None |
| interventions | 5 | 5 | None |
| facilities | 8 | 10 | latitude, longitude |

This compares header names only; flat-file headers do not establish native PostgreSQL types. The seven core files contain 108 columns in total versus 123 in the saved live audit. study_references is present in the archive but excluded from analysis as requested.

### Reproduce this pilot

One reusable script, `scripts/audit_snapshot.py`, reads the ZIP directly. It saves measurements, exact candidate-ID lists, the archive inventory and headers, and content hashes in one ignored JSON file. It records source dates only, not execution dates or times. Use a fresh output path when rerunning so earlier results are not overwritten.

```sh
python3 scripts/audit_snapshot.py \
  --archive data/aact/2018-09-01/4bpc2vfyhwnjt9cz1p1xbamts1kl.zip \
  --snapshot-date 2018-09-01 \
  --catalog-url https://aact.ctti-clinicaltrials.org/snapshots/378/download \
  --live-audit reports/phase1/schema_audit_2026-09-29/audit_results.json \
  --output data/aact/2018-09-01/audit_results_repeat.json
```

Validation passed: every ZIP member’s CRC, every inspected record’s field count, unique/nonblank study IDs, study-type totals, the mutually exclusive exclusion waterfall, nested candidate windows, date-precision bounds, and child-table coverage reconciliation. No SQL database was loaded or changed.

### Decision after the first pilot

The archive is structurally usable and yields a measurable pre-start candidate population. Historical feasibility is only partially established: date precision, baseline withdrawn/suspended states, planned-versus-actual enrollment, and missing facilities require explicit rules. The next cohort-design step is to decide those rules before locking eligibility; later archive inspection and outcome follow-up remain necessary. No model training or outcome labeling was performed.
