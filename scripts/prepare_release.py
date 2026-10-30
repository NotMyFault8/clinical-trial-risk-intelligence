"""Make a read-only serving bundle with no outcome table, credentials or raw ZIPs."""
import json,shutil
from pathlib import Path
import pandas as pd
from clinical_trial_risk.data.cohort import ROOT,digest

registry=json.loads((ROOT/'artifacts/model_registry.json').read_text())
ids=pd.read_parquet(ROOT/'artifacts/holdout_predictions.parquet').nct_id.tolist()
(ROOT/'artifacts/demo_portfolio.json').write_text(json.dumps({'nct_ids':ids,
    'description':'2021 baseline trials selected for Completed/Terminated status at five years; retrospective resolved-outcome sample'},indent=2)+'\n')
files=['data/processed/baseline_features.parquet','data/processed/cohort_metadata.parquet',
       'data/processed/embeddings.parquet','data/processed/llm_features.parquet',
       'artifacts/model_registry.json','artifacts/demo_portfolio.json','artifacts/extractions/cohort.jsonl',
       registry['model_path'],'reports/evaluation/holdout.json']
files += ['reports/extraction/llm_v3/'+name for name in (
    'fresh_evaluation.json','fresh_manifest.json','freeze.json',
    'ai_second_review.json','summary.md','ai_second_review.md')]
dest=ROOT/'artifacts/release_bundle';dest.mkdir(parents=True,exist_ok=True)
for name in files:
    src=ROOT/name;target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,target)
manifest={'purpose':'local read-only research serving bundle','files':{n:digest(dest/n) for n in files},
    'excluded':['outcomes.parquet','raw archives','credentials','why_stopped','holdout labels'],
    'model_registry_sha256':digest(ROOT/'artifacts/model_registry.json')}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Serving bundle ready:',len(files),'files')
