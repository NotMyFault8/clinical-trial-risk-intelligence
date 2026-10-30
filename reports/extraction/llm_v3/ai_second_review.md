# AI Secondary Review: 12 Frozen Cases

**Reviewer: Codex (AI). Cases reviewed: 12/12. Human review remains 0/12.**

This report preserves the human-review process and separately records an AI review of the source text, A/B outputs and CHIA annotations. The A/B system identities are disclosed, so this is an unblinded AI review. Type and boundary counts are recomputed from the existing gold by script; the written interpretations are AI judgments, not human or independent clinical sign-off.

The review used frozen predictions and did not change the model, prompts, gold or experiment scores. Reviewer identity, date and score fields in the human review packet remain unfilled.

Markdown display normalizes line endings and trims trailing whitespace. Character offsets refer to the original text preserved in the JSON record.

## Results for the 12 reviewed cases

| System | Correct TP | False positives FP | Misses FN | Precision | Recall | Exact span F1 | Completely exact documents |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original LLM | 10 | 31 | 63 | 24.4% | 13.7% | 17.5% | 0/12 |
| Revised LLM + NER | 37 | 114 | 36 | 24.5% | 50.7% | 33.0% | 1/12 |

This prespecified 12-document subset does not replace the [100-document primary result](summary.md). A completely exact document must have an exact predicted entity set, including documents with no target gold. The scoring implementation assigns F1=0 when both gold and predictions are empty; the separate exact-document flag shows whether the empty sets match. All retained spans can be traced to the source, but quotation support does not establish semantic correctness.

Main errors include disease or observation terms mislabeled as Measurement; truncated values, units and time windows; duplicate short and complete spans; and forcing labels outside the three target categories, such as Multiplier and Observation, into a target category. The revised system has lower exact F1 than the original on review-02 and review-10. Negation, AND/OR scope, exceptions and patient eligibility were not evaluated.

[Retained human review worksheet](human_review.md) · [Unfilled human review packet](human_review_packet.json) · [Machine-readable AI secondary review](ai_second_review.json)

## review-01 — NCT03119766_exc

