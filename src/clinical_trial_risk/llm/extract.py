"""Local, cached span extraction. Unsupported/ambiguous evidence fails closed."""
import argparse
from dataclasses import asdict
import hashlib
import json
import re
import time
from typing import Annotated

import pandas as pd
from pydantic import BaseModel,ConfigDict,Field,ValidationError
from clinical_trial_risk.data.cohort import ROOT,digest

KINDS=['Measurement','Value','Temporal'];MAX_CHARS=1800;MAX_TOKENS=384

class Spans(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    Measurement:Annotated[list[str],Field(max_length=6)]
    Value:Annotated[list[str],Field(max_length=6)]
    Temporal:Annotated[list[str],Field(max_length=6)]

def visible_text(text):
    text=str(text or '')
    if len(text)<=MAX_CHARS:return text
    # Avoid slicing a word in half; this is an explicitly budgeted prefix task.
    prefix=text[:MAX_CHARS];boundary=prefix.rfind(' ')
    return prefix[:boundary] if boundary>MAX_CHARS-100 else prefix

def unique_json_object(pairs):
    obj={}
    for key,value in pairs:
        if key in obj:raise ValueError('Duplicate JSON key')
        obj[key]=value
    return obj

def validate_output(raw,text):
    response=raw.strip()
    if response.startswith('```'):
        response=re.sub(r'^```(?:json)?\s*','',response);response=re.sub(r'\s*```$','',response)
    try:parsed=Spans.model_validate(json.loads(response,object_pairs_hook=unique_json_object))
    except (ValueError,ValidationError):return {'status':'extraction_failed','schema_valid':False,'items':[],'rejected':[]}
    items=[];rejected=[];seen=set()
    for kind,strings in parsed.model_dump().items():
        for evidence in strings:
            starts=[m.start() for m in re.finditer(re.escape(evidence),text)] if evidence.strip() else []
            if len(starts)!=1:
                rejected.append({'kind':kind,'evidence':evidence,'reason':'not_found' if not starts else 'ambiguous_repeated_span'});continue
            start=starts[0];key=(kind,start,start+len(evidence))
            if key in seen:continue
            seen.add(key);items.append({'kind':kind,'evidence':evidence,'start':start,'end':start+len(evidence),
                'numeric_literals':re.findall(r'\d+(?:\.\d+)?',evidence),'status':'source_span_supported'})
    return {'status':'partial' if rejected else 'supported' if items else 'not_stated_in_visible_prefix',
        'schema_valid':True,'items':items,'rejected':rejected}

def rules(text):
    patterns={
      'Measurement':r'\b(?:age|BMI|body mass index|platelet count|platelets|hemoglobin|creatinine|creatinine clearance|bilirubin|AST|ALT|ECOG|Karnofsky|HbA1c|blood pressure|neutrophil count)\b',
      'Value':r'(?:>=|<=|>|<|≥|≤|at least|at most|greater than|less than)\s*\d+(?:\.\d+)?(?:\s*(?:to|[-–])\s*\d+(?:\.\d+)?)?(?:\s*(?:mg/d[lL]|g/d[lL]|mmHg|%|years|kg/m2|x\s*ULN))?',
      'Temporal':r'\b(?:(?:within|at least|for|in the last|during the last)\s+)?(?:\d+|one|two|three|four|six|twelve)\s+(?:hours?|days?|weeks?|months?|years?)(?:\s+(?:prior to|before|after)\s+(?:screening|enrollment|study entry|randomization))?\b'}
    items=[]
    for kind,pattern in patterns.items():
        for m in re.finditer(pattern,text,re.I):
            items.append({'kind':kind,'evidence':m[0],'start':m.start(),'end':m.end(),'status':'source_span_supported'})
    return {'status':'supported' if items else 'not_stated_in_visible_prefix','schema_valid':True,'items':items,'rejected':[]}

class Extractor:
    def __init__(self):
        from mlx_lm import load
        self.model,self.tokenizer=load(str(ROOT/'artifacts/pretrained/qwen-4bit'))
        self.prompt=(ROOT/'prompts/extract_v1.txt').read_text()
        cfg=json.loads((ROOT/'configs/pretrained.json').read_text())[0]
        self.version={'model':cfg,'quantization':'mlx affine 4-bit group64',
            'quantized_weights_sha256':{p.name:digest(p) for p in (ROOT/'artifacts/pretrained/qwen-4bit').glob('*.safetensors')},
            'prompt_sha256':hashlib.sha256(self.prompt.encode()).hexdigest(),'schema':'span-v1',
            'max_characters':MAX_CHARS,'max_output_tokens':MAX_TOKENS,'decoding':'greedy',
            'implementation_sha256':digest(__file__)}
        self.cache=ROOT/'artifacts/extraction_cache';self.cache.mkdir(parents=True,exist_ok=True)

    def run(self,texts):
        from mlx_lm import batch_generate
        output=[None]*len(texts);pending=[]
        for i,text in enumerate(texts):
            visible=visible_text(text)
            key=hashlib.sha256(json.dumps({'text':text,'version':self.version},sort_keys=True).encode()).hexdigest()
            path=self.cache/(key+'.json')
            if path.exists():output[i]=json.loads(path.read_text());continue
            messages=[{'role':'system','content':self.prompt},{'role':'user','content':'SOURCE:\n'+visible}]
            tokens=self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
            pending.append((i,text,visible,key,path,tokens))
        for offset in range(0,len(pending),16):
            batch=pending[offset:offset+16];beg=time.perf_counter()
            generated=batch_generate(self.model,self.tokenizer,[b[5] for b in batch],max_tokens=MAX_TOKENS,
                completion_batch_size=16,prefill_batch_size=4,verbose=False)
            seconds=time.perf_counter()-beg
            for entry,raw in zip(batch,generated.texts):
                i,text,visible,key,path,tokens=entry;result=validate_output(raw,visible)
                result.update({'raw_output':raw,'input_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'run_id':key,'source_visible_characters':len(visible),'truncated':len(visible)<len(text),
                    'input_tokens':len(tokens),'output_tokens':len(self.tokenizer.encode(raw)),
                    'batch_seconds':seconds,'amortized_seconds':seconds/len(batch),'batch_size':len(batch),
                    'version':self.version,'batch_stats':asdict(generated.stats)})
                path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');output[i]=result
            print('Extraction',min(offset+len(batch),len(pending)),'/',len(pending),'batch seconds',round(seconds,2),flush=True)
        return output

def cohort():
    # IDs select the locked resolved cohort; only baseline text enters the extractor.
    p=ROOT/'data/processed';raw=pd.read_parquet(p/'baseline_features.parquet')
    meta=pd.read_parquet(p/'cohort_metadata.parquet');labels=pd.read_parquet(p/'outcomes.parquet')
    keys=['nct_id','snapshot_date'];selected=meta[meta.primary][keys].merge(labels[labels.label.notna()][keys],on=keys,validate='one_to_one')
    df=raw.merge(selected,on=keys,validate='one_to_one').sort_values(keys).reset_index(drop=True)
    outputs=Extractor().run(df.eligibility_text.fillna('').tolist());features=[];records=[]
    for (_,row),result in zip(df.iterrows(),outputs):
        features.append({'nct_id':row.nct_id,'snapshot_date':row.snapshot_date,
            **{f'llm_{kind.lower()}_count':sum(i['kind']==kind for i in result['items']) for kind in KINDS},
            'llm_failure':int(not result['schema_valid']),'llm_truncated':int(result['truncated']),
            'llm_rejected_count':len(result['rejected'])})
        records.append({'nct_id':row.nct_id,'snapshot_date':row.snapshot_date,**result})
    pd.DataFrame(features).to_parquet(p/'llm_features.parquet',index=False)
    out=ROOT/'artifacts/extractions';out.mkdir(parents=True,exist_ok=True)
    (out/'cohort.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))

if __name__=='__main__':cohort()
