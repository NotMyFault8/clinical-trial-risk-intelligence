# AI 二次复核：12 份冻结样本

**复核者：Codex（AI）。已复核 12/12；真人审核仍为 0/12。**

本报告保留人工审核流程，另行记录 AI 对原文、A/B 输出和 CHIA 标注的逐条复核。这里已揭示 A/B 系统身份，属于非盲法 AI 复核。类型和边界的数字是对既有金标准的脚本复算；文字解释是 AI 判断，不能当作真人或独立临床签核。

复核只使用冻结后的预测，没有改动模型、提示词、金标准或实验分数。原人工审核表的身份、时间和评分字段保持原状。

Markdown 展示统一换行并省略行尾空格；字符位置以 JSON 中保留的原始文本为准。

## 这 12 份样本的核对结果

| 系统 | 正确 TP | 误报 FP | 遗漏 FN | 精确率 | 召回率 | 精确片段 F1 | 完全匹配文档 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 旧版 LLM | 10 | 31 | 63 | 24.4% | 13.7% | 17.5% | 0/12 |
| 新版 LLM + NER | 37 | 114 | 36 | 24.5% | 50.7% | 33.0% | 1/12 |

这是预先抽取的 12 份复核子集，不能代替 [100 份文档的主结果](summary.md)。完全匹配要求整个实体集合一致，包含无目标实体的文档。空金标准与空预测的 F1 按评分实现记为 0，另用完全匹配标志表示该文档成功。所有保留片段均能回溯到原文，但原文匹配不等于语义正确。

主要问题：疾病/观察结果与 Measurement 混淆；数值、单位及时间窗截断；完整片段与短片段同时出现；Multiplier、Observation 等任务外标签被强制分配到三个目标类别。新版在 review-02、review-10 的精确 F1 低于旧版。否定、AND/OR、例外与患者资格没有得到验证。

[保留的真人审核表](human_review.md) · [未填写的人类评分记录](human_review_packet.json) · [机器可读 AI 二次复核](ai_second_review.json)

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 旧版 LLM | 0 / 1 / 14 | 0.0% | 否 |
| B | 新版 LLM + NER | 5 / 37 / 9 | 17.9% | 否 |

**AI 类型复核：** A把gastro-oesophageal中的子串age当成Measurement；虽然字符能在原文中找到，但不是独立实体。B补回两个重复时间窗和Child-Pugh score等实体，同时把多种疾病名称、单字母或缩写片段归入Measurement，误报很多。

**边界与遗漏：** B的> 6)多包含右括号；for 1 month prior to the enrollment in the trial比金标准多包含for；New York Heart Association等目标实体仍遗漏。

**上下文限制：** 这是一份排除标准。抽到疾病名或阈值并不等于已解析排除逻辑，不能据此生成患者入组结论。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 55:58 | "age" | 未匹配目标金标准 |

