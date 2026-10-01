"""Verified baseline evidence packets and additive model associations."""
import json
from functools import lru_cache
import hashlib
import joblib
import numpy as np
import pandas as pd
from scipy.special import expit,logit
from clinical_trial_risk.data.cohort import ROOT,digest
from clinical_trial_risk.features.build import build_features,NUMERIC
from clinical_trial_risk.models.train import probability

LIMITATION=('Research estimate conditional on a trial being reported Completed or Terminated at the five-year snapshot. '
            'It is not a termination probability for all newly starting trials. Retrospective temporal evaluation; no clinical or prospective validation.')

def json_value(x):
    if pd.isna(x):return None
    if isinstance(x,np.generic):return x.item()
    return x

def explain(bundle,frame):
    transformed=bundle['estimator'].named_steps['features'].transform(frame)
    names=bundle['estimator'].named_steps['features'].get_feature_names_out()
    model=bundle['estimator'].named_steps['model']
    if hasattr(model,'coef_'):
        dense=transformed.toarray() if hasattr(transformed,'toarray') else transformed
        contrib=dense[0]*model.coef_[0];base=float(model.intercept_[0])
        method='exact logistic coefficient contributions'
        reference='zero transformed design vector; scaled numeric zero is the training mean, categorical indicators all zero'
    else:
        import xgboost as xgb
        values=model.get_booster().predict(xgb.DMatrix(transformed),pred_contribs=True)[0]
        contrib=values[:-1];base=float(values[-1]);method='XGBoost TreeSHAP contributions'
        reference='tree path-dependent training background'
    raw=float(bundle['estimator'].predict_proba(frame)[0,1])
    if not np.isclose(expit(base+contrib.sum()),raw,atol=1e-5):raise ValueError('Attribution sum does not reproduce model output')
    slope=float(bundle['platt'].coef_[0,0]);intercept=float(bundle['platt'].intercept_[0])
    calibrated=contrib*slope;calbase=base*slope+intercept
    p=float(probability(bundle,frame)[0])
    if not np.isclose(expit(calbase+calibrated.sum()),p,atol=1e-5):raise ValueError('Calibrated attribution mismatch')
    order=np.argsort(-np.abs(calibrated))[:8]
    return {'method':method,'scale':'calibrated log-odds','reference':reference,
        'base_log_odds':calbase,'all_contributions_sum':float(calibrated.sum()),
        'displayed_contributions_sum':float(calibrated[order].sum()),
        'factors':[{'feature':str(names[i]),'contribution':float(calibrated[i]),
            'direction':'higher' if calibrated[i]>0 else 'lower' if calibrated[i]<0 else 'neutral'} for i in order],
        'interpretation':'model associations; not causes or effects of changing the trial'}