```text
Organic diseases of the digestive system (gastro-oesophageal reflux disease (GERD), ulcer, chronic pancreatitis, cholelithiasis, fatty liver disease, hepatitis, cirrhosis of liver, etc.) .
Diagnosis of other functional diseases of the digestive system, such as dyskinesia of cystic duct or gallbladder, irritable bowel syndrome, etc.
Discontinuation of proton pump inhibitors, propulsives, antispasmodics, antacids, or bismuth preparations less than 7 days prior to randomization.
H. Pylori eradication within 2 months before study entry.
Intestinal infection within 2 months before study entry.
Known history of/suspected malignant neoplasm of various sites.
Prior diagnosis of a class IV cardiovascular disease (according to the New York Heart Association, 1964), hypothyroidism, diabetes mellitus, chronic kidney disease (С3-5), or disease of liver with portal hypertension and/or severe decompensation (Child-Pugh score > 6).
Other severe coexisting morbidity which, in the investigator's opinion, can prevent the patient from participating in the study.
Allergy/intolerance to any of the components of medications used in the treatment.
Pregnancy, breast-feeding.
Patients who, from investigator's point of view, will fail to comply with the observation requirements of the trial or with the dosing regimen of the investigational drugs.
Planned hospitalization during the study period, for any diagnostic or treatment procedures.
Drug addiction, alcohol use in the amount over 2 units of alcohol a day, mental diseases.
Intake of medicines listed in the section 'Prohibited concomitant treatment' for 1 month prior to the enrollment in the trial.
Participation in other clinical trials within 3 months to the enrollment in this study.
Patient is related to the research staff of
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Original LLM | 0 / 1 / 14 | 0.0% | No |
| B | Revised LLM + NER | 5 / 37 / 9 | 17.9% | No |

**AI type review:** A labels the substring age inside gastro-oesophageal as a Measurement. Although the characters occur in the source, they are not a standalone entity. B recovers two repeated time windows and Child-Pugh score, but produces many false positives by labeling disease names, a single letter and abbreviations as Measurements.

**Boundaries and omissions:** B includes an extra closing parenthesis in > 6) and an extra for at the start of for 1 month prior to the enrollment in the trial. It still misses target entities such as New York Heart Association.

**Context and limitations:** This is an exclusion criterion. Extracting a disease name or threshold does not parse the exclusion logic and cannot support a patient eligibility decision.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 55:58 | "age" | no overlap with target gold |

Missed target entities:

- Temporal [[442, 481]]: ["less than 7 days prior to randomization"]
- Temporal [[506, 540]]: ["within 2 months before study entry"]
- Temporal [[564, 598]]: ["within 2 months before study entry"]
- Measurement [[737, 763]]: ["New York Heart Association"]
- Value [[687, 695]]: ["class IV"]
- Measurement [[831, 832]]: ["С"]
- Value [[832, 835]]: ["3-5"]
- Measurement [[913, 929]]: ["Child-Pugh score"]
- Value [[930, 933]]: ["> 6"]
- Temporal [[950, 960]]: ["coexisting"]
- Temporal [[1377, 1400]]: ["during the study period"]
- Measurement [[1463, 1474]]: ["alcohol use"]
- Value [[1489, 1518]]: ["over 2 units of alcohol a day"]
- Temporal [[1619, 1663]]: ["1 month prior to the enrollment in the trial"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 42:60 | "gastro-oesophageal" | no overlap with target gold |
| Measurement | 42:82 | "gastro-oesophageal reflux disease (GERD)" | no overlap with target gold; full annotation type: Condition |
| Measurement | 77:81 | "GERD" | no overlap with target gold |
| Measurement | 91:111 | "chronic pancreatitis" | no overlap with target gold; full annotation type: Condition |
| Measurement | 113:127 | "cholelithiasis" | no overlap with target gold; full annotation type: Condition |
| Measurement | 129:148 | "fatty liver disease" | no overlap with target gold; full annotation type: Condition |
| Measurement | 150:159 | "hepatitis" | no overlap with target gold; full annotation type: Condition |
| Measurement | 161:179 | "cirrhosis of liver" | no overlap with target gold; full annotation type: Condition |
| Measurement | 304:328 | "irritable bowel syndrome" | no overlap with target gold; full annotation type: Condition |
| Measurement | 484:485 | "H" | no overlap with target gold |
| Measurement | 554:563 | "infection" | no overlap with target gold |
| Measurement | 628:646 | "malignant neoplasm" | no overlap with target gold; full annotation type: Condition |
| Measurement | 693:695 | "IV" | overlaps an entity with another target type |
| Measurement | 696:718 | "cardiovascular disease" | no overlap with target gold; full annotation type: Condition |
| Measurement | 772:786 | "hypothyroidism" | no overlap with target gold; full annotation type: Condition |
| Measurement | 788:805 | "diabetes mellitus" | no overlap with target gold; full annotation type: Condition |
| Measurement | 807:829 | "chronic kidney disease" | no overlap with target gold; full annotation type: Condition |
| Measurement | 831:835 | "С3-5" | same type overlaps, but boundary differs |
| Measurement | 863:882 | "portal hypertension" | no overlap with target gold; full annotation type: Condition |
| Measurement | 897:911 | "decompensation" | no overlap with target gold |
| Measurement | 913:929 | "Child-Pugh score" | exact type and full boundary match |
| Temporal | 429:441 | "preparations" | no overlap with target gold |
| Temporal | 442:481 | "less than 7 days prior to randomization" | exact type and full boundary match |
| Temporal | 506:540 | "within 2 months before study entry" | exact type and full boundary match |
| Temporal | 564:598 | "within 2 months before study entry" | exact type and full boundary match |
| Temporal | 666:671 | "Prior" | no overlap with target gold |
| Temporal | 1013:1020 | "prevent" | no overlap with target gold |
| Temporal | 1377:1400 | "during the study period" | exact type and full boundary match |
| Temporal | 1489:1501 | "over 2 units" | overlaps an entity with another target type |
| Temporal | 1592:1613 | "concomitant treatment" | no overlap with target gold |
| Temporal | 1615:1663 | "for 1 month prior to the enrollment in the trial" | same type overlaps, but boundary differs |
| Temporal | 1705:1752 | "within 3 months to the enrollment in this study" | no overlap with target gold |
| Value | 442:451 | "less than" | overlaps an entity with another target type |
| Value | 571:579 | "2 months" | overlaps an entity with another target type |
| Value | 666:671 | "Prior" | no overlap with target gold |
| Value | 693:695 | "IV" | same type overlaps, but boundary differs |
| Value | 807:814 | "chronic" | no overlap with target gold |
| Value | 831:835 | "С3-5" | same type overlaps, but boundary differs |
| Value | 913:933 | "Child-Pugh score > 6" | same type overlaps, but boundary differs; full annotation type: Scope |
| Value | 930:934 | "> 6)" | same type overlaps, but boundary differs |
| Value | 1489:1501 | "over 2 units" | same type overlaps, but boundary differs |
| Value | 1581:1591 | "Prohibited" | no overlap with target gold |

Missed target entities:

- Measurement [[737, 763]]: ["New York Heart Association"]
- Value [[687, 695]]: ["class IV"]
- Measurement [[831, 832]]: ["С"]
- Value [[832, 835]]: ["3-5"]
- Value [[930, 933]]: ["> 6"]
- Temporal [[950, 960]]: ["coexisting"]
- Measurement [[1463, 1474]]: ["alcohol use"]
- Value [[1489, 1518]]: ["over 2 units of alcohol a day"]
- Temporal [[1619, 1663]]: ["1 month prior to the enrollment in the trial"]

## review-02 — NCT01312012_inc

```text
pregnant women in 30 to 32 weeks of gestation, with positive HBsAg and HBeAg,serum viral load above 8log10 copies per mL
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Original LLM | 4 / 2 / 3 | 61.5% | No |
| B | Revised LLM + NER | 4 / 3 / 3 | 57.1% | No |

**AI type review:** A and B both retain HBsAg, HBeAg and serum viral load. B adds positive but also returns a truncated serum viral span alongside the complete entity. Both label 30 to 32 weeks as Temporal; in this record, the gold labels the phrase as Value and gestation as Measurement.

**Boundaries and omissions:** B includes an extra in in in 30 to 32 weeks and misses gestation. Both systems miss above 8log10 copies per mL. The revised combination has a lower exact F1 than the original on this case, so the report should not show only examples that improved.