遗漏的目标实体：

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

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 42:60 | "gastro-oesophageal" | 未匹配目标金标准 |
| Measurement | 42:82 | "gastro-oesophageal reflux disease (GERD)" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 77:81 | "GERD" | 未匹配目标金标准 |
| Measurement | 91:111 | "chronic pancreatitis" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 113:127 | "cholelithiasis" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 129:148 | "fatty liver disease" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 150:159 | "hepatitis" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 161:179 | "cirrhosis of liver" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 304:328 | "irritable bowel syndrome" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 484:485 | "H" | 未匹配目标金标准 |
| Measurement | 554:563 | "infection" | 未匹配目标金标准 |
| Measurement | 628:646 | "malignant neoplasm" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 693:695 | "IV" | 与其他目标类型重叠 |
| Measurement | 696:718 | "cardiovascular disease" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 772:786 | "hypothyroidism" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 788:805 | "diabetes mellitus" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 807:829 | "chronic kidney disease" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 831:835 | "С3-5" | 同类型重叠，边界不匹配 |
| Measurement | 863:882 | "portal hypertension" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 897:911 | "decompensation" | 未匹配目标金标准 |
| Measurement | 913:929 | "Child-Pugh score" | 类型及完整边界匹配 |
| Temporal | 429:441 | "preparations" | 未匹配目标金标准 |
| Temporal | 442:481 | "less than 7 days prior to randomization" | 类型及完整边界匹配 |
| Temporal | 506:540 | "within 2 months before study entry" | 类型及完整边界匹配 |
| Temporal | 564:598 | "within 2 months before study entry" | 类型及完整边界匹配 |
| Temporal | 666:671 | "Prior" | 未匹配目标金标准 |
| Temporal | 1013:1020 | "prevent" | 未匹配目标金标准 |
| Temporal | 1377:1400 | "during the study period" | 类型及完整边界匹配 |
| Temporal | 1489:1501 | "over 2 units" | 与其他目标类型重叠 |
| Temporal | 1592:1613 | "concomitant treatment" | 未匹配目标金标准 |
| Temporal | 1615:1663 | "for 1 month prior to the enrollment in the trial" | 同类型重叠，边界不匹配 |
| Temporal | 1705:1752 | "within 3 months to the enrollment in this study" | 未匹配目标金标准 |
| Value | 442:451 | "less than" | 与其他目标类型重叠 |
| Value | 571:579 | "2 months" | 与其他目标类型重叠 |
| Value | 666:671 | "Prior" | 未匹配目标金标准 |
| Value | 693:695 | "IV" | 同类型重叠，边界不匹配 |
| Value | 807:814 | "chronic" | 未匹配目标金标准 |
| Value | 831:835 | "С3-5" | 同类型重叠，边界不匹配 |
| Value | 913:933 | "Child-Pugh score > 6" | 同类型重叠，边界不匹配；完整标注类型：Scope |
| Value | 930:934 | "> 6)" | 同类型重叠，边界不匹配 |
| Value | 1489:1501 | "over 2 units" | 同类型重叠，边界不匹配 |
| Value | 1581:1591 | "Prohibited" | 未匹配目标金标准 |

遗漏的目标实体：

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 旧版 LLM | 4 / 2 / 3 | 61.5% | 否 |
| B | 新版 LLM + NER | 4 / 3 / 3 | 57.1% | 否 |

**AI 类型复核：** A和B都保留HBsAg、HBeAg及serum viral load。B补出positive，但同时保留截断的serum viral，与完整实体重复。两组都把30 to 32 weeks标为Temporal；这条记录的金标准将其标为Value，gestation标为Measurement。

**边界与遗漏：** B的in 30 to 32 weeks边界多了in；B漏掉gestation，两组都漏掉above 8log10 copies per mL。这条样本中新组合的精确F1低于旧模型，不能只展示改善样例。

**上下文限制：** 孕周在本条语料中是测量值，不是相对事件时间窗；应依据上下文和已固定的任务标签判断。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 0:14 | "pregnant women" | 未匹配目标金标准 |
| Measurement | 36:45 | "gestation" | 类型及完整边界匹配 |
| Measurement | 61:66 | "HBsAg" | 类型及完整边界匹配 |
| Measurement | 71:76 | "HBeAg" | 类型及完整边界匹配 |
| Measurement | 77:93 | "serum viral load" | 类型及完整边界匹配 |
| Temporal | 18:32 | "30 to 32 weeks" | 与其他目标类型重叠；完整标注类型：Value |

遗漏的目标实体：

- Value [[18, 32]]: ["30 to 32 weeks"]
- Value [[52, 60]]: ["positive"]
- Value [[94, 120]]: ["above 8log10 copies per mL"]

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 61:66 | "HBsAg" | 类型及完整边界匹配 |
| Measurement | 71:76 | "HBeAg" | 类型及完整边界匹配 |
| Measurement | 77:88 | "serum viral" | 同类型重叠，边界不匹配 |
| Measurement | 77:93 | "serum viral load" | 类型及完整边界匹配 |
| Temporal | 18:32 | "30 to 32 weeks" | 与其他目标类型重叠；完整标注类型：Value |
| Value | 15:32 | "in 30 to 32 weeks" | 同类型重叠，边界不匹配 |
| Value | 52:60 | "positive" | 类型及完整边界匹配 |

