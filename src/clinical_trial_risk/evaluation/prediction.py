"""One frozen temporal holdout, paired cluster uncertainty and descriptive drift."""
import json,math
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score,roc_auc_score,brier_score_loss,
    balanced_accuracy_score,precision_score,recall_score,f1_score)
from sklearn.feature_extraction.text import HashingVectorizer
from clinical_trial_risk.data.cohort import ROOT,digest
from clinical_trial_risk.models.train import load_data,probability,FAMILIES
from clinical_trial_risk.features.build import NUMERIC,CATEGORICAL,build_features

def metrics(y,p):
    y=np.asarray(y,dtype=int);p=np.asarray(p);pred=p>=.5
    result={'n':len(y),'events':int(y.sum()),'prevalence':float(y.mean()),
        'average_precision':float(average_precision_score(y,p)) if y.sum() else None,
        'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
        'brier':float(brier_score_loss(y,p)),'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
        'precision':float(precision_score(y,pred,zero_division=0)),
        'recall':float(recall_score(y,pred,zero_division=0)),
        'f1':float(f1_score(y,pred,zero_division=0))}
    bins=[];ece=0.
    for i in range(10):
        mask=(p>=i/10)&((p<(i+1)/10) if i<9 else (p<=1))
        if not mask.any():continue
        mean=float(p[mask].mean());observed=float(y[mask].mean())
        bins.append({'lower':i/10,'upper':(i+1)/10,'n':int(mask.sum()),'mean_prediction':mean,'observed_rate':observed})
        ece+=mask.mean()*abs(mean-observed)
    result['ece_10_bins']=float(ece);result['calibration_bins']=bins
    order=np.argsort(-p,kind='stable')
    result['top_k']={}
    for fraction in [.05,.1,.2]:
        k=max(1,math.ceil(len(y)*fraction));captured=int(y[order[:k]].sum());precision=captured/k
        result['top_k'][str(fraction)]={'reviewed':k,'captured':captured,'precision':precision,
            'recall':captured/y.sum() if y.sum() else None,'lift':precision/y.mean() if y.mean() else None}
    return result

def cluster_intervals(y,predictions,groups,reps=1000):
    rng=np.random.default_rng(731);unique=np.unique(groups);indices={g:np.flatnonzero(groups==g) for g in unique}
    samples={name:{'average_precision':[],'brier':[]} for name in predictions}
    for _ in range(reps):
        idx=np.concatenate([indices[g] for g in rng.choice(unique,len(unique),replace=True)])
        if len(np.unique(y[idx]))<2:continue
        for name,p in predictions.items():
            samples[name]['average_precision'].append(average_precision_score(y[idx],p[idx]))
            samples[name]['brier'].append(brier_score_loss(y[idx],p[idx]))
    intervals={name:{m:np.quantile(v,[.025,.975]).tolist() for m,v in d.items()} for name,d in samples.items()}
    ref=samples['structured_logistic'];deltas={}
    for name,d in samples.items():
        if name=='structured_logistic':continue
        deltas[name]={m:{'difference':float((average_precision_score(y,predictions[name])-average_precision_score(y,predictions['structured_logistic'])) if m=='average_precision' else (brier_score_loss(y,predictions[name])-brier_score_loss(y,predictions['structured_logistic']))),
            'ci95':np.quantile(np.array(v)-np.array(ref[m]),[.025,.975]).tolist()} for m,v in d.items()}
    return {'replicates_requested':reps,'replicates_valid':len(ref['brier']),'clusters':len(unique),
        'method':'paired percentile bootstrap of held-out lead-sponsor clusters; conditional on fitted models',
        'intervals':intervals,'differences_from_structured_logistic':deltas}

