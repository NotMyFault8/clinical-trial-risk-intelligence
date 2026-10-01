"""Template versus experimental generation: exact checks, explicit review limits."""
from dataclasses import asdict
import hashlib,json,re,time
from typing import Annotated
import numpy as np
from pydantic import BaseModel,ConfigDict,Field
from clinical_trial_risk.data.cohort import ROOT,digest
from clinical_trial_risk.reporting.packets import runtime,template
from clinical_trial_risk.llm.extract import unique_json_object

class Citation(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    source_id:str
    quote:str

class GeneratedReport(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    risk_display:str
    percentile_display:str
    overview:str
    associations:str
    evidence:Annotated[list[Citation],Field(max_length=6)]
    limitations:str
    analyst_check:str

def check_generated(raw,packet):
    body=re.sub(r'^```(?:json)?\s*','',raw.strip());body=re.sub(r'\s*```$','',body)
    try:r=GeneratedReport.model_validate(json.loads(body,object_pairs_hook=unique_json_object))
    except (ValueError,TypeError):return {'schema_valid':False,'released':False,'reason':'invalid_schema'}
    risk=r.risk_display==packet['probability_display'];percentile=r.percentile_display==packet['percentile_display']
    citations={s['source_id']:s['quote'] for s in packet['evidence']}
    supported=sum(c.source_id in citations and c.quote==citations[c.source_id] for c in r.evidence)
    limitation=r.limitations==packet['limitations']
    percentages=re.findall(r'\d+(?:\.\d+)?\s*%',r.overview+' '+r.associations+' '+r.analyst_check)
    invented_percent=any(v.replace(' ','')!=packet['probability_display'] for v in percentages)
    prohibited=bool(re.search(r'\b(causes?|will prevent|will reduce risk|guarantee[sd]?)\b',r.associations,re.I))
    checks={'schema_valid':True,'risk_numeric_match':risk,'percentile_numeric_match':percentile,
        'citation_count':len(r.evidence),'exact_supported_citations':supported,'limitations_exact':limitation,
        'unapproved_percentage':invented_percent,'causal_phrase_flag':prohibited,
        'evidence_completeness':supported/len(citations) if citations else float(not r.evidence),
        'semantic_support':'not independently reviewed','usefulness':'not independently reviewed',
        'released':False}
    checks['automated_checks_pass']=risk and percentile and supported==len(r.evidence) and limitation and not invented_percent and not prohibited
    return checks

def compact_packet(p):
    # Only baseline evidence and computed typed outputs; no outcome file access.
    return {'nct_id':p['nct_id'],'phase':p['phase'],'sponsor_class':p['sponsor_class'],
        'probability_display':p['probability_display'],'percentile_display':f"{p['percentile']:.1f}",
        'attributions':p['attributions'],'missing_information':p['missing_information'],'limitations':p['limitations'],
        'evidence':[{'source_id':i['item_id'],'quote':i['evidence']} for i in p['extractions'][:3]]}

def main():
    from mlx_lm import load,batch_generate
    rt=runtime();ids=sorted(rt.ids,key=lambda n:hashlib.sha256(('report-v1:'+n).encode()).hexdigest())[:40]
    packets=[rt.packet(n) for n in ids];compact=[compact_packet(p) for p in packets]
    prompt=(ROOT/'prompts/report_v1.txt').read_text();model,tok=load(str(ROOT/'artifacts/pretrained/qwen-4bit'))
    out=ROOT/'reports/generation';out.mkdir(parents=True,exist_ok=True)
    details=[];blinded=[];mapping=[]
    for offset in range(0,len(ids),8):
        batch=compact[offset:offset+8]
        prompts=[tok.apply_chat_template([{'role':'system','content':prompt},{'role':'user','content':json.dumps({k:v for k,v in p.items() if k!='nct_id'})}],tokenize=True,add_generation_prompt=True) for p in batch]
        beg=time.perf_counter();result=batch_generate(model,tok,prompts=prompts,max_tokens=700,completion_batch_size=8,prefill_batch_size=4)
        elapsed=time.perf_counter()-beg
        for j,(p,raw) in enumerate(zip(batch,result.texts)):
            packet=packets[offset+j];start=time.perf_counter();baseline=template(packet);template_seconds=time.perf_counter()-start
            checks=check_generated(raw,p)
            details.append({'nct_id':p['nct_id'],'packet':p,'raw_generation':raw,'checks':checks,
                'batch_seconds':elapsed,'batch_size':len(batch),'amortized_seconds':elapsed/len(batch),
                'input_tokens':len(prompts[j]),'output_tokens':len(tok.encode(raw)),
                'template_seconds':template_seconds,'template_risk_match':p['probability_display'] in baseline,
                'batch_stats':asdict(result.stats)})
            swap=int(hashlib.sha256(p['nct_id'].encode()).hexdigest()[:8],16)%2
            texts=[baseline,raw] if not swap else [raw,baseline]
            blinded.append({'case':len(blinded)+1,'source_packet':p,'report_A':texts[0],'report_B':texts[1],
                'review':{'factual_support_A':None,'factual_support_B':None,'clarity_A':None,'clarity_B':None,'usefulness_preference':None,'unsupported_claims':None}})
            mapping.append({'case':len(blinded),'A':'template' if not swap else 'LLM','B':'LLM' if not swap else 'template'})
        print('Reports evaluated',offset+len(batch),flush=True)
    valid=[d['checks'] for d in details if d['checks']['schema_valid']]
    mismatches=sum(not c['risk_numeric_match'] or c['unapproved_percentage'] for c in valid)
    citations=sum(c['citation_count'] for c in valid);supported=sum(c['exact_supported_citations'] for c in valid)
    summary={'n':len(details),'schema_valid_rate':len(valid)/len(details),
        'risk_value_mismatches_among_schema_valid':mismatches,'schema_valid_denominator':len(valid),
        'exact_citation_support_rate':supported/citations if citations else None,'citation_denominator':citations,
        'automated_all_checks_pass_rate':sum(c.get('automated_checks_pass',False) for c in valid)/len(details),
        'template_risk_match_rate':sum(d['template_risk_match'] for d in details)/len(details),
        'generated_amortized_seconds_p50':float(np.median([d['amortized_seconds'] for d in details])),
        'generated_amortized_seconds_p95':float(np.quantile([d['amortized_seconds'] for d in details],.95)),
        'template_seconds_p50':float(np.median([d['template_seconds'] for d in details])),
        'input_tokens':sum(d['input_tokens'] for d in details),'output_tokens':sum(d['output_tokens'] for d in details),
        'hosted_api_cost':0,'local_energy_cost':'not measured',
        'semantic_faithfulness':'not independently reviewed; automated checks are insufficient',
        'usefulness_improvement':'not measured; blinded review form prepared, not completed',
        'release':'withheld; deterministic template is served',
        'prompt_sha256':digest(ROOT/'prompts/report_v1.txt'),'release_gate_sha256':digest(ROOT/'configs/report_release.json'),
        'model':json.loads((ROOT/'configs/pretrained.json').read_text())[0]}
    (out/'evaluation.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'cases.json').write_text(json.dumps(details,indent=2,ensure_ascii=False)+'\n')
    (out/'blinded_review.json').write_text(json.dumps(blinded,indent=2,ensure_ascii=False)+'\n')
    (out/'review_key.json').write_text(json.dumps(mapping,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