遗漏的目标实体：

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 新版 LLM + NER | 1 / 4 / 2 | 25.0% | 否 |
| B | 旧版 LLM | 0 / 0 / 3 | 0.0% | 否 |

**AI 类型复核：** A找到完整的within the past year，但又输出较短的past，并把同一时间窗重复标为Value。B没有保留实体。

**边界与遗漏：** A把> 5 events per hour截成> 5；两组都未完整抽出apnea hypopnea index及其数值。renal function在这条记录的目标金标准中未标为Measurement，其临床合理性没有在本复核中裁定。

**上下文限制：** 时间窗、指数名称和单位构成不同信息；仅保留数字5会丢失每小时事件数的量纲。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 40:54 | "renal function" | 未匹配目标金标准 |
| Temporal | 141:161 | "within the past year" | 类型及完整边界匹配 |
| Temporal | 152:156 | "past" | 同类型重叠，边界不匹配 |
| Value | 141:161 | "within the past year" | 与其他目标类型重叠；完整标注类型：Temporal |
| Value | 184:187 | "> 5" | 同类型重叠，边界不匹配 |

遗漏的目标实体：

- Measurement [[163, 183]]: ["apnea hypopnea index"]
- Value [[184, 203]]: ["> 5 events per hour"]

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| — | — | 无保留输出 | — |

遗漏的目标实体：

- Temporal [[141, 161]]: ["within the past year"]
- Measurement [[163, 183]]: ["apnea hypopnea index"]
- Value [[184, 203]]: ["> 5 events per hour"]

## review-04 — NCT02901106_exc

```text
pregnant or breastfeeding woman
patient with a measure of legal protection
subject unaffiliated insurance
```

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 旧版 LLM | 0 / 3 / 0 | 0.0% | 否 |
| B | 新版 LLM + NER | 0 / 0 / 0 | 0.0% | 是 |

**AI 类型复核：** 金标准没有Measurement、Value、Temporal目标实体。B的空输出与本任务金标准完全一致。A将妊娠/哺乳状态、法律保护和保险相关描述当成Measurement，不符合本任务标签。

**边界与遗漏：** B没有本任务范围内的误报或漏报；这不表示这些资格条件不存在或不重要。

**上下文限制：** 本轮仅评估三个实体类别，不对法律条款或妊娠状态做资格判断。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 0:25 | "pregnant or breastfeeding" | 未匹配目标金标准 |
| Measurement | 41:75 | "with a measure of legal protection" | 未匹配目标金标准 |
| Measurement | 85:107 | "unaffiliated insurance" | 未匹配目标金标准 |

遗漏的目标实体：

- 无。

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| — | — | 无保留输出 | — |

遗漏的目标实体：

- 无。

## review-05 — NCT00396734_inc

```text
Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week
```

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 旧版 LLM | 0 / 3 / 0 | 0.0% | 否 |
| B | 新版 LLM + NER | 0 / 3 / 0 | 0.0% | 否 |

**AI 类型复核：** 两组都将用量或频次当成目标实体。核对完整.ann后，1g to 2g a day和1 to 3 times a week实际标为Multiplier，cocaine-dependent标为Condition，因此本任务的目标金标准为空。

**边界与遗漏：** B还产生明显未完成的片段between 1g to。两组在精确基准上都有3个误报；不能把金标准没有目标实体直接解释为原文没有数量信息。

**上下文限制：** 出现数字和时间单位并不足以决定Value或Temporal标签；药物用量/频次需要遵循语料类别范围。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 21:38 | "cocaine-dependent" | 未匹配目标金标准；完整标注类型：Condition |
| Value | 60:68 | "1g to 2g" | 未匹配目标金标准 |
| Temporal | 76:95 | "1 to 3 times a week" | 未匹配目标金标准；完整标注类型：Multiplier |