def descriptive_audit(data):
    tr=data[data.split=='train'];te=data[data.split=='test'];drift={}
    for c in NUMERIC:
        sd=tr[c].std();drift[c]={'train_mean':None if pd.isna(tr[c].mean()) else float(tr[c].mean()),
            'test_mean':None if pd.isna(te[c].mean()) else float(te[c].mean()),
            'standardized_mean_difference':float((te[c].mean()-tr[c].mean())/sd) if sd>0 else None,
            'train_missing':float(tr[c].isna().mean()),'test_missing':float(te[c].isna().mean())}
    categorical={}
    for c in CATEGORICAL:
        a=tr[c].value_counts(normalize=True);b=te[c].value_counts(normalize=True);levels=a.index.union(b.index)
        categorical[c]={'total_variation':float((a.reindex(levels,fill_value=0)-b.reindex(levels,fill_value=0)).abs().sum()/2),
                        'train':a.to_dict(),'test':b.to_dict()}
    v=HashingVectorizer(analyzer='char',ngram_range=(4,5),n_features=2**18,alternate_sign=False)
    traintext=v.transform(tr.eligibility_text);testtext=v.transform(te.eligibility_text)
    similarities=(testtext@traintext.T).toarray().max(axis=1)
    return {'numeric':drift,'categorical':categorical,
        'near_duplicate_test_count':int((similarities>=.9).sum()),'similarity_method':'fixed hashed character n-gram cosine >=0.9',
        'train_test_sponsor_overlap':len(set(tr.sponsor_cluster)&set(te.sponsor_cluster)),
        'prevalence_by_year':data.groupby('year').label.agg(['count','sum','mean']).to_dict()},similarities

def selection_audit():
    p=ROOT/'data/processed';f=build_features(pd.read_parquet(p/'baseline_features.parquet'))
    m=pd.read_parquet(p/'cohort_metadata.parquet');l=pd.read_parquet(p/'outcomes.parquet')
    d=f.merge(m[m.primary][['nct_id','snapshot_date']],on=['nct_id','snapshot_date'],validate='one_to_one').merge(l,on=['nct_id','snapshot_date'],validate='one_to_one')
    d['resolved']=d.label.notna();out={}
    for status,g in d.groupby('resolved'):
        out['resolved' if status else 'excluded']={'n':len(g),'numeric_means':{c:float(g[c].mean()) if g[c].notna().any() else None for c in NUMERIC},
            'sponsor_class':g.sponsor_class.value_counts(normalize=True).to_dict(),
            'phase':g.phase.value_counts(normalize=True).to_dict(),'status_counts':g.outcome_status.value_counts().to_dict()}
    return out

