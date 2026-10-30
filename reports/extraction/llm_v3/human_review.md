# Human extraction review worksheet

Status: pending. These are unfilled forms, not completed human judgments.

CHIA v2 source text: Kury et al., https://doi.org/10.6084/m9.figshare.11855817.v2, CC BY 4.0.

For display, this Markdown normalizes source line endings and trailing whitespace. Offsets refer to the unchanged original source in human_review_packet.json.

For each case, record your name/expertise/date, judge each A/B span's type and complete boundary, list missed entities, and check source context/negation. Avoid the separate key until scoring is frozen. Return scores in human_review_packet.json or as numbered notes.

## review-01 — NCT03119766_exc

Source:

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

### A

- Measurement [55:58]: "age"

### B

- Measurement [42:60]: "gastro-oesophageal"
- Measurement [42:82]: "gastro-oesophageal reflux disease (GERD)"
- Measurement [77:81]: "GERD"
- Measurement [91:111]: "chronic pancreatitis"
- Measurement [113:127]: "cholelithiasis"
- Measurement [129:148]: "fatty liver disease"
- Measurement [150:159]: "hepatitis"
- Measurement [161:179]: "cirrhosis of liver"
- Measurement [304:328]: "irritable bowel syndrome"
- Measurement [484:485]: "H"
- Measurement [554:563]: "infection"
- Measurement [628:646]: "malignant neoplasm"
- Measurement [693:695]: "IV"
- Measurement [696:718]: "cardiovascular disease"
- Measurement [772:786]: "hypothyroidism"
- Measurement [788:805]: "diabetes mellitus"
- Measurement [807:829]: "chronic kidney disease"
- Measurement [831:835]: "С3-5"
- Measurement [863:882]: "portal hypertension"
- Measurement [897:911]: "decompensation"
- Measurement [913:929]: "Child-Pugh score"
- Temporal [429:441]: "preparations"
- Temporal [442:481]: "less than 7 days prior to randomization"
- Temporal [506:540]: "within 2 months before study entry"
- Temporal [564:598]: "within 2 months before study entry"
- Temporal [666:671]: "Prior"
- Temporal [1013:1020]: "prevent"
- Temporal [1377:1400]: "during the study period"
- Temporal [1489:1501]: "over 2 units"
- Temporal [1592:1613]: "concomitant treatment"
- Temporal [1615:1663]: "for 1 month prior to the enrollment in the trial"
- Temporal [1705:1752]: "within 3 months to the enrollment in this study"
- Value [442:451]: "less than"
- Value [571:579]: "2 months"
- Value [666:671]: "Prior"
- Value [693:695]: "IV"
- Value [807:814]: "chronic"
- Value [831:835]: "С3-5"
- Value [913:933]: "Child-Pugh score > 6"
- Value [930:934]: "> 6)"
- Value [1489:1501]: "over 2 units"
- Value [1581:1591]: "Prohibited"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-02 — NCT01312012_inc

Source:

```text
pregnant women in 30 to 32 weeks of gestation, with positive HBsAg and HBeAg,serum viral load above 8log10 copies per mL
```

### A

- Measurement [0:14]: "pregnant women"
- Measurement [36:45]: "gestation"
- Measurement [61:66]: "HBsAg"
- Measurement [71:76]: "HBeAg"
- Measurement [77:93]: "serum viral load"
- Temporal [18:32]: "30 to 32 weeks"

### B

- Measurement [61:66]: "HBsAg"
- Measurement [71:76]: "HBeAg"
- Measurement [77:88]: "serum viral"
- Measurement [77:93]: "serum viral load"
- Temporal [18:32]: "30 to 32 weeks"
- Value [15:32]: "in 30 to 32 weeks"
- Value [52:60]: "positive"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-03 — NCT03335904_exc

Source:

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

### A

- Measurement [40:54]: "renal function"
- Temporal [141:161]: "within the past year"
- Temporal [152:156]: "past"
- Value [141:161]: "within the past year"
- Value [184:187]: "> 5"

### B