遗漏的目标实体：

- 无。

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Temporal | 76:95 | "1 to 3 times a week" | 未匹配目标金标准；完整标注类型：Multiplier |
| Value | 52:65 | "between 1g to" | 未匹配目标金标准 |
| Value | 52:74 | "between 1g to 2g a day" | 未匹配目标金标准 |

遗漏的目标实体：

- 无。

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 旧版 LLM | 2 / 5 / 10 | 21.1% | 否 |
| B | 新版 LLM + NER | 8 / 24 / 4 | 36.4% | 否 |

**AI 类型复核：** B补回多个完整时间窗，召回显著高于A，但把疾病名、Live、Investigational、whichever和IV等片段误当Measurement，并输出多余的active等标签。

**边界与遗漏：** 两组输出30 days or 5 half-lives off drug，未对应金标准中的不连续30 days | off drug及另一条5 half-lives off drug。B仍漏掉while receiving trial medication和12 months off drug等完整时间片段。

**上下文限制：** 原文含whichever is longer以及多个不同排除条件。当前连续片段抽取不能表示取较长值的逻辑；不能把已复制的文本视为完整规则。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 87:94 | "nursing" | 未匹配目标金标准；完整标注类型：Condition |
| Value | 62:69 | "Grade 3" | 未匹配目标金标准；完整标注类型：Qualifier |
| Value | 269:301 | "while receiving trial medication" | 与其他目标类型重叠；完整标注类型：Temporal |
| Temporal | 647:663 | "30 days off drug" | 类型及完整边界匹配 |
| Temporal | 687:704 | "3 months off drug" | 类型及完整边界匹配 |
| Temporal | 738:770 | "30 days or 5 half-lives off drug" | 同类型重叠，边界不匹配；完整标注类型：Scope |
| Temporal | 1577:1592 | "within 2 months" | 同类型重叠，边界不匹配 |

遗漏的目标实体：

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

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 14:26 | "sacroiliitis" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 49:61 | "sacroiliitis" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 668:672 | "Live" | 未匹配目标金标准 |
| Measurement | 709:724 | "Investigational" | 未匹配目标金标准 |
| Measurement | 772:781 | "whichever" | 未匹配目标金标准 |
| Measurement | 1545:1547 | "IV" | 未匹配目标金标准 |
| Measurement | 1712:1740 | "human immunodeficiency virus" | 未匹配目标金标准 |
| Measurement | 1712:1745 | "human immunodeficiency virus (HIV" | 未匹配目标金标准 |
| Measurement | 1750:1762 | "seropositive" | 未匹配目标金标准 |
| Measurement | 1786:1789 | "HCV" | 未匹配目标金标准 |
| Measurement | 1786:1790 | "HCV)" | 未匹配目标金标准 |
| Temporal | 145:166 | "within 6 months after" | 同类型重叠，边界不匹配 |
| Temporal | 145:193 | "within 6 months after receiving trial medication" | 类型及完整边界匹配 |
| Temporal | 305:343 | "within 6 months after trial medication" | 类型及完整边界匹配 |
| Temporal | 647:663 | "30 days off drug" | 类型及完整边界匹配 |
| Temporal | 687:704 | "3 months off drug" | 类型及完整边界匹配 |
| Temporal | 738:770 | "30 days or 5 half-lives off drug" | 同类型重叠，边界不匹配；完整标注类型：Scope |
| Temporal | 932:938 | "active" | 未匹配目标金标准；完整标注类型：Qualifier |
| Temporal | 1061:1067 | "active" | 未匹配目标金标准 |
| Temporal | 1080:1086 | "active" | 未匹配目标金标准 |
| Temporal | 1119:1125 | "active" | 未匹配目标金标准；完整标注类型：Qualifier |
| Temporal | 1150:1168 | "prior to Screening" | 类型及完整边界匹配 |
| Temporal | 1242:1276 | "within 6 months prior to Screening" | 类型及完整边界匹配 |
| Temporal | 1577:1610 | "within 2 months prior to Baseline" | 类型及完整边界匹配 |
| Temporal | 1633:1640 | "ongoing" | 类型及完整边界匹配 |
| Temporal | 1653:1662 | "recurrent" | 未匹配目标金标准；完整标注类型：Qualifier |
| Temporal | 1763:1766 | "for" | 未匹配目标金标准 |
| Value | 27:34 | "Grade 2" | 未匹配目标金标准；完整标注类型：Qualifier |
| Value | 62:69 | "Grade 3" | 未匹配目标金标准；完整标注类型：Qualifier |
| Value | 73:80 | "Grade 4" | 未匹配目标金标准；完整标注类型：Qualifier |
| Value | 839:841 | "12" | 与其他目标类型重叠 |
| Value | 1754:1762 | "positive" | 未匹配目标金标准 |

