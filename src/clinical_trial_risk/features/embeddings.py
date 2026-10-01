"""Frozen, word-chunked MiniLM embeddings; no outcome access or fitted vocabulary."""
import json,time
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from clinical_trial_risk.data.cohort import ROOT,digest

def main():
    raw=pd.read_parquet(ROOT/'data/processed/baseline_features.parquet')
    model=SentenceTransformer(str(ROOT/'artifacts/pretrained/minilm'),local_files_only=True,device='cpu')
    # 100 words leave room below 256 model tokens for most English text. The
    # tokenizer enforces 256 and truncations are measured, not hidden.
    chunks=[];owners=[];token_truncations=0
    for idx,text in enumerate(raw.eligibility_text.fillna('')):
        words=text.split();pieces=[' '.join(words[i:i+100]) for i in range(0,len(words),100)] or ['']
        for piece in pieces:
            token_truncations+=len(model.tokenizer.encode(piece,add_special_tokens=True))>model.max_seq_length
            chunks.append(piece);owners.append(idx)
    start=time.perf_counter()
    vec=model.encode(chunks,batch_size=64,show_progress_bar=True,normalize_embeddings=True)
    means=np.zeros((len(raw),384),dtype=np.float64);counts=np.zeros(len(raw))
    for owner,v in zip(owners,vec):means[owner]+=v;counts[owner]+=1
    means/=counts[:,None];means/=np.maximum(np.linalg.norm(means,axis=1,keepdims=True),1e-12)
    out=raw[['nct_id','snapshot_date']].copy()
    out=pd.concat([out,pd.DataFrame(means,columns=[f'emb_{i}' for i in range(384)])],axis=1)
    out.to_parquet(ROOT/'data/processed/embeddings.parquet',index=False)
    p=ROOT/'reports/text';p.mkdir(parents=True,exist_ok=True)
    (p/'embeddings.json').write_text(json.dumps({'model':json.loads((ROOT/'configs/pretrained.json').read_text())[1],
        'rows':len(raw),'chunks':len(chunks),'word_chunk_size':100,'token_limit':model.max_seq_length,
        'token_truncated_chunks':token_truncations,'seconds':time.perf_counter()-start,
        'source_sha256':digest(ROOT/'data/processed/baseline_features.parquet'),
        'training_cutoff':'undocumented; contamination cannot be excluded'},indent=2)+'\n')

if __name__=='__main__':main()
