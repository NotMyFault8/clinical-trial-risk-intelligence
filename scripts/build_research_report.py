"""Build a reviewable report and figures solely from saved measured results."""
import json,re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from clinical_trial_risk.data.cohort import ROOT
from clinical_trial_risk.models.train import FAMILIES

ev=json.loads((ROOT/'reports/evaluation/holdout.json').read_text())
co=json.loads((ROOT/'reports/cohort/audit.json').read_text())
ex=json.loads((ROOT/'reports/extraction/test.json').read_text())
gen=json.loads((ROOT/'reports/generation/evaluation.json').read_text())
fig=ROOT/'reports/figures';fig.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
names={'structured_logistic':'Structured logistic','structured_counts':'+ Simple counts',
       'structured_tfidf':'+ TF-IDF','structured_boosting':'Structured XGBoost',
       'structured_embeddings':'+ Frozen embeddings','structured_llm':'+ Experimental LLM spans'}
values=[ev['models'][f]['platt']['average_precision'] for f in FAMILIES]
cis=[ev['uncertainty']['intervals'][f]['average_precision'] for f in FAMILIES]
figure,ax=plt.subplots(figsize=(8,4.2))
for i,(v,(lo,hi)) in enumerate(zip(values,cis)):
    ax.plot([lo,hi],[i,i],color='#769c96',linewidth=3)
    ax.scatter([v],[i],color='#126b62',s=45,zorder=3)
ax.axvline(ev['no_skill_reference']['AP'],linestyle='--',color='#b2772a',label='Test prevalence')
ax.set_yticks(range(len(names)),[names[f] for f in FAMILIES]);ax.invert_yaxis();ax.set_xlabel('Average precision · sponsor-cluster 95% interval')
ax.set_title('Frozen 2021 resolved-outcome holdout');ax.text(ev['no_skill_reference']['AP']+.006,2.5,'Test prevalence',rotation=90,va='center',color='#b2772a');figure.tight_layout();figure.savefig(fig/'model_comparison.png');plt.close(figure)
selected=ev['selected_using_validation'];cal=ev['models'][selected]['platt']['calibration_bins']
figure,ax=plt.subplots(figsize=(5.4,4.5));ax.plot([0,1],[0,1],'--',color='#a3aaa8')
ax.plot([b['mean_prediction'] for b in cal],[b['observed_rate'] for b in cal],'-o',color='#126b62')
for b in cal:ax.annotate(str(b['n']),(b['mean_prediction'],b['observed_rate']),xytext=(4,5),textcoords='offset points',fontsize=8)
ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean Platt-calibrated prediction',ylabel='Observed termination fraction',title='Calibration · labels show bin sample size')
figure.tight_layout();figure.savefig(fig/'calibration.png');plt.close(figure)
years=[];completed=[];terminated=[];other=[]
for snapshot,a in co['snapshots'].items():
    years.append(snapshot[:4]);s=a['primary_status_counts'];completed.append(s.get('completed',0));terminated.append(s.get('terminated',0));other.append(a['primary_trials']-completed[-1]-terminated[-1])
figure,ax=plt.subplots(figsize=(7,4.4));ax.bar(years,completed,label='Completed',color='#4c9285');ax.bar(years,terminated,bottom=completed,label='Terminated',color='#bf7c43');ax.bar(years,other,bottom=np.array(completed)+terminated,label='Other / unresolved / missing',color='#b7c4c0');ax.set(ylabel='Eligible baseline trials',title='Five-year status selection');ax.set_ylim(0,1850);ax.legend(fontsize=8,ncol=3,loc='upper center',frameon=False);figure.tight_layout();figure.savefig(fig/'outcome_selection.png');plt.close(figure)

def f(v):return 'undefined' if v is None else f'{v:.3f}'
def ci(v):return f"[{v[0]:.3f}, {v[1]:.3f}]"
lines=['# Clinical trial early-termination research report',
       '**Implemented local research demonstrator. Experimental extraction and free-form generation are withheld from semantic release.**',
       '## Research question and estimand',
       'Can historical baseline metadata and eligibility text distinguish trials reported Terminated versus Completed at a five-year snapshot? The answer applies only to the resolved, annual-landmark sample. It is not an estimate of termination probability for all newly starting trials.',
       'Baseline sources are September 2018–2021 AACT archives; matched outcome sources are September 2023–2026. The conservative 90-day start-interval rule gives 5,703 unique trials. Most do not enter the binary comparison. No later record repairs baseline features.',
       '| Baseline | Eligible | Completed | Terminated | Other / unresolved |',
       '|---|---:|---:|---:|---:|']