class Runtime:
    def __init__(self):
        self.registry=json.loads((ROOT/'artifacts/model_registry.json').read_text())
        path=ROOT/self.registry['model_path']
        if digest(path)!=self.registry['model_sha256']:raise ValueError('Registered model checksum mismatch')
        self.bundle=joblib.load(path)
        p=ROOT/'data/processed'
        if digest(p/'baseline_features.parquet')!=self.bundle['training_input_sha256']:raise ValueError('Baseline feature checksum mismatch')
        for name,expected in self.bundle.get('supplementary_input_sha256',{}).items():
            if digest(p/name)!=expected:raise ValueError('Supplementary feature checksum mismatch')
        self.raw=pd.read_parquet(p/'baseline_features.parquet')
        self.meta=pd.read_parquet(p/'cohort_metadata.parquet')
        self.features=build_features(self.raw)
        for name in ['embeddings.parquet','llm_features.parquet']:
            file=p/name
            if file.exists():self.features=self.features.merge(pd.read_parquet(file),on=['nct_id','snapshot_date'],how='left',validate='one_to_one')
        # The demo universe is explicitly the held-out resolved sample. Outcomes
        # are NOT read by the serving process and never enter a baseline packet.
        ids=json.loads((ROOT/'artifacts/demo_portfolio.json').read_text())
        self.ids=ids['nct_ids'];self.universe=ids['description']
        mask=self.features.nct_id.isin(self.ids)&(self.features.snapshot_date=='2021-09-01')
        self.demo=self.features[mask].copy()
        if len(self.demo)!=len(self.ids):raise ValueError('Demo cohort mismatch')
        self.demo['probability']=probability(self.bundle,self.demo)
        self.sources={s['snapshot_date']:s for s in json.loads((ROOT/'configs/snapshots.json').read_text())['sources']}
        extraction=ROOT/'artifacts/extractions/cohort.jsonl';self.extractions={}
        if extraction.exists():
            for line in extraction.read_text().splitlines():
                r=json.loads(line);self.extractions[(r['nct_id'],r['snapshot_date'])]=r

    def portfolio(self):
        rows=[]
        for _,r in self.demo.sort_values(['probability','nct_id'],ascending=[False,True]).iterrows():
            m=self.meta[(self.meta.nct_id==r.nct_id)&(self.meta.snapshot_date==r.snapshot_date)].iloc[0]
            rows.append({'nct_id':r.nct_id,'title':m.title,'snapshot_date':r.snapshot_date,
                         'phase':r.phase,'sponsor_class':r.sponsor_class,'probability':float(r.probability)})
        return rows

    def packet(self,nct_id):
        frame=self.demo[self.demo.nct_id==nct_id].drop(columns='probability')
        if len(frame)!=1:raise KeyError('Trial is outside the locked demonstration portfolio')
        row=frame.iloc[0];snapshot=row.snapshot_date
        original=self.raw[(self.raw.nct_id==nct_id)&(self.raw.snapshot_date==snapshot)].iloc[0]
        metadata=self.meta[(self.meta.nct_id==nct_id)&(self.meta.snapshot_date==snapshot)].iloc[0]
        p=float(probability(self.bundle,frame)[0]);reference=np.array(self.bundle['reference_probabilities'])
        percentile=float(100*(np.sum(reference<p)+.5*np.sum(reference==p))/len(reference))
        text='' if pd.isna(original.eligibility_text) else str(original.eligibility_text);sid=f'eligibility:{snapshot}:{nct_id}'
        extracted=self.extractions.get((nct_id,snapshot));items=[]
        if extracted:
            if hashlib.sha256(text.encode()).hexdigest()!=extracted['input_sha256']:raise ValueError('Extraction/source mismatch')
            for i,item in enumerate(extracted['items']):
                if text[item['start']:item['end']]!=item['evidence']:raise ValueError('Evidence span mismatch')
                items.append({**item,'citation':sid,'item_id':f'E{i+1}'})
        missing=[c for c in NUMERIC if c in original and pd.isna(original[c])]
        if original.facilities_unlisted:missing.append('facility list unavailable; not proof of zero sites')
        if original.planned_enrollment_missing:missing.append('planned enrollment unavailable; actual values excluded')
        source=self.sources[snapshot]
        return {'mode':'baseline_prediction','nct_id':nct_id,'title':metadata.title,'prediction_date':snapshot,
            'probability':p,'probability_display':f'{100*p:.1f}%',
            'percentile':percentile,'percentile_reference':'2020 calibration partition: resolved outcomes, separate sponsor groups',
            'phase':json_value(original.phase),'sponsor_class':json_value(original.sponsor_class),
            'planned_enrollment':json_value(original.planned_enrollment),'number_of_arms':json_value(original.number_of_arms),
            'attributions':explain(self.bundle,frame),'extractions':items,
            'extraction_status':extracted['status'] if extracted else 'not_available',
            'extraction_quality':'experimental span labels; exact quotes verified, clinical type/logic not guaranteed',
            'extraction_truncated':extracted['truncated'] if extracted else None,
            'missing_information':missing,'limitations':LIMITATION,
            'sources':[{'source_id':sid,'table':'eligibilities','field':'criteria','text':text,
                        'snapshot_date':snapshot,'archive_sha256':source['archive_sha256'],'catalog_url':source['catalog_url']}],
            'model':self.registry,'report_version':'baseline-template-v1','portfolio_scope':self.universe}

def template(packet):
    p=packet
    parts=[f"# {p['nct_id']}: {p['title']}",
      f"Baseline snapshot: {p['prediction_date']}. Conditional research estimate: **{p['probability_display']}**.",
      p['limitations'],f"Calibration-reference percentile: {p['percentile']:.1f}. {p['percentile_reference']}.",
      f"Phase: {p['phase'] or 'unreported'}; sponsor class: {p['sponsor_class'] or 'unreported'}; planned enrollment: {p['planned_enrollment'] if p['planned_enrollment'] is not None else 'unreported'}.",
      'Associated model factors (calibrated log-odds; not causal effects):']
    parts+=['- '+f"{f['feature']}: {f['contribution']:+.3f} ({f['direction']} score association)." for f in p['attributions']['factors']]
    parts+=['Experimental eligibility spans (verify the original context before interpretation):']
    parts+=['- '+f"{i['kind']}: “{i['evidence']}” [{i['citation']}, characters {i['start']}–{i['end']}]." for i in p['extractions'][:8]]
    if not p['extractions']:parts+=['No validated extraction available. Read the source eligibility text.']
    if p['extraction_truncated']:parts+=['Extraction used a budgeted text prefix; later criteria were not analyzed.']
    parts+=['Analyst checks: verify source context and missing fields; proposed checks are not proven risk-reducing interventions.']
    parts+=['- '+m for m in p['missing_information']]
    parts+=[f"Model: {p['model']['selected_model']}; calibration: {p['model']['calibration']}; report: {p['report_version']}."]
    parts+=[f"Source: {s['source_id']}; archive SHA256 {s['archive_sha256']}; {s['catalog_url']}." for s in p['sources']]
    return '\n\n'.join(parts)+'\n'

@lru_cache(maxsize=1)
def runtime():return Runtime()
