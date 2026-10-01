"""External human-annotated span benchmark; whole related trials share a split."""
import argparse
from collections import Counter
import hashlib,json,re,zipfile
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from clinical_trial_risk.data.cohort import ROOT,digest
from clinical_trial_risk.llm.extract import Extractor,KINDS,visible_text,rules

def prepare():
    z=zipfile.ZipFile(ROOT/'data/annotations/chia/chia_with_scope.zip');docs=[]
    for name in sorted(z.namelist()):
        if not name.endswith('.txt'):continue
        text=z.read(name).decode('utf-8');items=[]
        for line in z.read(name[:-4]+'.ann').decode('utf-8').splitlines():
            if not line.startswith('T'):continue
            fields=line.split('\t');kind,positions=fields[1].split(' ',1)
            if kind not in KINDS:continue
            spans=[list(map(int,s.split())) for s in positions.split(';')]
            items.append({'kind':kind,'spans':spans})
        docs.append({'record_id':name[:-4],'nct_id':name.split('_')[0],'text':text,'gold':items})
    trial_ids=sorted({d['nct_id'] for d in docs});by_id={n:'\n'.join(d['text'] for d in docs if d['nct_id']==n) for n in trial_ids}
    # Fixed hashing representation; cluster >=.9 cosine near-duplicates before
    # splitting. This is a similarity proxy, not proof all paraphrases are grouped.
    v=HashingVectorizer(analyzer='char',ngram_range=(4,5),n_features=2**18,alternate_sign=False)
    mat=v.transform([by_id[n] for n in trial_ids]);sim=(mat@mat.T).tocoo();parent=list(range(len(trial_ids)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b,s in zip(sim.row,sim.col,sim.data):
        if a<b and s>=.9:parent[find(b)]=find(a)
    groups={n:trial_ids[find(i)] for i,n in enumerate(trial_ids)}
    unique=sorted(set(groups.values()),key=lambda x:hashlib.sha256(('chia-v1:'+x).encode()).hexdigest())
    dev=set(unique[:50]);test=set(unique[50:200]);records=[]
    for d in docs:
        group=groups[d['nct_id']]
        if group in dev:d['split']='development'
        elif group in test:d['split']='test'
        else:continue
        d['group']=group;records.append(d)
    p=ROOT/'data/annotations/chia/benchmark.json';p.write_text(json.dumps(records,ensure_ascii=False)+'\n')
    print('Benchmark partitions',Counter(d['split'] for d in records),'near-duplicate clusters',len(unique),flush=True)
    return records

def score(records,outputs):
    scores={k:Counter() for k in KINDS};schema=0;rejected=0;predicted=0;failures=0;outside=0;discontinuous=0
    errors=[]
    for d,o in zip(records,outputs):
        schema+=o['schema_valid'];rejected+=len(o['rejected']);predicted+=len(o['items'])+len(o['rejected']);failures+=not o['schema_valid']
        vis=visible_text(d['text']);gold=set()
        for item in d['gold']:
            if max(s[1] for s in item['spans'])>len(vis):outside+=1;continue
            if len(item['spans'])>1:discontinuous+=1
            gold.add((item['kind'],tuple(tuple(s) for s in item['spans'])))
        pred={(i['kind'],((i['start'],i['end']),)) for i in o['items']}
        for kind in KINDS:
            g={x for x in gold if x[0]==kind};p={x for x in pred if x[0]==kind}
            scores[kind].update(tp=len(g&p),fp=len(p-g),fn=len(g-p))
        errors.append({'record_id':d['record_id'],'false_positive':list(pred-gold),'false_negative':list(gold-pred),'status':o['status']})
    def metrics(c):
        tp,fp,fn=c['tp'],c['fp'],c['fn'];p=tp/(tp+fp) if tp+fp else 0;r=tp/(tp+fn) if tp+fn else 0
        return {**dict(c),'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0}
    total=Counter()
    for c in scores.values():total.update(c)
    return {'records':len(records),'trials':len({d['nct_id'] for d in records}),
        'per_type':{k:metrics(c) for k,c in scores.items()},'micro':metrics(total),
        'schema_valid_rate':schema/len(records),'failure_rate':failures/len(records),
        'rejected_span_rate':rejected/predicted if predicted else 0,
        'raw_spans':predicted,'retained_spans':predicted-rejected,
        'gold_spans_outside_prefix':outside,'gold_discontinuous_inside_prefix':discontinuous,
        'scope':'exact type plus full span offsets inside budgeted prefix; discontinuous gold retained as false negatives',
        'normalized_value_accuracy':'not evaluated: corpus entity spans are not adjudicated normalized operator/unit tuples'},errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['development','test'],default='development');a=p.parse_args()
    path=ROOT/'data/annotations/chia/benchmark.json';records=json.loads(path.read_text()) if path.exists() else prepare()
    records=[d for d in records if d['split']==a.split]
    outputs=Extractor().run([r['text'] for r in records]);llm,errors=score(records,outputs)
    baseline,_=score(records,[rules(visible_text(r['text'])) for r in records])
    llm['amortized_seconds']={k:float(np.quantile([o['amortized_seconds'] for o in outputs],q)) for k,q in [('p50',.5),('p95',.95)]}
    llm['input_tokens']=sum(o['input_tokens'] for o in outputs);llm['output_tokens']=sum(o['output_tokens'] for o in outputs)
    llm['hosted_api_cost']=0;llm['local_energy_cost']='not measured'
    out=ROOT/'reports/extraction';out.mkdir(parents=True,exist_ok=True)
    result={'split':a.split,'benchmark_sha256':digest(path),'llm':llm,'rules':baseline,
        'version':outputs[0]['version'],'limitations':['external Phase-IV domain','no local clinician adjudication','prefix budget','entity spans do not establish complete eligibility logic']}
    (out/(a.split+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    (out/(a.split+'_errors.json')).write_text(json.dumps(errors,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