for i,y in enumerate(years):lines.append(f'| {y} | {completed[i]+terminated[i]+other[i]:,} | {completed[i]:,} | {terminated[i]:,} | {other[i]:,} |')
lines+=['![Outcome selection](figures/outcome_selection.png)',
        'Selection is material: the model is conditioned on observing one of two reported statuses. Other statuses are not negative labels. Five years of follow-up does not solve registry reporting delay or selection bias. See the saved selection audit for differences in sponsor class, phase, enrollment and missingness.',
        '## Locked evaluation',
        'Training: 2018–2019, 1,107 trials / 217 terminations. Tuning: 2020 sponsor-hash partition, 332 / 47. Calibration: disjoint 2020 sponsor groups, 341 / 69. Final holdout: 2021, 632 / 116. Preprocessing fits on training only. Four candidate settings per model family; Platt calibration uses its separate partition.',
        '**Retrospective temporal generalization, not historically deployable pseudo-prospective validation.** Training outcome labels from 2023–2024 were unavailable at the 2021 prediction landmark. Pretrained models were also not historically available, and their training contamination cannot be excluded. No actual prospective or clinical validation is claimed.',
        'The primary comparison was TF-IDF versus structured logistic regression on average precision. Other families and sensitivities are secondary. Confidence intervals resample test lead-sponsor clusters and condition on the fitted models; they do not include training-set uncertainty.',
        '## Holdout measurements',
        '| Model | AP (95% interval) | ROC-AUC | Brier | Precision@10% | Recall@10% |',
        '|---|---:|---:|---:|---:|---:|']
for family in FAMILIES:
    m=ev['models'][family]['platt'];interval=ev['uncertainty']['intervals'][family]['average_precision'];top=m['top_k']['0.1']
    lines.append(f"| {names[family]} | {f(m['average_precision'])} {ci(interval)} | {f(m['roc_auc'])} | {f(m['brier'])} | {f(top['precision'])} | {f(top['recall'])} |")
delta=ev['uncertainty']['differences_from_structured_logistic']['structured_tfidf']['average_precision']
lines+=[f"No-skill AP reference is test prevalence, {f(ev['no_skill_reference']['AP'])}. Primary paired AP difference (TF-IDF minus structured): **{f(delta['difference'])}, 95% interval {ci(delta['ci95'])}**.",
        ('The interval includes zero; this experiment does not establish a reliable incremental AP gain from TF-IDF.' if delta['ci95'][0]<=0<=delta['ci95'][1] else 'The interval excludes zero under the stated conditional test-sample bootstrap. This does not establish clinical usefulness, causality or prospective performance.'),
        '![Model comparison](figures/model_comparison.png)',
        f"The local demonstrator uses **{names[selected]}**, chosen using the frozen tuning scores among qualified components. It was not chosen by maximizing holdout performance. Failed-gate LLM features remain research-only.",
        '## Calibration and prioritization',
        '![Calibration](figures/calibration.png)',
        '| Probability mapping | Brier | Ten-bin ECE | Balanced accuracy at 0.5 | F1 at 0.5 |',
        '|---|---:|---:|---:|---:|']
for mode in ['raw','platt','isotonic']:
    m=ev['models'][selected][mode];lines.append(f"| {mode} | {f(m['brier'])} | {f(m['ece_10_bins'])} | {f(m['balanced_accuracy'])} | {f(m['f1'])} |")
lines+=['Platt was prespecified for the primary scores. Isotonic is a diagnostic comparison, not a post-test replacement. Sparse calibration bins have unstable observed rates; passing one finite evaluation does not establish reliable probabilities for a new population.',
        '| Review fraction | Trials reviewed | Terminations captured | Recall | Precision | Lift |','|---|---:|---:|---:|---:|---:|']
for frac,m in ev['models'][selected]['platt']['top_k'].items():lines.append(f"| {float(frac):.0%} | {m['reviewed']} | {m['captured']} | {f(m['recall'])} | {f(m['precision'])} | {f(m['lift'])} |")
lines+=['These are retrospective prioritization counts, not demonstrated business savings or effective interventions.',
        '## Sensitivity, subgroup and drift evidence',
        '| Secondary setting | Structured AP | TF-IDF AP |','|---|---:|---:|']
