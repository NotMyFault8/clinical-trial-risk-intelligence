"""Download pinned public research resources; no source trial text is uploaded."""
import hashlib,json,urllib.request
from pathlib import Path
from huggingface_hub import snapshot_download
from clinical_trial_risk.data.cohort import ROOT
for model in json.loads((ROOT/'configs/pretrained.json').read_text()):
    snapshot_download(model['id'],revision=model['revision'],local_dir=ROOT/model['path'],
        allow_patterns=['*.json','*.safetensors','*.txt','*.model','*.jinja','README.md'])
source=json.loads((ROOT/'configs/chia_source.json').read_text())
target=ROOT/'data/annotations/chia'/source['file']['name'];target.parent.mkdir(parents=True,exist_ok=True)
if not target.exists():
    with urllib.request.urlopen(source['file']['download_url']) as response:content=response.read()
    if hashlib.sha256(content).hexdigest()!=source['sha256']:raise ValueError('CHIA checksum mismatch')
    target.write_bytes(content)
from mlx_lm import convert
quant=ROOT/'artifacts/pretrained/qwen-4bit'
if not quant.exists():convert(str(ROOT/'artifacts/pretrained/qwen'),mlx_path=str(quant),quantize=True,q_bits=4,q_group_size=64)