遗漏的目标实体：

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 新版 LLM + NER | 1 / 5 / 1 | 25.0% | 否 |
| B | 旧版 LLM | 0 / 2 / 2 | 0.0% | 否 |

**AI 类型复核：** A正确保留Current，但把Current or recent整体作为Temporal，同时把整条感染描述、实验室异常和Pregnancy当成Value。B把infection和laboratory abnormalities当成Measurement。

**边界与遗漏：** 金标准分别标Current与recent；A漏掉独立的recent，B两者都漏掉。Clinically significant也不是这条记录的Temporal金标准。

**上下文限制：** 状态修饰词与其修饰的疾病/妊娠条件需要区分，不能用整条criterion替代实体。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Temporal | 0:7 | "Current" | 类型及完整边界匹配 |
| Temporal | 0:17 | "Current or recent" | 同类型重叠，边界不匹配；完整标注类型：Scope |
| Temporal | 29:51 | "Clinically significant" | 未匹配目标金标准；完整标注类型：Qualifier |
| Value | 0:27 | "Current or recent infection" | 与其他目标类型重叠 |
| Value | 29:76 | "Clinically significant laboratory abnormalities" | 未匹配目标金标准 |
| Value | 78:87 | "Pregnancy" | 未匹配目标金标准；完整标注类型：Condition |

遗漏的目标实体：

- Temporal [[11, 17]]: ["recent"]

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 18:27 | "infection" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 52:76 | "laboratory abnormalities" | 未匹配目标金标准；完整标注类型：Condition |

遗漏的目标实体：

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 新版 LLM + NER | 7 / 24 / 12 | 28.0% | 否 |
| B | 旧版 LLM | 0 / 6 / 19 | 0.0% | 否 |

**AI 类型复核：** A恢复了多个重复的at Screening、完整年龄范围及<=0.70；B把年龄范围拆成>=40与<=80，且没有任何完整目标匹配。A仍产生age、NHANES、reference等不匹配Measurement。

**边界与遗漏：** A把长肺功能测量名称截断；>=50 and <=70% of predicted normal缺少values；for at least 6 months prior to Visit 1漏for；score 2 or higher漏score。缩写和长复合实体仍是难点。