**Context and limitations:** Here, gestational age is labeled as a measurement value, not a relative event-time window. The fixed task labels and context govern this comparison.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 0:14 | "pregnant women" | no overlap with target gold |
| Measurement | 36:45 | "gestation" | exact type and full boundary match |
| Measurement | 61:66 | "HBsAg" | exact type and full boundary match |
| Measurement | 71:76 | "HBeAg" | exact type and full boundary match |
| Measurement | 77:93 | "serum viral load" | exact type and full boundary match |
| Temporal | 18:32 | "30 to 32 weeks" | overlaps an entity with another target type; full annotation type: Value |

Missed target entities:

- Value [[18, 32]]: ["30 to 32 weeks"]
- Value [[52, 60]]: ["positive"]
- Value [[94, 120]]: ["above 8log10 copies per mL"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 61:66 | "HBsAg" | exact type and full boundary match |
| Measurement | 71:76 | "HBeAg" | exact type and full boundary match |
| Measurement | 77:88 | "serum viral" | same type overlaps, but boundary differs |
| Measurement | 77:93 | "serum viral load" | exact type and full boundary match |
| Temporal | 18:32 | "30 to 32 weeks" | overlaps an entity with another target type; full annotation type: Value |
| Value | 15:32 | "in 30 to 32 weeks" | same type overlaps, but boundary differs |
| Value | 52:60 | "positive" | exact type and full boundary match |

Missed target entities:

- Value [[18, 32]]: ["30 to 32 weeks"]
- Measurement [[36, 45]]: ["gestation"]
- Value [[94, 120]]: ["above 8log10 copies per mL"]

## review-03 — NCT03335904_exc

```text
history of hypertension
known impaired renal function
liver disease
heart failure
myocardial infarction
coronary artery disease
smoked within the past year
apnea hypopnea index > 5 events per hour
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Revised LLM + NER | 1 / 4 / 2 | 25.0% | No |
| B | Original LLM | 0 / 0 / 3 | 0.0% | No |

**AI type review:** A returns the full within the past year, then also returns the shorter past and labels the same window as Value. B retains no entities.

**Boundaries and omissions:** A truncates > 5 events per hour to > 5. Neither system fully extracts apnea hypopnea index and its value. Renal function is not labeled Measurement in this record's target gold; this review does not independently judge whether that annotation is clinically appropriate.

**Context and limitations:** The time window, index name and unit convey different information. Keeping only 5 loses the per-hour event rate.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 40:54 | "renal function" | no overlap with target gold |
| Temporal | 141:161 | "within the past year" | exact type and full boundary match |
| Temporal | 152:156 | "past" | same type overlaps, but boundary differs |
| Value | 141:161 | "within the past year" | overlaps an entity with another target type; full annotation type: Temporal |
| Value | 184:187 | "> 5" | same type overlaps, but boundary differs |

Missed target entities:

- Measurement [[163, 183]]: ["apnea hypopnea index"]
- Value [[184, 203]]: ["> 5 events per hour"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| — | — | No retained predictions | — |

Missed target entities:

- Temporal [[141, 161]]: ["within the past year"]
- Measurement [[163, 183]]: ["apnea hypopnea index"]
- Value [[184, 203]]: ["> 5 events per hour"]

## review-04 — NCT02901106_exc

```text
pregnant or breastfeeding woman
patient with a measure of legal protection
subject unaffiliated insurance
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Original LLM | 0 / 3 / 0 | 0.0% | No |
| B | Revised LLM + NER | 0 / 0 / 0 | 0.0% | Yes |

**AI type review:** The gold contains no target Measurement, Value or Temporal entities. B's empty output is an exact document match under this task's gold. A labels descriptions of pregnancy or breastfeeding, legal protection and insurance as Measurements, which do not match the target labels.

**Boundaries and omissions:** B has no false positives or false negatives within the scope of this task. This does not mean these eligibility conditions are absent or unimportant.

**Context and limitations:** This review scores only three entity categories; it does not decide eligibility based on legal clauses or pregnancy status.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 0:25 | "pregnant or breastfeeding" | no overlap with target gold |
| Measurement | 41:75 | "with a measure of legal protection" | no overlap with target gold |
| Measurement | 85:107 | "unaffiliated insurance" | no overlap with target gold |

Missed target entities:

- None.

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| — | — | No retained predictions | — |

Missed target entities:

- None.

## review-05 — NCT00396734_inc

```text
Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Original LLM | 0 / 3 / 0 | 0.0% | No |
| B | Revised LLM + NER | 0 / 3 / 0 | 0.0% | No |

**AI type review:** Both systems label quantity or frequency as a target entity. The complete annotation file labels 1g to 2g a day and 1 to 3 times a week as Multiplier, and cocaine-dependent as Condition. The target gold is therefore empty for this task.

**Boundaries and omissions:** B also returns the clearly incomplete span between 1g to. Both systems have three benchmark false positives; an empty target gold must not be described as an absence of quantity information in the source.

**Context and limitations:** Numbers and time units alone do not determine Value or Temporal labels. Medication dose and frequency must follow the corpus label scope.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 21:38 | "cocaine-dependent" | no overlap with target gold; full annotation type: Condition |
| Value | 60:68 | "1g to 2g" | no overlap with target gold |
| Temporal | 76:95 | "1 to 3 times a week" | no overlap with target gold; full annotation type: Multiplier |

Missed target entities:

- None.

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Temporal | 76:95 | "1 to 3 times a week" | no overlap with target gold; full annotation type: Multiplier |
| Value | 52:65 | "between 1g to" | no overlap with target gold |
| Value | 52:74 | "between 1g to 2g a day" | no overlap with target gold |

Missed target entities:

- None.

## review-06 — NCT03253796_exc

```text
Has bilateral sacroiliitis Grade 2 or unilateral sacroiliitis Grade 3 or Grade 4
Is a nursing or pregnant female, or intends to become pregnant within 6 months after receiving trial medication
Intends to donate eggs (female participants) or sperm (male participants) while receiving trial medication or within 6 months after trial medication
Has any clinically significant condition or situation that would interfere with the trial evaluations or participation in the trial
Has ever received any cytotoxic drugs, including chlorambucil, cyclophosphamide, nitrogen mustard, or other alkylating agents
• Disease-modifying anti-rheumatic drugs (30 days off drug)
• Live vaccinations (3 months off drug)
• Investigational medications (30 days or 5 half-lives off drug, whichever is longer)
• Bacille Calmette-Guerin (BCG) vaccination (12 months off drug)
Has any systemic inflammatory condition, including psoriatic arthritis, active Lyme disease, systemic lupus erythematosus, infectious arthritis, vasculitis, parvovirus infection, rheumatoid arthritis, active uveitis, or active IBD
Has a history of latent or active granulomatous infection prior to Screening
Had a nontuberculous mycobacterial infection or opportunistic infection within 6 months prior to Screening
Has a history of an infected joint prosthesis, or has received antibiotics for a suspected infection of a joint prosthesis, if that prosthesis has not been removed or replaced
Had a serious infection, has been hospitalized for an infection, or has been treated with IV antibiotics for an infection within 2 months prior to Baseline
Had a history of, or ongoing, chronic or recurrent infectious disease
Is known to be infected with human immunodeficiency virus (HIV) or seropositive for hepatitis C virus (HCV)
Has had
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Original LLM | 2 / 5 / 10 | 21.1% | No |
| B | Revised LLM + NER | 8 / 24 / 4 | 36.4% | No |

**AI type review:** B recovers several complete time windows and has much higher recall than A, but mislabels disease names and fragments such as Live, Investigational, whichever and IV as Measurement and emits extra Temporal predictions such as active.

**Boundaries and omissions:** Both systems return 30 days or 5 half-lives off drug, which does not match the gold's discontinuous 30 days | off drug and separate 5 half-lives off drug spans. B still misses complete windows including while receiving trial medication and 12 months off drug.

**Context and limitations:** The source includes whichever is longer and several distinct exclusion conditions. Contiguous span extraction cannot represent the longer-of rule; copied text alone is not a complete rule.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 87:94 | "nursing" | no overlap with target gold; full annotation type: Condition |
| Value | 62:69 | "Grade 3" | no overlap with target gold; full annotation type: Qualifier |
| Value | 269:301 | "while receiving trial medication" | overlaps an entity with another target type; full annotation type: Temporal |
| Temporal | 647:663 | "30 days off drug" | exact type and full boundary match |
| Temporal | 687:704 | "3 months off drug" | exact type and full boundary match |
| Temporal | 738:770 | "30 days or 5 half-lives off drug" | same type overlaps, but boundary differs; full annotation type: Scope |
| Temporal | 1577:1592 | "within 2 months" | same type overlaps, but boundary differs |

Missed target entities:

- Temporal [[145, 193]]: ["within 6 months after receiving trial medication"]
- Temporal [[269, 301]]: ["while receiving trial medication"]
- Temporal [[305, 343]]: ["within 6 months after trial medication"]
- Temporal [[738, 745], [762, 770]]: ["30 days", "off drug"]
- Temporal [[749, 770]]: ["5 half-lives off drug"]
- Temporal [[839, 857]]: ["12 months off drug"]
- Temporal [[1150, 1168]]: ["prior to Screening"]
- Temporal [[1242, 1276]]: ["within 6 months prior to Screening"]
- Temporal [[1577, 1610]]: ["within 2 months prior to Baseline"]
- Temporal [[1633, 1640]]: ["ongoing"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 14:26 | "sacroiliitis" | no overlap with target gold; full annotation type: Condition |
| Measurement | 49:61 | "sacroiliitis" | no overlap with target gold; full annotation type: Condition |
| Measurement | 668:672 | "Live" | no overlap with target gold |
| Measurement | 709:724 | "Investigational" | no overlap with target gold |
| Measurement | 772:781 | "whichever" | no overlap with target gold |
| Measurement | 1545:1547 | "IV" | no overlap with target gold |
| Measurement | 1712:1740 | "human immunodeficiency virus" | no overlap with target gold |
| Measurement | 1712:1745 | "human immunodeficiency virus (HIV" | no overlap with target gold |
| Measurement | 1750:1762 | "seropositive" | no overlap with target gold |
| Measurement | 1786:1789 | "HCV" | no overlap with target gold |
| Measurement | 1786:1790 | "HCV)" | no overlap with target gold |
| Temporal | 145:166 | "within 6 months after" | same type overlaps, but boundary differs |
| Temporal | 145:193 | "within 6 months after receiving trial medication" | exact type and full boundary match |
| Temporal | 305:343 | "within 6 months after trial medication" | exact type and full boundary match |
| Temporal | 647:663 | "30 days off drug" | exact type and full boundary match |
| Temporal | 687:704 | "3 months off drug" | exact type and full boundary match |
| Temporal | 738:770 | "30 days or 5 half-lives off drug" | same type overlaps, but boundary differs; full annotation type: Scope |
| Temporal | 932:938 | "active" | no overlap with target gold; full annotation type: Qualifier |
| Temporal | 1061:1067 | "active" | no overlap with target gold |
| Temporal | 1080:1086 | "active" | no overlap with target gold |
| Temporal | 1119:1125 | "active" | no overlap with target gold; full annotation type: Qualifier |
| Temporal | 1150:1168 | "prior to Screening" | exact type and full boundary match |
| Temporal | 1242:1276 | "within 6 months prior to Screening" | exact type and full boundary match |
| Temporal | 1577:1610 | "within 2 months prior to Baseline" | exact type and full boundary match |
| Temporal | 1633:1640 | "ongoing" | exact type and full boundary match |
| Temporal | 1653:1662 | "recurrent" | no overlap with target gold; full annotation type: Qualifier |
| Temporal | 1763:1766 | "for" | no overlap with target gold |
| Value | 27:34 | "Grade 2" | no overlap with target gold; full annotation type: Qualifier |
| Value | 62:69 | "Grade 3" | no overlap with target gold; full annotation type: Qualifier |
| Value | 73:80 | "Grade 4" | no overlap with target gold; full annotation type: Qualifier |
| Value | 839:841 | "12" | overlaps an entity with another target type |
| Value | 1754:1762 | "positive" | no overlap with target gold |

Missed target entities:

- Temporal [[269, 301]]: ["while receiving trial medication"]
- Temporal [[738, 745], [762, 770]]: ["30 days", "off drug"]
- Temporal [[749, 770]]: ["5 half-lives off drug"]
- Temporal [[839, 857]]: ["12 months off drug"]

## review-07 — NCT02092467_exc

```text
Current or recent infection
Clinically significant laboratory abnormalities
Pregnancy
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Revised LLM + NER | 1 / 5 / 1 | 25.0% | No |
| B | Original LLM | 0 / 2 / 2 | 0.0% | No |

**AI type review:** A correctly retains Current but also labels the whole Current or recent phrase as Temporal and labels the full infection description, laboratory abnormalities and Pregnancy as Value. B labels infection and laboratory abnormalities as Measurement.

**Boundaries and omissions:** The gold labels Current and recent separately. A misses the standalone recent span; B misses both. Clinically significant is not a Temporal gold span in this record.

**Context and limitations:** State modifiers need to be distinguished from the disease or pregnancy condition they modify. Returning the entire criterion does not replace the individual entities.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Temporal | 0:7 | "Current" | exact type and full boundary match |
| Temporal | 0:17 | "Current or recent" | same type overlaps, but boundary differs; full annotation type: Scope |
| Temporal | 29:51 | "Clinically significant" | no overlap with target gold; full annotation type: Qualifier |
| Value | 0:27 | "Current or recent infection" | overlaps an entity with another target type |
| Value | 29:76 | "Clinically significant laboratory abnormalities" | no overlap with target gold |
| Value | 78:87 | "Pregnancy" | no overlap with target gold; full annotation type: Condition |

Missed target entities:

- Temporal [[11, 17]]: ["recent"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 18:27 | "infection" | no overlap with target gold; full annotation type: Condition |
| Measurement | 52:76 | "laboratory abnormalities" | no overlap with target gold; full annotation type: Condition |

Missed target entities:

- Temporal [[11, 17]]: ["recent"]
- Temporal [[0, 7]]: ["Current"]

## review-08 — NCT01313676_inc

```text
Type of subject: outpatient.
Informed consent: Subjects must give their signed and dated written informed consent to participate.
Gender: Male or female. Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception.
Age: >=40 and <=80 years of age at Screening (Visit 1).
Tobacco use: Subjects with a current or prior history of >=10 pack-years of cigarette smoking at screening (Visit 1). Previous smokers are defined as those who have stopped smoking for at least 6 months prior to Visit 1.
Airflow Obstruction:
Subjects with a measured post-albuterol/salbutamol forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio of <=0.70 at Screening (Visit 1).
Subjects with a measured post-albuterol/salbutamol FEV1 >=50 and <=70% of predicted normal values calculated using NHANES III reference equations [Hankinson, 1999; Hankinson, 2010] at Screening (Visit 1).
Post-bronchodilator spirometry will be performed approximately 15 minutes after the subject has self-administered 4 inhalations (i.e., total 400mcg) of albuterol/salbutamol via a metered dose inhaler (MDI )with a valved-holding chamber. The FEV1/FVC ratio and FEV1 percent predicted values will be calculated.
Symptoms of COPD: Subjects must score 2 or higher on the modified Medical Research Council Dyspnea scale (Visit 1)
Cardiovascular disease:
For patients >= 40 years of age: any one of the following:
Established (i.e. by clinical signs or imaging studies) coronary artery disease (CAD) Established (i.e. by clinical signs or imaging studies) peripheral vascular
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Revised LLM + NER | 7 / 24 / 12 | 28.0% | No |
| B | Original LLM | 0 / 6 / 19 | 0.0% | No |

**AI type review:** A recovers several repeated at Screening spans, the full age range and <=0.70. B splits the age range into >=40 and <=80 and has no complete target match. A still emits unmatched Measurements such as age, NHANES and reference.

**Boundaries and omissions:** A truncates the long lung-function measurement name; omits values from >=50 and <=70% of predicted normal values; omits for from for at least 6 months prior to Visit 1; and omits score from score 2 or higher. Abbreviations and long compound entities remain difficult.

**Context and limitations:** The source combines age, smoking exposure, lung function, a dosing procedure and a clinical score. Segmentation improves coverage but does not reliably distinguish all measurement, dose and timing descriptions.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 478:481 | "age" | no overlap with target gold; full annotation type: Person |
| Measurement | 802:831 | "forced expiratory volume in 1" | same type overlaps, but boundary differs |
| Measurement | 847:868 | "forced vital capacity" | same type overlaps, but boundary differs |
| Measurement | 1029:1035 | "NHANES" | no overlap with target gold |
| Measurement | 1040:1049 | "reference" | no overlap with target gold |
| Measurement | 1255:1267 | "total 400mcg" | no overlap with target gold |
| Measurement | 1361:1369 | "FEV1/FVC" | no overlap with target gold |
| Measurement | 1380:1392 | "FEV1 percent" | no overlap with target gold |
| Temporal | 338:340 | "at" | no overlap with target gold |
| Temporal | 482:494 | "at Screening" | exact type and full boundary match |
| Temporal | 482:496 | "at Screening (" | same type overlaps, but boundary differs |
| Temporal | 536:543 | "current" | exact type and full boundary match |
| Temporal | 547:563 | "prior history of" | same type overlaps, but boundary differs |
| Temporal | 601:615 | "at screening (" | same type overlaps, but boundary differs |
| Temporal | 625:633 | "Previous" | no overlap with target gold |
| Temporal | 688:691 | "for" | same type overlaps, but boundary differs |
| Temporal | 692:726 | "at least 6 months prior to Visit 1" | same type overlaps, but boundary differs |
| Temporal | 710:726 | "prior to Visit 1" | same type overlaps, but boundary differs |
| Temporal | 889:901 | "at Screening" | exact type and full boundary match |
| Temporal | 1095:1107 | "at Screening" | exact type and full boundary match |
| Temporal | 1194:1203 | "after the" | same type overlaps, but boundary differs |
| Temporal | 1585:1596 | ">= 40 years" | overlaps an entity with another target type; full annotation type: Value |
| Value | 140:144 | "Male" | no overlap with target gold; full annotation type: Person |
| Value | 180:195 | "post-menopausal" | no overlap with target gold |
| Value | 455:474 | ">=40 and <=80 years" | exact type and full boundary match |
| Value | 564:579 | ">=10 pack-years" | no overlap with target gold; full annotation type: Multiplier |
| Value | 882:888 | "<=0.70" | exact type and full boundary match |
| Value | 970:1004 | ">=50 and <=70% of predicted normal" | same type overlaps, but boundary differs |
| Value | 1183:1185 | "15" | overlaps an entity with another target type |
| Value | 1469:1480 | "2 or higher" | same type overlaps, but boundary differs |
| Value | 1585:1596 | ">= 40 years" | exact type and full boundary match |

Missed target entities:

- Temporal [[601, 613]]: ["at screening"]
- Temporal [[547, 552]]: ["prior"]
- Temporal [[688, 726]]: ["for at least 6 months prior to Visit 1"]
- Temporal [[776, 801]]: ["post-albuterol/salbutamol"]
- Measurement [[802, 878]]: ["forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio"]
- Temporal [[939, 964]]: ["post-albuterol/salbutamol"]
- Measurement [[965, 969]]: ["FEV1"]
- Value [[970, 1011]]: [">=50 and <=70% of predicted normal values"]
- Temporal [[1120, 1139]]: ["Post-bronchodilator"]
- Temporal [[1169, 1199]]: ["approximately 15 minutes after"]
- Value [[1463, 1480]]: ["score 2 or higher"]
- Measurement [[1488, 1535]]: ["modified Medical Research Council Dyspnea scale"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 450:453 | "Age" | no overlap with target gold; full annotation type: Person |
| Measurement | 1361:1375 | "FEV1/FVC ratio" | no overlap with target gold |
| Measurement | 1380:1409 | "FEV1 percent predicted values" | no overlap with target gold |
| Value | 455:459 | ">=40" | same type overlaps, but boundary differs |
| Value | 464:468 | "<=80" | same type overlaps, but boundary differs |
| Value | 970:984 | ">=50 and <=70%" | same type overlaps, but boundary differs |

Missed target entities:

- Value [[455, 474]]: [">=40 and <=80 years"]
- Temporal [[482, 494]]: ["at Screening"]
- Temporal [[601, 613]]: ["at screening"]
- Temporal [[547, 552]]: ["prior"]
- Temporal [[536, 543]]: ["current"]
- Temporal [[688, 726]]: ["for at least 6 months prior to Visit 1"]
- Temporal [[776, 801]]: ["post-albuterol/salbutamol"]
- Measurement [[802, 878]]: ["forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio"]
- Value [[882, 888]]: ["<=0.70"]
- Temporal [[889, 901]]: ["at Screening"]
- Temporal [[939, 964]]: ["post-albuterol/salbutamol"]
- Measurement [[965, 969]]: ["FEV1"]
- Value [[970, 1011]]: [">=50 and <=70% of predicted normal values"]
- Temporal [[1095, 1107]]: ["at Screening"]
- Temporal [[1120, 1139]]: ["Post-bronchodilator"]
- Temporal [[1169, 1199]]: ["approximately 15 minutes after"]
- Value [[1463, 1480]]: ["score 2 or higher"]
- Measurement [[1488, 1535]]: ["modified Medical Research Council Dyspnea scale"]
- Value [[1585, 1596]]: [">= 40 years"]

## review-09 — NCT03471117_exc

```text
Allergy to Glitazones
Myocardial infarction
Heart failure
Angina
History of kidney stones
Liver disease (abnormal liver enzymes)
Anemia (hemoglobin <8 g/dl)
Cancer with current treatment
Previous organ transplantation
Immunosuppressant therapy
Human immunodeficiency virus infection
Pregnancy or lactating
Current tobacco use
Dilantin and oral contraceptive usage due to potential drug interaction with glitazones
Self-identified history of hypoglycemia
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Original LLM | 0 / 0 / 7 | 0.0% | No |
| B | Revised LLM + NER | 5 / 2 / 2 | 71.4% | No |

**AI type review:** B correctly extracts hemoglobin, <8 g/dl and three Temporal spans, recovering more target spans than A's empty output. B labels Human immunodeficiency virus as Measurement and abnormal liver as Value.

**Boundaries and omissions:** The gold separates Value abnormal from Measurement liver enzymes; B matches neither complete span.

**Context and limitations:** Current and Previous appear at separate locations and must retain their source casing. A disease name is not automatically a measurement.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| — | — | No retained predictions | — |

Missed target entities:

- Measurement [[119, 132]]: ["liver enzymes"]
- Value [[110, 118]]: ["abnormal"]
- Measurement [[143, 153]]: ["hemoglobin"]
- Value [[154, 161]]: ["<8 g/dl"]
- Temporal [[176, 183]]: ["current"]
- Temporal [[195, 203]]: ["Previous"]
- Temporal [[318, 325]]: ["Current"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 143:153 | "hemoglobin" | exact type and full boundary match |
| Measurement | 254:282 | "Human immunodeficiency virus" | no overlap with target gold |
| Temporal | 176:183 | "current" | exact type and full boundary match |
| Temporal | 195:203 | "Previous" | exact type and full boundary match |
| Temporal | 318:325 | "Current" | exact type and full boundary match |
| Value | 110:124 | "abnormal liver" | same type overlaps, but boundary differs |
| Value | 154:161 | "<8 g/dl" | exact type and full boundary match |

Missed target entities:

- Measurement [[119, 132]]: ["liver enzymes"]
- Value [[110, 118]]: ["abnormal"]

## review-10 — NCT02872935_exc

```text
Non- English speakers
Height < 4' 11"
BMI >40 Kg/ mm
Antiemetic drug use in the 24 hours prior to cesarean delivery,
Hypertensive diseases of pregnancy
Chronic hypertension receiving antihypertensive treatment
Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Revised LLM + NER | 2 / 4 / 2 | 40.0% | No |
| B | Original LLM | 3 / 5 / 1 | 50.0% | No |

**AI type review:** A and B both retain Height and >40 Kg/ mm. A splits the height cutoff into < 4' and 11" and truncates the time window. B retains the full time window but adds disease spans and the full exclusion clause.

**Boundaries and omissions:** The complete spans are < 4' 11" and in the 24 hours prior to cesarean delivery. In this annotation file, BMI is explicitly Observation; its label is not changed based on a different common convention.

**Context and limitations:** The source writes the BMI unit as Kg/ mm. Preserve the suspicious source wording rather than silently changing it to a more common unit.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 23:29 | "Height" | exact type and full boundary match |
| Measurement | 40:43 | "BMI" | no overlap with target gold; full annotation type: Observation |
| Temporal | 76:109 | "in the 24 hours prior to cesarean" | same type overlaps, but boundary differs |
| Value | 30:34 | "< 4'" | same type overlaps, but boundary differs |
| Value | 35:38 | "11\"" | same type overlaps, but boundary differs |
| Value | 44:54 | ">40 Kg/ mm" | exact type and full boundary match |

Missed target entities:

- Value [[30, 38]]: ["< 4' 11\""]
- Temporal [[76, 118]]: ["in the 24 hours prior to cesarean delivery"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 23:29 | "Height" | exact type and full boundary match |
| Measurement | 40:43 | "BMI" | no overlap with target gold; full annotation type: Observation |
| Measurement | 121:155 | "Hypertensive diseases of pregnancy" | no overlap with target gold; full annotation type: Condition |
| Measurement | 157:214 | "Chronic hypertension receiving antihypertensive treatment" | no overlap with target gold |
| Measurement | 216:329 | "Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection" | no overlap with target gold |
| Value | 44:54 | ">40 Kg/ mm" | exact type and full boundary match |
| Value | 178:214 | "receiving antihypertensive treatment" | no overlap with target gold |
| Temporal | 76:118 | "in the 24 hours prior to cesarean delivery" | exact type and full boundary match |

Missed target entities:

- Value [[30, 38]]: ["< 4' 11\""]

## review-11 — NCT02621541_inc

```text
suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI
signed informed consent
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Revised LLM + NER | 0 / 1 / 0 | 0.0% | No |
| B | Original LLM | 0 / 3 / 0 | 0.0% | No |

**AI type review:** The full annotation labels nonfunctional P-NET and hypervascularity as Condition, CT/MRI as Procedure, and signed informed consent as Informed_consent, so the target gold is empty. A labels hypervascularity as Measurement; B places disease/imaging findings and informed consent under Measurement, Value or Temporal.

**Boundaries and omissions:** A has one and B has three benchmark false positives. Signing consent is not a Temporal entity in this record.

**Context and limitations:** Distinguish the three target labels from the full clinical annotation; do not force every medical concept into one of those categories.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 52:68 | "hypervascularity" | no overlap with target gold; full annotation type: Condition |

Missed target entities:

- None.

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 27:32 | "P-NET" | no overlap with target gold |
| Value | 52:68 | "hypervascularity" | no overlap with target gold; full annotation type: Condition |
| Temporal | 78:101 | "signed informed consent" | no overlap with target gold; full annotation type: Informed_consent |

Missed target entities:

- None.

## review-12 — NCT02445339_exc

```text
Active opioid dependence
Acute or chronic pain requiring opioid treatment
Acute liver injury (liver aminotransferase concentrations >5 times the upper limit of normal)
Health condition considered unsafe for inclusion (at discretion of PI and/or attending physician)
Lack of capacity or willingness to consent
Currently prescribed pharmacotherapy for alcohol dependence (not including treatment of acute alcohol withdrawal syndrome)
Previous significant adverse reaction to naltrexone or diluent
Pregnant, nursing, or not using effective methods of birth control
Prisoners (as defined by Office of Human Research Protection) at the time of enrollment ARE NOT ELIGIBLE for study entry. However, subjects who become prisoners after being enrolled will be included and not be withdrawn from the study. Patients on parole or probation are eligible for enrollment.
```

| Output | System | TP / FP / FN | Exact span F1 | Completely exact |
|---|---|---|---:|---|
| A | Revised LLM + NER | 4 / 7 / 1 | 50.0% | No |
| B | Original LLM | 1 / 1 / 4 | 28.6% | No |

**AI type review:** A recovers the full liver aminotransferase concentrations span, >5 times the upper limit of normal, Previous and at the time of enrollment, but also retains incomplete shorter spans and an unrelated organization name. B exactly matches only at the time of enrollment.

**Boundaries and omissions:** A misses Currently and labels Human Research Protection as Measurement. Active, Acute, at and for do not match the Temporal gold for this record.

**Context and limitations:** The source has both an exclusion for prisoners at enrollment and an exception for people imprisoned after enrollment, along with a not including medication clause. The current outputs do not parse negation or exceptions; they cannot determine patient eligibility.

### A span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 96:118 | "liver aminotransferase" | same type overlaps, but boundary differs |
| Measurement | 96:133 | "liver aminotransferase concentrations" | exact type and full boundary match |
| Measurement | 605:630 | "Human Research Protection" | no overlap with target gold |
| Temporal | 0:6 | "Active" | no overlap with target gold; full annotation type: Qualifier |
| Temporal | 76:81 | "Acute" | no overlap with target gold |
| Temporal | 221:223 | "at" | no overlap with target gold |
| Temporal | 438:446 | "Previous" | exact type and full boundary match |
| Temporal | 632:657 | "at the time of enrollment" | exact type and full boundary match |
| Temporal | 675:678 | "for" | no overlap with target gold |
| Value | 134:142 | ">5 times" | same type overlaps, but boundary differs |
| Value | 134:168 | ">5 times the upper limit of normal" | exact type and full boundary match |

Missed target entities:

- Temporal [[314, 323]]: ["Currently"]

### B span-by-span comparison

| Type | Character offsets | Source text | Gold comparison |
|---|---|---|---|
| Measurement | 355:373 | "alcohol dependence" | no overlap with target gold; full annotation type: Condition |
| Temporal | 632:657 | "at the time of enrollment" | exact type and full boundary match |

Missed target entities:

- Measurement [[96, 133]]: ["liver aminotransferase concentrations"]
- Value [[134, 168]]: [">5 times the upper limit of normal"]
- Temporal [[314, 323]]: ["Currently"]
- Temporal [[438, 446]]: ["Previous"]

## Recommended next steps (not yet run)

1. Add label-exclusion rules and hard negative examples to development data. Distinguish Person, Condition, Observation and Multiplier from the three target labels instead of assigning every medical term or number to a target category. Record corpus disagreements without editing test gold after evaluation.
2. Use NER on the same development folds as the baseline. Compare candidate reranking, type filtering and boundary correction to test whether the LLM contributes independently. The current union adds false positives and should not be selected by recall alone.
3. On development data, evaluate complete unit/operator boundaries, duplicate short-span removal and rejection of substrings inside words. Also test constrained JSON output and an appropriate generation budget. Check rules against abbreviation and punctuation counterexamples instead of patching only these 12 cases.
4. Annotate and evaluate negation, conditional relations, temporal comparisons and exceptions as separate tasks. Freeze a new protocol after development and evaluate it on a new unused sample; record actual human review separately.

## Scope and sources

Type comparisons follow the original CHIA annotations; disagreement with the corpus is not automatically a clinical error. Potential annotation issues and suspicious source units are retained, and test gold is not changed after review. Further development requires a new freeze and evaluation sample.

Source text and gold annotations are from Kury et al., CHIA v2, CC BY 4.0: [paper](https://doi.org/10.1038/s41597-020-00620-0) · [dataset](https://doi.org/10.6084/m9.figshare.11855817.v2). AI interpretations, model predictions and this review are derived work.