def main():
    out=ROOT/'reports/evaluation';out.mkdir(parents=True,exist_ok=True)
    if (out/'holdout.json').exists():raise FileExistsError('Frozen holdout already evaluated; preserve it. Change version for a new study.')
    data=load_data();test=data[data.split=='test'].copy();predictions={};results={};bundles={};validation={}
    for family in FAMILIES:
        path=ROOT/'artifacts/models/primary'/(family+'.joblib')
        if not path.exists():raise FileNotFoundError(f'All prespecified families must be frozen first: {path}')
        bundle=joblib.load(path)
        if set(bundle['training_ids']+bundle['calibration_ids'])&set(test.nct_id):raise ValueError('Holdout ID contamination')
        if bundle['protocol_sha256']!=digest(ROOT/'configs/analysis_protocol.json'):raise ValueError('Protocol changed after fit')
        if bundle['training_input_sha256']!=digest(ROOT/'data/processed/baseline_features.parquet'):raise ValueError('Baseline data changed after fit')
        bundles[family]=bundle;validation[family]=json.loads((ROOT/'reports/models/primary'/(family+'.json')).read_text())['chosen_tuning_AP']
    # Selection uses only previously frozen validation scores, before test scores.
    extraction_release=json.loads((ROOT/'configs/extraction_release.json').read_text())
    extraction_eval=json.loads((ROOT/'reports/extraction/test.json').read_text())['llm']
    extraction_pass=(extraction_eval['schema_valid_rate']>=extraction_release['test_min_schema_valid_rate']
        and extraction_eval['micro']['precision']>=extraction_release['test_min_micro_precision']
        and extraction_eval['micro']['f1']>=extraction_release['test_min_micro_f1']
        and extraction_release['target_cohort_human_semantic_review_completed'])
    qualified=[f for f in FAMILIES if f!='structured_llm' or extraction_pass]
    selected=max(qualified,key=lambda f:validation[f])
    for family,bundle in bundles.items():
        predictions[family]=probability(bundle,test)
        results[family]={mode:metrics(test.label,probability(bundle,test,mode)) for mode in ['raw','platt','isotonic']}
    drift,similarity=descriptive_audit(data)
    y=test.label.astype(int).to_numpy();subgroups={}
    for field in ['phase','sponsor_class','therapeutic_area','has_us_site']:
        subgroups[field]={}
        for name,g in test.groupby(field,dropna=False):
            idx=test.index.get_indexer(g.index);yy=y[idx]
            subgroups[field][str(name)]={'n':len(g),'events':int(yy.sum()),'metrics':metrics(yy,predictions[selected][idx]) if len(g)>=30 and yy.sum()>=5 and (1-yy).sum()>=5 else None}
    sensitivity={}
    for variant in ['possible_date_interval','withdrawal','no_facilities','zero_imputation']:
        d=load_data('possible' if variant=='possible_date_interval' else 'primary','withdrawal' if variant=='withdrawal' else 'primary');t=d[d.split=='test']
        sensitivity[variant]={}
        for family in ['structured_logistic','structured_tfidf']:
            b=joblib.load(ROOT/'artifacts/models'/variant/(family+'.joblib'))
            sensitivity[variant][family]=metrics(t.label,probability(b,t))
    mask=similarity<.9
    sensitivity['test_without_near_duplicate_training_text']={f:metrics(y[mask],p[mask]) for f,p in predictions.items()}
    result={'selected_using_validation':selected,'validation_AP':validation,
        'qualified_for_local_demo':qualified,'llm_extraction_release_passed':extraction_pass,
        'extraction_gate_sha256':digest(ROOT/'configs/extraction_release.json'),
        'protocol_sha256':digest(ROOT/'configs/analysis_protocol.json'),
        'test_trials':len(test),'test_events':int(y.sum()),'models':results,
        'uncertainty':cluster_intervals(y,predictions,test.sponsor_cluster.to_numpy()),
        'subgroups_selected_model':subgroups,'drift':drift,'selection':selection_audit(),'sensitivities':sensitivity,
        'no_skill_reference':{'AP':float(y.mean()),'brier_training_prevalence':float(brier_score_loss(y,np.repeat(data[data.split=='train'].label.mean(),len(y))))},
        'interpretation':'retrospective conditional resolved-outcome comparison; no prospective or clinical validation'}
    for family,p in predictions.items():test[family]=p
    test[['nct_id','snapshot_date','label','sponsor_cluster']+FAMILIES].to_parquet(ROOT/'artifacts/holdout_predictions.parquet',index=False)
    (out/'holdout.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    registry={'selected_model':selected,'selection_basis':'locked 2020 tuning average precision',
        'model_path':f'artifacts/models/primary/{selected}.joblib','model_sha256':digest(ROOT/f'artifacts/models/primary/{selected}.joblib'),
        'protocol_sha256':result['protocol_sha256'],'evaluation_sha256':digest(out/'holdout.json'),
        'release_scope':'local retrospective research demonstrator','calibration':'Platt; separate 2020 sponsor groups',
        'generation':'deterministic template; free-form LLM not released'}
    (ROOT/'artifacts/model_registry.json').write_text(json.dumps(registry,indent=2)+'\n')
    print('Selected by validation:',selected)
    for f in FAMILIES:print(f,{k:results[f]['platt'][k] for k in ['average_precision','roc_auc','brier']})

if __name__=='__main__':main()