for name,s in ev['sensitivities'].items():lines.append(f"| {name} | {f(s['structured_logistic']['average_precision'])} | {f(s['structured_tfidf']['average_precision'])} |")
lines+=[f"Near-duplicate filtering removes {ev['drift']['near_duplicate_test_count']} test texts with hashed character-gram cosine similarity >=0.9 to training. There are {ev['drift']['train_test_sponsor_overlap']} lead sponsors shared across training and test; this is future-cohort transfer, not unseen-sponsor validation.",
        'Subgroup results are saved by phase, sponsor class, coarse therapeutic area and US site listing. Metrics are withheld for groups with fewer than 30 trials or fewer than five examples of either class. Keyword therapeutic areas are imperfect and sparse subgroup results should not be used to rank clinical populations. Drift measurements describe changes; they do not prove their causes.',
        '## LLM extraction: negative release result',
        f"The independent published CHIA annotations provide {ex['llm']['trials']} test trials / {ex['llm']['records']} inclusion/exclusion documents. This is an external Phase-IV benchmark, not new annotations from this project. Exact entity-type/offset micro F1: LLM **{f(ex['llm']['micro']['f1'])}**, rules **{f(ex['rules']['micro']['f1'])}**. LLM precision {f(ex['llm']['micro']['precision'])}; recall {f(ex['llm']['micro']['recall'])}; valid schema {ex['llm']['schema_valid_rate']:.1%}.",
        'The extractor failed its pre-test release thresholds. Exact copied text is not proof of correct clinical typing or logic. Discontinuous spans, negation scope, semantic relations and normalized operator/unit accuracy are not solved. One test target annotation has a source-text/offset discrepancy; published offsets were retained and the discrepancy disclosed. The corpus-wide check found 21 such discrepancies among 48,870 annotated entities.',
        f"The final extractor uses pinned Qwen2.5-1.5B-Instruct weights, 4-bit local inference, an 1,800-character prefix and at most six spans of each type. {ex['llm']['gold_spans_outside_prefix']} gold spans lie beyond the prefix. Published development pilots include a larger model that was slower and worse under this setup. Neither model was fine-tuned.",
        'The same 2,412 primary resolved trials enter the exploratory LLM-feature risk comparison. Invalid outputs remain explicit failure flags; trials are never silently dropped. Any incremental discrimination cannot turn an inaccurate extractor into validated clinical understanding. No human adjudication of target-cohort extractions has been performed.',
        '## Generated reports',
        f"On {gen['n']} frozen report cases, valid JSON rate was {gen['schema_valid_rate']:.1%}. " +
        (f"Risk-value mismatches: {gen['risk_value_mismatches_among_schema_valid']} among {gen['schema_valid_denominator']} schema-valid outputs; exact citation support {f(gen['exact_citation_support_rate'])} over {gen['citation_denominator']} citations. " if gen['schema_valid_denominator'] else 'All generated reports failed the structured-output contract, so numeric/citation fidelity among accepted reports is not estimable. Zero accepted reports must not be interpreted as zero fabrication risk. ') +
        f"All automated checks passed for {gen['automated_all_checks_pass_rate']:.1%} of cases. Deterministic templates reproduced the typed risk display in {gen['template_risk_match_rate']:.1%} of cases.",
        'Free-form generation is withheld. Automated numeric/source checks are not an independent semantic-faithfulness or analyst-usefulness evaluation. A blinded review form and rubric are prepared but uncompleted. No claim that generated prose improves usefulness is supported. The default served report is deterministic and includes verified additive model associations and source citations.',
        f"Measured generation amortized p50/p95 latency: {gen['generated_amortized_seconds_p50']:.3f}/{gen['generated_amortized_seconds_p95']:.3f} seconds per report in batches. Template p50 formatting latency: {gen['template_seconds_p50']:.6f} seconds, excluding packet/model computation. Hosted API charges: zero; local energy cost was not measured.",
        '## Engineering evidence and remaining gates',
        'The implementation includes streamed archive ingestion, pre-join SQL aggregation, source checksums, physically separate outcomes, explicit feature allowlists, temporal evaluation, model/prompt/source registries, a local read-only FastAPI dashboard, container packaging, unit/integration checks and descriptive monitoring. API requests never query the live registry or mutate trial records.',
        'The local demonstrator is suitable for research inspection and learning. It is not a production clinical system. Full project release remains gated on independent target-domain extraction/report review, demonstrated analyst usefulness and genuinely prospective evaluation where required. Negative component results are retained rather than relabeled as successful deployment.',
        'Reproduce with [the runbook](../docs/reproducibility.md). See [the locked protocol](../docs/research_protocol.md), [feature dictionary](../docs/feature_dictionary.md), [annotation manual](../docs/annotation_manual.md), and raw JSON result tables under this reports directory.',
        '## Sources',
        '- [AACT historical flat-file catalog](https://aact.ctti-clinicaltrials.org/snapshots) — selected archive URLs and hashes are in configs/snapshots.json.',
        '- [CHIA paper](https://doi.org/10.1038/s41597-020-00620-0) and [versioned annotations](https://doi.org/10.6084/m9.figshare.11855817.v2), CC BY 4.0.',
        '- [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) and [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). Pinned revisions and undocumented training-cutoff limits are recorded.']
document='\n\n'.join(lines)+'\n'
document=re.sub(r'(?m)(^\|[^\n]*\|)\n\n(?=\|)',r'\1\n',document)
(ROOT/'reports/research_report.md').write_text(document)
print('Research report and three figures generated.')