**上下文限制：** 原文同时有年龄、吸烟暴露、肺功能、给药步骤及临床评分。分段改善了覆盖，但没有可靠区分所有测量、剂量和时间描述。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 478:481 | "age" | 未匹配目标金标准；完整标注类型：Person |
| Measurement | 802:831 | "forced expiratory volume in 1" | 同类型重叠，边界不匹配 |
| Measurement | 847:868 | "forced vital capacity" | 同类型重叠，边界不匹配 |
| Measurement | 1029:1035 | "NHANES" | 未匹配目标金标准 |
| Measurement | 1040:1049 | "reference" | 未匹配目标金标准 |
| Measurement | 1255:1267 | "total 400mcg" | 未匹配目标金标准 |
| Measurement | 1361:1369 | "FEV1/FVC" | 未匹配目标金标准 |
| Measurement | 1380:1392 | "FEV1 percent" | 未匹配目标金标准 |
| Temporal | 338:340 | "at" | 未匹配目标金标准 |
| Temporal | 482:494 | "at Screening" | 类型及完整边界匹配 |
| Temporal | 482:496 | "at Screening (" | 同类型重叠，边界不匹配 |
| Temporal | 536:543 | "current" | 类型及完整边界匹配 |
| Temporal | 547:563 | "prior history of" | 同类型重叠，边界不匹配 |
| Temporal | 601:615 | "at screening (" | 同类型重叠，边界不匹配 |
| Temporal | 625:633 | "Previous" | 未匹配目标金标准 |
| Temporal | 688:691 | "for" | 同类型重叠，边界不匹配 |
| Temporal | 692:726 | "at least 6 months prior to Visit 1" | 同类型重叠，边界不匹配 |
| Temporal | 710:726 | "prior to Visit 1" | 同类型重叠，边界不匹配 |
| Temporal | 889:901 | "at Screening" | 类型及完整边界匹配 |
| Temporal | 1095:1107 | "at Screening" | 类型及完整边界匹配 |
| Temporal | 1194:1203 | "after the" | 同类型重叠，边界不匹配 |
| Temporal | 1585:1596 | ">= 40 years" | 与其他目标类型重叠；完整标注类型：Value |
| Value | 140:144 | "Male" | 未匹配目标金标准；完整标注类型：Person |
| Value | 180:195 | "post-menopausal" | 未匹配目标金标准 |
| Value | 455:474 | ">=40 and <=80 years" | 类型及完整边界匹配 |
| Value | 564:579 | ">=10 pack-years" | 未匹配目标金标准；完整标注类型：Multiplier |
| Value | 882:888 | "<=0.70" | 类型及完整边界匹配 |
| Value | 970:1004 | ">=50 and <=70% of predicted normal" | 同类型重叠，边界不匹配 |
| Value | 1183:1185 | "15" | 与其他目标类型重叠 |
| Value | 1469:1480 | "2 or higher" | 同类型重叠，边界不匹配 |
| Value | 1585:1596 | ">= 40 years" | 类型及完整边界匹配 |

遗漏的目标实体：

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

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 450:453 | "Age" | 未匹配目标金标准；完整标注类型：Person |
| Measurement | 1361:1375 | "FEV1/FVC ratio" | 未匹配目标金标准 |
| Measurement | 1380:1409 | "FEV1 percent predicted values" | 未匹配目标金标准 |
| Value | 455:459 | ">=40" | 同类型重叠，边界不匹配 |
| Value | 464:468 | "<=80" | 同类型重叠，边界不匹配 |
| Value | 970:984 | ">=50 and <=70%" | 同类型重叠，边界不匹配 |

遗漏的目标实体：

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 旧版 LLM | 0 / 0 / 7 | 0.0% | 否 |
| B | 新版 LLM + NER | 5 / 2 / 2 | 71.4% | 否 |

**AI 类型复核：** B正确抽取hemoglobin、<8 g/dl和三个Temporal位置，比A的空输出覆盖更多。B把Human immunodeficiency virus当成Measurement，并把abnormal liver作为Value。

**边界与遗漏：** 正确边界应分为Value abnormal及Measurement liver enzymes，B两者都未精确完成。

**上下文限制：** current、Previous和Current大小写及各自位置均需保留；疾病名称出现本身不能证明它是测量名称。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| — | — | 无保留输出 | — |

遗漏的目标实体：

- Measurement [[119, 132]]: ["liver enzymes"]
- Value [[110, 118]]: ["abnormal"]
- Measurement [[143, 153]]: ["hemoglobin"]
- Value [[154, 161]]: ["<8 g/dl"]
- Temporal [[176, 183]]: ["current"]
- Temporal [[195, 203]]: ["Previous"]
- Temporal [[318, 325]]: ["Current"]

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 143:153 | "hemoglobin" | 类型及完整边界匹配 |
| Measurement | 254:282 | "Human immunodeficiency virus" | 未匹配目标金标准 |
| Temporal | 176:183 | "current" | 类型及完整边界匹配 |
| Temporal | 195:203 | "Previous" | 类型及完整边界匹配 |
| Temporal | 318:325 | "Current" | 类型及完整边界匹配 |
| Value | 110:124 | "abnormal liver" | 同类型重叠，边界不匹配 |
| Value | 154:161 | "<8 g/dl" | 类型及完整边界匹配 |

