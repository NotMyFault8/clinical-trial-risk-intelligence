"""Copy user-downloaded archives to configured paths and verify immutable hashes."""
import argparse,json,shutil
from pathlib import Path
from clinical_trial_risk.data.cohort import ROOT,digest
p=argparse.ArgumentParser();p.add_argument('--downloads',type=Path,required=True);a=p.parse_args()
for source in json.loads((ROOT/'configs/snapshots.json').read_text())['sources']:
    target=ROOT/source['archive_path']
    if not target.exists():
        downloaded=a.downloads/target.name
        if digest(downloaded)!=source['archive_sha256']:raise ValueError('Downloaded archive differs from pinned source')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(downloaded,target)
    if digest(target)!=source['archive_sha256']:raise ValueError(f'Archive mismatch: {target}')
    print(source['snapshot_date'],'verified')
