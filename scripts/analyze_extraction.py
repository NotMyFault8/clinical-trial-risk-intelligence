"""Post-freeze error analysis; does not change prompts, predictions or gold."""
from collections import Counter
import hashlib,json,re,zipfile
from clinical_trial_risk.data.cohort import ROOT
from clinical_trial_risk.llm.benchmark import score

report=json.loads((ROOT/'reports/extraction/test.json').read_text())
records=[d for d in json.loads((ROOT/'data/annotations/chia/benchmark.json').read_text()) if d['split']=='test']
cache={}
for p in (ROOT/'artifacts/extraction_cache').glob('*.json'):
    d=json.loads(p.read_text())
    if d['version']==report['version']:cache[d['input_sha256']]=d
outputs=[cache[hashlib.sha256(d['text'].encode()).hexdigest()] for d in records]
strata={}
for field in ['length','negation','section']:
    groups={}
    for i,r in enumerate(records):
        if field=='length':key='short_<500' if len(r['text'])<500 else 'medium_500_999' if len(r['text'])<1000 else 'long_1000plus'
        elif field=='negation':key='negation_terms' if re.search(r'\b(no|not|without|except|unless)\b',r['text'],re.I) else 'no_negation_terms'
        else:key=r['record_id'].split('_')[-1]
        groups.setdefault(key,[]).append(i)
    strata[field]={k:score([records[i] for i in v],[outputs[i] for i in v])[0] for k,v in groups.items()}
errors=json.loads((ROOT/'reports/extraction/test_errors.json').read_text());patterns=Counter()
for e in errors:
    for kind,spans in e['false_positive']:
        same=False;different=False
        for gold_kind,gold_spans in e['false_negative']:
            overlap=any(max(a,c)<min(b,d) for a,b in spans for c,d in gold_spans)
            same|=overlap and kind==gold_kind;different|=overlap and kind!=gold_kind
        patterns['boundary_overlap' if same else 'type_overlap' if different else 'unmatched_prediction']+=1
for out in outputs:
    patterns['invalid_schema_records']+=not out['schema_valid']
    for r in out['rejected']:patterns[r['reason']]+=1
z=zipfile.ZipFile(ROOT/'data/annotations/chia/chia_with_scope.zip');integrity=Counter();selected_invalid=[]
selected={r['record_id'] for r in records}
for name in z.namelist():
    if not name.endswith('.txt'):continue
    text=z.read(name).decode()
    for line in z.read(name[:-4]+'.ann').decode().splitlines():
        if not line.startswith('T'):continue
        parts=line.split('\t');kind,pos=parts[1].split(' ',1)
        spans=[list(map(int,p.split())) for p in pos.split(';')]
        actual=' '.join(text[a:b] for a,b in spans);claimed=parts[2] if len(parts)>2 else ''
        integrity['all_entities']+=1;integrity['text_matches_offsets']+=actual==claimed
        if actual!=claimed:
            integrity['mismatched_entities']+=1
            if name[:-4] in selected and kind in ['Measurement','Value','Temporal']:
                selected_invalid.append({'record_id':name[:-4],'entity_id':parts[0],'kind':kind})
out={'strata':strata,'error_pattern_counts':dict(patterns),'annotation_integrity':dict(integrity),
    'test_target_annotation_mismatches':selected_invalid,
    'interpretation':'Post-test descriptive analysis; no prompts, models or gold changed. Offset mismatches are disclosed; exact scoring retained published offsets.'}
(ROOT/'reports/extraction/error_analysis.json').write_text(json.dumps(out,indent=2)+'\n')
gate=json.loads((ROOT/'configs/extraction_release.json').read_text());m=report['llm']
checks={'schema':m['schema_valid_rate']>=gate['test_min_schema_valid_rate'],
        'precision':m['micro']['precision']>=gate['test_min_micro_precision'],
        'f1':m['micro']['f1']>=gate['test_min_micro_f1'],
        'human_semantic_review':gate['target_cohort_human_semantic_review_completed']}
(ROOT/'reports/extraction/release_decision.json').write_text(json.dumps({'checks':checks,'released':all(checks.values()),
    'decision':'Withhold semantic extraction release; retain as an explicitly experimental research component.'},indent=2)+'\n')
print(dict(patterns),dict(integrity),'test target mismatches',len(selected_invalid))
