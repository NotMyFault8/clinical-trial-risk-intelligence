"""Tune on development data, calibrate separately, save locked estimators.

No held-out performance is computed here. Evaluation is a separate command.
"""
import argparse
import hashlib
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from scipy.special import logit,expit
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler

from clinical_trial_risk.data.cohort import ROOT,digest
from clinical_trial_risk.features.build import build_features,NUMERIC,CATEGORICAL,COUNTS

FAMILIES=['structured_logistic','structured_counts','structured_tfidf','structured_boosting','structured_embeddings','structured_llm']

def group_name(row):
    val=row.get('sponsor_group')
    return ' '.join(str(val).lower().split()) if pd.notna(val) and str(val).strip() else row['nct_id']

def partition(sponsor):return int(hashlib.sha256(sponsor.encode()).hexdigest()[:8],16)%2

def load_data(cohort='primary',endpoint='primary'):
    p=ROOT/'data/processed'
    raw=pd.read_parquet(p/'baseline_features.parquet');meta=pd.read_parquet(p/'cohort_metadata.parquet')
    labels=pd.read_parquet(p/'outcomes.parquet')
    keys=['nct_id','snapshot_date']
    selected=meta[meta[cohort]].merge(labels,on=keys,validate='one_to_one')
    if endpoint=='withdrawal':selected['label']=selected.outcome_status.map({'completed':0,'terminated':1,'withdrawn':1})
    selected=selected[selected.label.notna()].copy()
    # Build the baseline matrix BEFORE labels are joined to avoid accidental feature reuse.
    x=build_features(raw)
    for filename in ['embeddings.parquet','llm_features.parquet']:
        path=p/filename
        if path.exists():x=x.merge(pd.read_parquet(path),on=keys,how='left',validate='one_to_one')
    x=x.merge(selected,on=keys,validate='one_to_one')
    x['sponsor_cluster']=x.apply(group_name,axis=1)
    x['year']=x.snapshot_date.str[:4].astype(int)
    x['split']=np.where(x.year<=2019,'train',np.where(x.year==2021,'test',
        np.where(x.sponsor_cluster.map(partition)==0,'tune','calibrate')))
    if x.nct_id.duplicated().any():raise ValueError('More than one prediction per trial')
    return x