遗漏的目标实体：

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 新版 LLM + NER | 2 / 4 / 2 | 40.0% | 否 |
| B | 旧版 LLM | 3 / 5 / 1 | 50.0% | 否 |

**AI 类型复核：** A和B都保留Height及>40 Kg/ mm；A把身高阈值拆成< 4'和11"，时间窗也截断。B完整保留时间窗，但多抽了疾病和整条排除条件。

**边界与遗漏：** 应保留完整< 4' 11"及in the 24 hours prior to cesarean delivery。BMI在这条.ann中明确为Observation，不能因为它通常是测量指标就修改本次金标准。

**上下文限制：** 原文BMI单位写作Kg/ mm；本任务必须原样保留并标出可疑源文本，不能默默改成更常见单位。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 23:29 | "Height" | 类型及完整边界匹配 |
| Measurement | 40:43 | "BMI" | 未匹配目标金标准；完整标注类型：Observation |
| Temporal | 76:109 | "in the 24 hours prior to cesarean" | 同类型重叠，边界不匹配 |
| Value | 30:34 | "< 4'" | 同类型重叠，边界不匹配 |
| Value | 35:38 | "11\"" | 同类型重叠，边界不匹配 |
| Value | 44:54 | ">40 Kg/ mm" | 类型及完整边界匹配 |

遗漏的目标实体：

- Value [[30, 38]]: ["< 4' 11\""]
- Temporal [[76, 118]]: ["in the 24 hours prior to cesarean delivery"]

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 23:29 | "Height" | 类型及完整边界匹配 |
| Measurement | 40:43 | "BMI" | 未匹配目标金标准；完整标注类型：Observation |
| Measurement | 121:155 | "Hypertensive diseases of pregnancy" | 未匹配目标金标准；完整标注类型：Condition |
| Measurement | 157:214 | "Chronic hypertension receiving antihypertensive treatment" | 未匹配目标金标准 |
| Measurement | 216:329 | "Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection" | 未匹配目标金标准 |
| Value | 44:54 | ">40 Kg/ mm" | 类型及完整边界匹配 |
| Value | 178:214 | "receiving antihypertensive treatment" | 未匹配目标金标准 |
| Temporal | 76:118 | "in the 24 hours prior to cesarean delivery" | 类型及完整边界匹配 |

遗漏的目标实体：

- Value [[30, 38]]: ["< 4' 11\""]

## review-11 — NCT02621541_inc

```text
suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI
signed informed consent
```

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 新版 LLM + NER | 0 / 1 / 0 | 0.0% | 否 |
| B | 旧版 LLM | 0 / 3 / 0 | 0.0% | 否 |

**AI 类型复核：** 完整标注中nonfunctional P-NET和hypervascularity属于Condition，CT/MRI属于Procedure，signed informed consent属于Informed_consent，因此三个目标类别的金标准为空。A把hypervascularity当Measurement；B将疾病/影像征象和知情同意混入Measurement、Value、Temporal。

**边界与遗漏：** A有1个、B有3个基准误报。签署同意书的动作不是此处的Temporal实体。

**上下文限制：** 必须区分本次三个目标标签与完整临床信息，不应把所有医学概念强制分配到这三类。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 52:68 | "hypervascularity" | 未匹配目标金标准；完整标注类型：Condition |

遗漏的目标实体：

- 无。

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 27:32 | "P-NET" | 未匹配目标金标准 |
| Value | 52:68 | "hypervascularity" | 未匹配目标金标准；完整标注类型：Condition |
| Temporal | 78:101 | "signed informed consent" | 未匹配目标金标准；完整标注类型：Informed_consent |