- No retained predictions.

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-04 — NCT02901106_exc

Source:

```text
pregnant or breastfeeding woman
patient with a measure of legal protection
subject unaffiliated insurance
```

### A

- Measurement [0:25]: "pregnant or breastfeeding"
- Measurement [41:75]: "with a measure of legal protection"
- Measurement [85:107]: "unaffiliated insurance"

### B

- No retained predictions.

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-05 — NCT00396734_inc

Source:

```text
Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week
```

### A

- Measurement [21:38]: "cocaine-dependent"
- Value [60:68]: "1g to 2g"
- Temporal [76:95]: "1 to 3 times a week"

### B

- Temporal [76:95]: "1 to 3 times a week"
- Value [52:65]: "between 1g to"
- Value [52:74]: "between 1g to 2g a day"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-06 — NCT03253796_exc

Source:

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

### A

- Measurement [87:94]: "nursing"
- Value [62:69]: "Grade 3"
- Value [269:301]: "while receiving trial medication"
- Temporal [647:663]: "30 days off drug"
- Temporal [687:704]: "3 months off drug"
- Temporal [738:770]: "30 days or 5 half-lives off drug"
- Temporal [1577:1592]: "within 2 months"

### B

- Measurement [14:26]: "sacroiliitis"
- Measurement [49:61]: "sacroiliitis"
- Measurement [668:672]: "Live"
- Measurement [709:724]: "Investigational"
- Measurement [772:781]: "whichever"
- Measurement [1545:1547]: "IV"
- Measurement [1712:1740]: "human immunodeficiency virus"
- Measurement [1712:1745]: "human immunodeficiency virus (HIV"
- Measurement [1750:1762]: "seropositive"
- Measurement [1786:1789]: "HCV"
- Measurement [1786:1790]: "HCV)"
- Temporal [145:166]: "within 6 months after"
- Temporal [145:193]: "within 6 months after receiving trial medication"
- Temporal [305:343]: "within 6 months after trial medication"
- Temporal [647:663]: "30 days off drug"
- Temporal [687:704]: "3 months off drug"
- Temporal [738:770]: "30 days or 5 half-lives off drug"
- Temporal [932:938]: "active"
- Temporal [1061:1067]: "active"
- Temporal [1080:1086]: "active"
- Temporal [1119:1125]: "active"
- Temporal [1150:1168]: "prior to Screening"
- Temporal [1242:1276]: "within 6 months prior to Screening"
- Temporal [1577:1610]: "within 2 months prior to Baseline"
- Temporal [1633:1640]: "ongoing"
- Temporal [1653:1662]: "recurrent"
- Temporal [1763:1766]: "for"
- Value [27:34]: "Grade 2"
- Value [62:69]: "Grade 3"
- Value [73:80]: "Grade 4"
- Value [839:841]: "12"
- Value [1754:1762]: "positive"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-07 — NCT02092467_exc

Source:

```text
Current or recent infection
Clinically significant laboratory abnormalities
Pregnancy
```

### A

- Temporal [0:7]: "Current"
- Temporal [0:17]: "Current or recent"
- Temporal [29:51]: "Clinically significant"
- Value [0:27]: "Current or recent infection"
- Value [29:76]: "Clinically significant laboratory abnormalities"
- Value [78:87]: "Pregnancy"

### B

- Measurement [18:27]: "infection"
- Measurement [52:76]: "laboratory abnormalities"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-08 — NCT01313676_inc

Source:

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

### A