def estimator(family,candidate,no_facilities=False,zero_impute=False):
    nums=NUMERIC.copy()
    if no_facilities:nums=[c for c in nums if c not in ['facility_count','country_count','has_us_site','facilities_unlisted']]
    if family=='structured_counts':nums+=COUNTS
    if family=='structured_llm':nums+=['llm_measurement_count','llm_value_count','llm_temporal_count','llm_failure','llm_truncated','llm_rejected_count']
    numeric=Pipeline([('impute',SimpleImputer(strategy='constant' if zero_impute else 'median',fill_value=0,add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())])
    transforms=[('numeric',numeric,nums),('category',OneHotEncoder(handle_unknown='ignore',min_frequency=5),CATEGORICAL)]
    if family=='structured_tfidf':transforms.append(('text',TfidfVectorizer(ngram_range=(1,2),min_df=3,max_features=6000,sublinear_tf=True),'eligibility_text'))
    if family=='structured_embeddings':
        transforms.append(('embedding',Pipeline([('impute',SimpleImputer()),('pca',PCA(n_components=32,random_state=731)),('scale',StandardScaler())]),[f'emb_{i}' for i in range(384)]))
    prep=ColumnTransformer(transforms,sparse_threshold=0 if family=='structured_boosting' else 0.3)
    if family=='structured_boosting':
        from xgboost import XGBClassifier
        model=XGBClassifier(n_estimators=150,learning_rate=.04,subsample=1,colsample_bytree=1,
            reg_lambda=10,eval_metric='logloss',random_state=731,n_jobs=4,**candidate)
    else:model=LogisticRegression(C=candidate,max_iter=3000,solver='lbfgs',random_state=731)
    return Pipeline([('features',prep),('model',model)])

def probability(bundle,x,mode='platt'):
    p=bundle['estimator'].predict_proba(x)[:,1]
    if mode=='raw':return p
    if mode=='isotonic':return bundle['isotonic'].predict(p)
    return bundle['platt'].predict_proba(logit(np.clip(p,1e-7,1-1e-7)).reshape(-1,1))[:,1]

def fit_family(data,family,protocol,variant='primary',**options):
    tr=data[data.split=='train'];tu=data[data.split=='tune'];ca=data[data.split=='calibrate']
    for frame in [tr,tu,ca]:
        if frame.label.nunique()!=2:raise ValueError('Training/development partition has one class')
    if set(tu.sponsor_cluster)&set(ca.sponsor_cluster):raise ValueError('Calibration shares tuning sponsors')
    candidates=protocol['boosting_candidates'] if family=='structured_boosting' else protocol['logistic_C']
    scores=[];models=[];beg=time.perf_counter()
    for candidate in candidates:
        pipe=estimator(family,candidate,**options)
        pipe.fit(tr,tr.label.astype(int));ap=average_precision_score(tu.label,pipe.predict_proba(tu)[:,1])
        scores.append(float(ap));models.append(pipe)
    best=int(np.argmax(scores));model=models[best]
    p=model.predict_proba(ca)[:,1]
    platt=LogisticRegression(C=1e6,max_iter=1000).fit(logit(np.clip(p,1e-7,1-1e-7)).reshape(-1,1),ca.label.astype(int))
    iso=IsotonicRegression(out_of_bounds='clip').fit(p,ca.label)
    bundle={'estimator':model,'platt':platt,'isotonic':iso,'family':family,'variant':variant,
        'protocol_sha256':digest(ROOT/'configs/analysis_protocol.json'),
        'training_input_sha256':digest(ROOT/'data/processed/baseline_features.parquet'),
        'outcome_input_sha256':digest(ROOT/'data/processed/outcomes.parquet'),
        'training_ids':tr.nct_id.tolist(),'calibration_ids':ca.nct_id.tolist(),
        'reference_probabilities':None}
    extra='embeddings.parquet' if family=='structured_embeddings' else 'llm_features.parquet' if family=='structured_llm' else None
    bundle['supplementary_input_sha256']={extra:digest(ROOT/'data/processed'/extra)} if extra else {}
    bundle['training_code_sha256']=digest(__file__)
    bundle['feature_code_sha256']=digest(ROOT/'src/clinical_trial_risk/features/build.py')
    bundle['reference_probabilities']=probability(bundle,ca).tolist()
    output=ROOT/'artifacts/models'/variant;output.mkdir(parents=True,exist_ok=True)
    joblib.dump(bundle,output/(family+'.joblib'))
    summary={'family':family,'variant':variant,'candidates':candidates,'tuning_AP':scores,
        'chosen_candidate':candidates[best],'chosen_tuning_AP':scores[best],
        'platt_slope':float(platt.coef_[0,0]),'platt_intercept':float(platt.intercept_[0]),
        'fit_seconds':time.perf_counter()-beg,'split_counts':data.groupby('split').label.agg(['count','sum']).to_dict(),
        'protocol_sha256':bundle['protocol_sha256'],'model_sha256':digest(output/(family+'.joblib'))}
    report=ROOT/'reports/models'/variant;report.mkdir(parents=True,exist_ok=True)
    (report/(family+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
    print(family,'validation AP',scores,'Platt slope',summary['platt_slope'],flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--families',nargs='+',default=FAMILIES[:4]);parser.add_argument('--variant',default='primary',choices=['primary','possible_date_interval','withdrawal','no_facilities','zero_imputation']);args=parser.parse_args()
    protocol=json.loads((ROOT/'configs/analysis_protocol.json').read_text())
    data=load_data('possible' if args.variant=='possible_date_interval' else 'primary','withdrawal' if args.variant=='withdrawal' else 'primary')
    for family in args.families:
        fit_family(data,family,protocol,args.variant,no_facilities=args.variant=='no_facilities',zero_impute=args.variant=='zero_imputation')

if __name__=='__main__':main()