遗漏的目标实体：

- 无。

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

| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |
|---|---|---|---:|---|
| A | 新版 LLM + NER | 4 / 7 / 1 | 50.0% | 否 |
| B | 旧版 LLM | 1 / 1 / 4 | 28.6% | 否 |

**AI 类型复核：** A补出完整liver aminotransferase concentrations、>5 times the upper limit of normal、Previous和at the time of enrollment，但也保留不完整短版本及无关组织名称。B只精确抽到at the time of enrollment。

**边界与遗漏：** A漏掉Currently，并把Human Research Protection误当Measurement；Active、Acute、at、for不匹配此处的Temporal金标准。

**上下文限制：** 原文同时规定入组时的囚犯排除与入组后的例外，并有not including用药范围。当前输出没有解析这些否定/例外，不能据片段推断患者资格。

### A 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 96:118 | "liver aminotransferase" | 同类型重叠，边界不匹配 |
| Measurement | 96:133 | "liver aminotransferase concentrations" | 类型及完整边界匹配 |
| Measurement | 605:630 | "Human Research Protection" | 未匹配目标金标准 |
| Temporal | 0:6 | "Active" | 未匹配目标金标准；完整标注类型：Qualifier |
| Temporal | 76:81 | "Acute" | 未匹配目标金标准 |
| Temporal | 221:223 | "at" | 未匹配目标金标准 |
| Temporal | 438:446 | "Previous" | 类型及完整边界匹配 |
| Temporal | 632:657 | "at the time of enrollment" | 类型及完整边界匹配 |
| Temporal | 675:678 | "for" | 未匹配目标金标准 |
| Value | 134:142 | ">5 times" | 同类型重叠，边界不匹配 |
| Value | 134:168 | ">5 times the upper limit of normal" | 类型及完整边界匹配 |

遗漏的目标实体：

- Temporal [[314, 323]]: ["Currently"]

### B 逐片段核对

| 类型 | 字符位置 | 原文片段 | 金标准匹配 |
|---|---|---|---|
| Measurement | 355:373 | "alcohol dependence" | 未匹配目标金标准；完整标注类型：Condition |
| Temporal | 632:657 | "at the time of enrollment" | 类型及完整边界匹配 |

遗漏的目标实体：

- Measurement [[96, 133]]: ["liver aminotransferase concentrations"]
- Value [[134, 168]]: [">5 times the upper limit of normal"]
- Temporal [[314, 323]]: ["Currently"]
- Temporal [[438, 446]]: ["Previous"]

## 后续改进顺序（尚未运行）

1. 在开发集补充标签排除规则与困难反例，区分 Person、Condition、Observation、Multiplier 与三个目标标签，避免见到医学词或数字就强制分类。保留语料差异记录，不事后改测试金标准。
2. 以同一开发集上的 NER 为基线，比较候选重排、按类型筛选和边界校正，检验 LLM 是否有独立增益。当前直接取并集增加了误报，不能因召回提高就默认采用。
3. 在开发集验证完整单位/运算符边界、重复短片段去重及词内子串拒绝；另测受约束的 JSON 输出和更合理的生成预算。规则需检查缩写与标点反例，不能只针对这 12 份样本修补。
4. 将否定、条件关系、时间比较与例外作为单独标注和评估的任务。完成开发后再冻结方案，用新的未使用样本评估，另行记录真实人工审核。

## 范围与来源

标签冲突依据原始 CHIA 标注记录，不把与语料不一致直接解释为临床事实错误。可能的标注不一致和可疑源单位保持原样，不在复核后修改测试答案。下一轮开发需要新的冻结方案与评估样本。

原文和金标准来自 Kury et al., CHIA v2，CC BY 4.0：[论文](https://doi.org/10.1038/s41597-020-00620-0) · [数据](https://doi.org/10.6084/m9.figshare.11855817.v2)。AI 解释、模型预测和本复核表为派生成果。
