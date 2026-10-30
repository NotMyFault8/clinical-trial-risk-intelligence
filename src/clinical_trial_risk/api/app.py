"""Local, read-only research demo. No arbitrary model upload or database credentials."""
import json,re,time
from collections import deque
from pathlib import Path
import numpy as np
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import HTMLResponse,PlainTextResponse,JSONResponse
from clinical_trial_risk.data.cohort import ROOT
from clinical_trial_risk.reporting.packets import runtime,template
from clinical_trial_risk.api.extraction import router as extraction_router

API_VERSION='0.3.0'
app=FastAPI(title='Clinical Trial Research Explorer',version=API_VERSION,
    description='Read-only historical trial reports, saved V3 extraction comparisons and AI secondary review. All research endpoints serve recorded results.')
app.include_router(extraction_router)
latencies=deque(maxlen=1000);counts={'requests':0,'errors':0}

@app.middleware('http')
async def observe(request,call_next):
    start=time.perf_counter();counts['requests']+=1
    try:
        response=await call_next(request)
        if response.status_code>=500:counts['errors']+=1
        return response
    except Exception:
        counts['errors']+=1;raise
    finally:latencies.append(time.perf_counter()-start)

@app.get('/',response_class=HTMLResponse)
def index():return (Path(__file__).parent/'index.html').read_text()

@app.get('/health')
def health():
    try:runtime()
    except (FileNotFoundError,ValueError):
        return JSONResponse(status_code=503,content={'status':'missing_or_invalid_research_artifacts','scope':'local retrospective research'})
    return {'status':'ready','scope':'local retrospective research'}

@app.get('/portfolio')
def portfolio(limit:int=Query(50,ge=1,le=1000)):
    r=runtime();return {'scope':r.universe,'total':len(r.ids),'trials':r.portfolio()[:limit]}

@app.get('/trials/{nct_id}/report')
def report(nct_id:str):
    if not re.fullmatch(r'NCT\d{8}',nct_id):raise HTTPException(422,'Use a valid NCT identifier')
    try:packet=runtime().packet(nct_id)
    except KeyError:raise HTTPException(404,'Trial is outside this research portfolio')
    return {'packet':packet,'report_markdown':template(packet),
        'extraction_provenance':{'serving':'cached_original_cohort_spans',
            'v3_applied_to_this_trial':False,'latest_benchmark_url':'/extraction/evaluation'}}

@app.get('/evaluation')
def evaluation():return json.loads((ROOT/'reports/evaluation/holdout.json').read_text())

@app.get('/monitoring')
def monitoring():
    return {**counts,'api_version':API_VERSION,'latency_seconds_p50':float(np.quantile(latencies,.5)) if latencies else None,
        'latency_seconds_p95':float(np.quantile(latencies,.95)) if latencies else None,
        'stored_request_bodies':False,'stored_trial_identifiers':False,
        'generation_mode':'deterministic; experimental LLM generation is not served',
        'extraction_research_mode':'saved benchmark results and AI secondary review'}