- Measurement [478:481]: "age"
- Measurement [802:831]: "forced expiratory volume in 1"
- Measurement [847:868]: "forced vital capacity"
- Measurement [1029:1035]: "NHANES"
- Measurement [1040:1049]: "reference"
- Measurement [1255:1267]: "total 400mcg"
- Measurement [1361:1369]: "FEV1/FVC"
- Measurement [1380:1392]: "FEV1 percent"
- Temporal [338:340]: "at"
- Temporal [482:494]: "at Screening"
- Temporal [482:496]: "at Screening ("
- Temporal [536:543]: "current"
- Temporal [547:563]: "prior history of"
- Temporal [601:615]: "at screening ("
- Temporal [625:633]: "Previous"
- Temporal [688:691]: "for"
- Temporal [692:726]: "at least 6 months prior to Visit 1"
- Temporal [710:726]: "prior to Visit 1"
- Temporal [889:901]: "at Screening"
- Temporal [1095:1107]: "at Screening"
- Temporal [1194:1203]: "after the"
- Temporal [1585:1596]: ">= 40 years"
- Value [140:144]: "Male"
- Value [180:195]: "post-menopausal"
- Value [455:474]: ">=40 and <=80 years"
- Value [564:579]: ">=10 pack-years"
- Value [882:888]: "<=0.70"
- Value [970:1004]: ">=50 and <=70% of predicted normal"
- Value [1183:1185]: "15"
- Value [1469:1480]: "2 or higher"
- Value [1585:1596]: ">= 40 years"

### B

- Measurement [450:453]: "Age"
- Measurement [1361:1375]: "FEV1/FVC ratio"
- Measurement [1380:1409]: "FEV1 percent predicted values"
- Value [455:459]: ">=40"
- Value [464:468]: "<=80"
- Value [970:984]: ">=50 and <=70%"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-09 — NCT03471117_exc

Source:

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

### A

- No retained predictions.

### B

- Measurement [143:153]: "hemoglobin"
- Measurement [254:282]: "Human immunodeficiency virus"
- Temporal [176:183]: "current"
- Temporal [195:203]: "Previous"
- Temporal [318:325]: "Current"
- Value [110:124]: "abnormal liver"
- Value [154:161]: "<8 g/dl"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-10 — NCT02872935_exc

Source:

```text
Non- English speakers
Height < 4' 11"
BMI >40 Kg/ mm
Antiemetic drug use in the 24 hours prior to cesarean delivery,
Hypertensive diseases of pregnancy
Chronic hypertension receiving antihypertensive treatment
Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.
```

### A

- Measurement [23:29]: "Height"
- Measurement [40:43]: "BMI"
- Temporal [76:109]: "in the 24 hours prior to cesarean"
- Value [30:34]: "< 4'"
- Value [35:38]: "11\""
- Value [44:54]: ">40 Kg/ mm"

### B

- Measurement [23:29]: "Height"
- Measurement [40:43]: "BMI"
- Measurement [121:155]: "Hypertensive diseases of pregnancy"
- Measurement [157:214]: "Chronic hypertension receiving antihypertensive treatment"
- Measurement [216:329]: "Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection"
- Value [44:54]: ">40 Kg/ mm"
- Value [178:214]: "receiving antihypertensive treatment"
- Temporal [76:118]: "in the 24 hours prior to cesarean delivery"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-11 — NCT02621541_inc

Source:

```text
suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI
signed informed consent
```

### A

- Measurement [52:68]: "hypervascularity"

### B

- Measurement [27:32]: "P-NET"
- Value [52:68]: "hypervascularity"
- Temporal [78:101]: "signed informed consent"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____

## review-12 — NCT02445339_exc

Source:

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

### A

- Measurement [96:118]: "liver aminotransferase"
- Measurement [96:133]: "liver aminotransferase concentrations"
- Measurement [605:630]: "Human Research Protection"
- Temporal [0:6]: "Active"
- Temporal [76:81]: "Acute"
- Temporal [221:223]: "at"
- Temporal [438:446]: "Previous"
- Temporal [632:657]: "at the time of enrollment"
- Temporal [675:678]: "for"
- Value [134:142]: ">5 times"
- Value [134:168]: ">5 times the upper limit of normal"

### B

- Measurement [355:373]: "alcohol dependence"
- Temporal [632:657]: "at the time of enrollment"

Reviewer: ____  Expertise: ____  Date: ____

A: correct types ___ / total ___; correct boundaries ___ / total ___

B: correct types ___ / total ___; correct boundaries ___ / total ___

Misses/context errors/preference: ____
