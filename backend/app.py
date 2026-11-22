import asyncio,json,os,secrets,subprocess,sys,shutil,zipfile,io,html
import threading,functools
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any,Literal
import pandas as pd
import numpy as np
from fastapi import FastAPI,UploadFile,File,Request,HTTPException,Query
from fastapi.responses import JSONResponse,FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel,Field,ConfigDict
from . import storage as db
from . import service
from .statistics import evaluate
from scipy.special import expit
from .schemas import AnalysisResult

TOKEN=secrets.token_urlsafe(32)
ORIGINS=os.environ.get('MULTIVARIAT_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',')
PROCESS=None
MUTATION_LOCK=threading.RLock()
def synchronized(fn):
    @functools.wraps(fn)
    def wrapped(*args,**kwargs):
        with MUTATION_LOCK:return fn(*args,**kwargs)
    return wrapped

def stop_process(p):
    if p and p.poll() is None:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)
        else:p.kill()

async def scheduler():
    global PROCESS
    while True:
        jobs=list(reversed(db.listing('run')))
        for job in jobs:
            if job['status']!='queued':continue
            try:
                if db.get(job['id'])['status']!='queued':continue
            except KeyError:continue
            PROCESS=subprocess.Popen([sys.executable,'-m','backend.worker',job['id']],cwd=db.ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            started=asyncio.get_running_loop().time()
            while PROCESS.poll() is None:
                await asyncio.sleep(.2)
                current=db.get(job['id'])
                if current['status']=='cancelled':stop_process(PROCESS)
                elif asyncio.get_running_loop().time()-started>300:
                    stop_process(PROCESS);current.update(status='failed',error=dict(code='TIMEOUT',message='Batas 300 detik terlampaui.',retryable=True));db.put('run',current)
            PROCESS=None
            db.transition(job['id'],['running'],dict(status='failed',error=dict(code='WORKER_EXIT',message='Proses analisis berhenti sebelum menghasilkan hasil lengkap.',retryable=True)))
        await asyncio.sleep(.2)

@asynccontextmanager
async def lifespan(app):
    for kind in ('run','job'):
        for job in db.listing(kind):
            if job['status'] in ('running','queued'):job.update(status='failed',error=dict(code='INTERRUPTED',message='Server sebelumnya berhenti.',retryable=True));db.put(kind,job)
    task=asyncio.create_task(scheduler())
    yield
    task.cancel();stop_process(PROCESS)

app=FastAPI(title='Multivariat Lab API',version='1.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=['*'],allow_headers=['Content-Type','X-Session-Token'])

def error(code,message,status=422):return JSONResponse(dict(error=dict(code=code,message=message,field_errors=[],request_id=db.uid(),retryable=False)),status_code=status)
@app.middleware('http')
async def local_security(request,call_next):
    origin=request.headers.get('origin')
    host=request.headers.get('host','').split(':')[0]
    if host not in ('localhost','127.0.0.1','testserver'):return error('HOST_DENIED','Host tidak diizinkan.',403)
    if origin and origin not in ORIGINS:return error('ORIGIN_DENIED','Origin tidak diizinkan.',403)
    if origin and request.method not in ('GET','HEAD','OPTIONS') and request.headers.get('x-session-token')!=TOKEN:return error('SESSION_REQUIRED','Token sesi lokal diperlukan.',403)
    try:length=int(request.headers.get('content-length','0'))
    except ValueError:return error('INVALID_LENGTH','Content length tidak valid.',400)
    if length>51*1024**2:return error('FILE_TOO_LARGE','Batas upload 50 MiB.',413)
    return await call_next(request)
@app.exception_handler(KeyError)
async def missing(req,exc):return error('NOT_FOUND','Data tidak ditemukan.',404)
@app.exception_handler(ValueError)
async def invalid(req,exc):return error('INVALID_INPUT',str(exc))
@app.exception_handler(RequestValidationError)
async def invalid_schema(req,exc):return error('INVALID_SCHEMA','Bentuk request tidak sesuai schema.')
@app.exception_handler(HTTPException)
async def http_error(req,exc):return error('REQUEST_FAILED',str(exc.detail),exc.status_code)
@app.exception_handler(zipfile.BadZipFile)
async def bad_archive(req,exc):return error('INVALID_ARCHIVE','Arsip dokumen atau workbook rusak. Unggah berkas yang valid.')
@app.exception_handler(Exception)
async def unexpected(req,exc):return error('INTERNAL_ERROR','Permintaan gagal diproses. Periksa berkas dan konfigurasi, lalu coba lagi.',500)

class ProjectInput(BaseModel):
    name:str=Field(min_length=1,max_length=200)
    description:str=''
class DraftInput(BaseModel):
    dataset_version_id:str
    purpose:str=''
    method:Literal['lda','pca','efa','kmeans','hierarchical']
    feature_ids:list[str]
    target_id:str|None=None
    positive_label:Any=None
    preprocessing:dict=Field(default_factory=dict)
    split:dict=Field(default_factory=dict)
    settings:dict=Field(default_factory=dict)
    analysis_options:dict=Field(default_factory=dict)
class RunInput(BaseModel):
    draft_id:str
    revision:int
    idempotency_key:str
class RevisionInput(BaseModel):
    expected_revision:int
    patch:dict
class ScenarioInput(BaseModel):
    kind:Literal['threshold_simulation','equal_prior','oof_threshold']
    threshold:float=Field(default=.5,ge=0,le=1)
    idempotency_key:str
    subset:str='test'

def page(items,offset=0,limit=50):return dict(items=items[offset:offset+limit],total=len(items),offset=offset,limit=limit)
def read_bundle(id):return json.loads((db.folder(id)/'result.json').read_text(encoding='utf-8'))
def read_raw(id):return json.loads((db.folder(id)/'raw.json').read_text(encoding='utf-8'))
def require_result(id):
    run=db.get(id,'run')
    if run['status']!='succeeded':raise HTTPException(409,'Hasil belum tersedia.')
    return run
def public(obj):return {k:v for k,v in obj.items() if k not in ('path',)}
def artifact(path,project_id,kind):
    id=db.uid();data=path.read_bytes()
    return db.put('artifact',dict(id=id,project_id=project_id,kind=kind,path=str(path),mime_type={'.json':'application/json','.pdf':'application/pdf','.csv':'text/csv','.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.zip':'application/zip','.svg':'image/svg+xml','.png':'image/png'}.get(path.suffix,'application/octet-stream'),size_bytes=len(data),sha256=db.digest(data),download_url=f'/api/v1/artifacts/{id}/download'))

@app.get('/api/v1/health')
def health():
    from .assistant import configured
    return dict(status='ok',python=sys.version.split()[0],statistical_engine='python',efa_engine='statsmodels',database=True,exporter=dict(pdf=True,table=True,plotly=True),ai_configured=configured(),session_token=TOKEN)
@app.get('/api/v1/capabilities')
def capabilities():
    from .assistant import configured
    return dict(schema_version='1.0.0',methods={m:dict(available=True) for m in service.METHODS},limits=dict(file_bytes=50*1024**2,rows=100000,columns=200,hierarchical_rows=3000,silhouette_sample=2000),defaults=dict(seed=42,test_size=.3,prior='empirical',threshold=.5,k=3,basis='correlation'),features=dict(ai=configured(),ocr=False,group_temporal_oof=True))
@app.get('/api/v1/projects')
def projects(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200)):return page(db.listing('project'),offset,limit)
@app.post('/api/v1/projects')
def create_project(body:ProjectInput):return db.put('project',dict(id=db.uid(),**body.model_dump(),case_type='custom',created_at=db.now(),updated_at=db.now()))
@app.get('/api/v1/projects/{id}')
def project(id:str):return db.get(id,'project')
@app.patch('/api/v1/projects/{id}')
def update_project(id:str,body:ProjectInput):
    obj=db.get(id,'project');obj.update(body.model_dump(),updated_at=db.now());return db.put('project',obj)
@app.delete('/api/v1/projects/{id}')
@synchronized
def delete_project(id:str):
    db.get(id,'project')
    for kind in ('deckplan','autoplan','suite','run','draft','dataset','import','document','snapshot','scenario','artifact','job'):
        for obj in db.listing(kind,id):
            if kind in ('run','job') and obj['status'] in ('running','queued'):raise HTTPException(409,'Tunggu atau batalkan pekerjaan aktif sebelum menghapus proyek.')
    for kind in ('deckplan','autoplan','suite','run','draft','dataset','import','document','snapshot','scenario','artifact','job'):
        for obj in db.listing(kind,id):
            shutil.rmtree(db.folder(obj['id']),ignore_errors=True);db.remove(obj['id'])
    db.remove(id);return dict(deleted=True)
@app.post('/api/v1/projects/{id}/imports')
async def upload(id:str,file:UploadFile=File(...)):
    db.get(id,'project');data=await file.read(50*1024**2+1)
    inspection=service.inspect_upload(data,file.filename or '')
    iid=db.uid();path=db.folder(iid)/('source'+Path(file.filename).suffix.lower());path.write_bytes(data)
    obj=db.put('import',dict(id=iid,project_id=id,filename=Path(file.filename).name,path=str(path),inspection=inspection))
    return dict(import_id=iid,inspection=obj['inspection'])
@app.post('/api/v1/imports/{id}/confirm')
def confirm(id:str,options:dict):return public(service.import_confirm(db.get(id,'import'),options))
@app.get('/api/v1/datasets/{id}/profile')
def profile(id:str):return service.profile(db.get(id,'dataset'))
@app.get('/api/v1/datasets/{id}/rows')
def rows(id:str,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),column_ids:str|None=None,sort:str|None=None):
    frame=service.dataframe(db.get(id,'dataset'))
    if sort:frame=frame.sort_values(sort,kind='stable')
    if column_ids:frame=frame[['_row_id','_source_row']+column_ids.split(',')]
    return dict(items=db.clean(frame.iloc[offset:offset+limit].to_dict('records')),total=len(frame),offset=offset,limit=limit)
@app.post('/api/v1/projects/{id}/drafts')
def draft(id:str,body:DraftInput):
    db.get(id,'project');dataset=db.get(body.dataset_version_id,'dataset')
    if dataset['project_id']!=id:raise ValueError('Dataset bukan milik proyek ini.')
    return db.put('draft',dict(id=db.uid(),project_id=id,revision=1,**body.model_dump()))
@app.get('/api/v1/drafts/{id}')
def get_draft(id:str):return db.get(id,'draft')
@app.patch('/api/v1/drafts/{id}')
@synchronized
def patch_draft(id:str,body:RevisionInput):
    obj=db.get(id,'draft')
    if obj['revision']!=body.expected_revision:raise HTTPException(409,'Revision berubah.')
    updated=DraftInput.model_validate({**obj,**body.patch}).model_dump()
    if db.get(updated['dataset_version_id'],'dataset')['project_id']!=obj['project_id']:raise ValueError('Dataset tidak sesuai proyek.')
    obj.update(updated,revision=obj['revision']+1);return db.put('draft',obj)
@app.post('/api/v1/drafts/{id}/validate')
def validate(id:str):return service.validate(db.get(id,'draft'))
@app.post('/api/v1/drafts/{id}/validate-suite')
def validate_suite(id:str):
    from .suites import plan
    return plan(db.get(id,'draft'))

@app.post('/api/v1/analysis-suites',status_code=202)
@synchronized
def start_suite(body:RunInput):
    from .suites import plan,view
    cfg=db.get(body.draft_id,'draft')
    for old in db.listing('suite',cfg['project_id']):
        if old['idempotency_key']==body.idempotency_key:
            if old['request']!=body.model_dump():raise HTTPException(409,'Kunci idempotency berbeda payload.')
            return view(old)
    if cfg['revision']!=body.revision:raise HTTPException(409,'Revision berubah.')
    checked=plan(cfg);items=[]
    for item in checked['analyses']:
        if item['blocking']:
            items.append(dict(method=item['method'],status='blocked',blocking=item['blocking'],warnings=item['warnings']));continue
        child=draft(cfg['project_id'],DraftInput(**item['config']))
        r=start(RunInput(draft_id=child['id'],revision=child['revision'],idempotency_key=body.idempotency_key+':'+item['method']))
        items.append(dict(method=item['method'],status='queued',run_id=r['run_id'],warnings=item['warnings']))
    obj=db.put('suite',dict(id=db.uid(),project_id=cfg['project_id'],draft_id=cfg['id'],created_at=db.now(),idempotency_key=body.idempotency_key,request=body.model_dump(),analyses=items))
    return view(obj)

@app.get('/api/v1/analysis-suites/{id}')
def get_suite(id:str):
    from .suites import view
    return view(db.get(id,'suite'))

@app.get('/api/v1/projects/{id}/analysis-suites')
def suites(id:str):
    from .suites import view
    return page([view(s) for s in db.listing('suite',id)])

@app.post('/api/v1/projects/{id}/automatic-plan')
def automatic_plan(id:str,body:dict):
    from .automatic import create_plan
    d=db.get(body['dataset_version_id'],'dataset')
    if d['project_id']!=id:raise ValueError('Dataset bukan milik proyek ini.')
    return create_plan(d['id'])

@app.get('/api/v1/automatic-plans/{id}')
def get_automatic_plan(id:str):return db.get(id,'autoplan')

@app.post('/api/v1/automatic-plans/{id}/start',status_code=202)
@synchronized
def start_automatic(id:str,body:dict):
    from .suites import view
    plan=db.get(id,'autoplan');key=body.get('idempotency_key')
    if not isinstance(key,str) or not key:raise ValueError('Kunci pengiriman diperlukan.')
    for old in db.listing('suite',plan['project_id']):
        if old.get('automatic_plan_id')==id and old['idempotency_key']==key:return view(old)
    items=[]
    for a in plan['analyses']:
        if a['status']=='explained':items.append({k:v for k,v in a.items() if k!='config'});continue
        child=draft(plan['project_id'],DraftInput(**a['config']))
        result=start(RunInput(draft_id=child['id'],revision=1,idempotency_key=id+':'+key+':'+a['method']))
        items.append(dict(method=a['method'],title=a['title'],question=a['question'],explanation=a['explanation'],decisions=a['decisions'],run_id=result['run_id'],status='queued'))
    suite=db.put('suite',dict(id=db.uid(),project_id=plan['project_id'],automatic_plan_id=id,created_at=db.now(),analyses=items,idempotency_key=key))
    return view(suite)

@app.get('/api/v1/analysis-suites/{id}/presentation')
def automatic_presentation(id:str):
    from .automatic import coverage_sections
    from .suites import view
    suite=view(db.get(id,'suite'));sections=[]
    if suite.get('automatic_plan_id'):
        plan=db.get(suite['automatic_plan_id'],'autoplan');sections.extend(coverage_sections(suite,plan))
    for rid in suite['successful_run_ids']:sections.extend(presentation_sections(rid)['sections'])
    return dict(suite_id=id,sections=sections)
@app.post('/api/v1/runs',status_code=202)
@synchronized
def start(body:RunInput):
    cfg=db.get(body.draft_id,'draft')
    for old in db.listing('run',cfg['project_id']):
        if old.get('idempotency_key')==body.idempotency_key:
            if old['request']!=body.model_dump():raise HTTPException(409,'Kunci idempotency berbeda payload.')
            return dict(run_id=old['id'],job_id=old['id'])
    if cfg['revision']!=body.revision:raise HTTPException(409,'Revision berubah.')
    plan=service.validate(cfg)
    if plan['blocking']:raise ValueError(plan['blocking'][0]['message'])
    id=db.uid();db.put('run',dict(id=id,project_id=cfg['project_id'],config=cfg,config_hash=db.digest(db.dumps(cfg).encode()),draft_revision=cfg['revision'],dataset_version_id=cfg['dataset_version_id'],status='queued',phase='validating',progress=None,created_at=db.now(),error=None,idempotency_key=body.idempotency_key,request=body.model_dump()))
    return dict(run_id=id,job_id=id)
@app.get('/api/v1/runs/{id}')
def run(id:str):return db.get(id,'run')
@app.post('/api/v1/runs/{id}/cancel')
def cancel(id:str):
    db.get(id,'run')
    db.transition(id,['queued','running'],dict(status='cancelled',finished_at=db.now()))
    return db.get(id,'run')
@app.get('/api/v1/projects/{id}/runs')
def history(id:str):return page(db.listing('run',id))
@app.get('/api/v1/runs/{id}/results',response_model=AnalysisResult)
def results(id:str):require_result(id);return read_bundle(id)['result']
@app.get('/api/v1/runs/{id}/tables/{table_id}')
def table(id:str,table_id:str,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200)):
    require_result(id);t=read_bundle(id)['tables'][table_id];return {**{k:v for k,v in t.items() if k!='rows'},**page(t['rows'],offset,limit)}
@app.get('/api/v1/runs/{id}/visuals/{visual_id}')
def visual(id:str,visual_id:str):require_result(id);return read_bundle(id)['visuals'][visual_id]
@app.get('/api/v1/runs/{id}/observations/{row_id}')
def observation(id:str,row_id:str):
    r=require_result(id);raw=read_raw(id);frame=json.loads((db.folder(id)/'frame.json').read_text(encoding='utf-8'))
    i=next((i for i,v in enumerate(frame) if v['_row_id']==row_id),None)
    if i is None:raise KeyError(row_id)
    output=dict(row_id=row_id,source=frame[i],run_id=id)
    if r['config']['method']=='lda':
        m=raw['model'];coeff=np.array(m['b'][1])-m['b'][0];x=np.array(raw['transformed'][i]);eta=raw['eta'][i]
        output.update(transformed=x,contributions=x*coeff,coefficients=coeff,constant=m['c'][1]-m['c'][0],eta=eta,posterior=raw['probability'][i],canonical_score=raw['canonical_scores'][i],prediction=int(raw['probability'][i]>=r['config']['settings'].get('threshold',.5)),formula='p1=expit(sum(contributions)+constant)')
    elif r['config']['method'] in ('pca','efa'):
        output['scores']=raw['scores'][i]
    else:
        group=int(raw['labels'][i]);output.update(cluster=group+1,centroid=raw['centroids'][group])
    return db.clean(output)
@app.post('/api/v1/runs/{id}/scenarios')
@synchronized
def scenario(id:str,body:ScenarioInput):
    r=require_result(id)
    if r['config']['method']!='lda':raise ValueError('Skenario hanya untuk LDA.')
    if body.subset not in ('train','test'):raise ValueError('Subset tidak sah.')
    for old in db.listing('scenario',r['project_id']):
        if old.get('parent_run_id')==id and old.get('idempotency_key')==body.idempotency_key:
            if old['request']!=body.model_dump():raise HTTPException(409,'Payload berubah.')
            return old
    raw=read_raw(id);indices=np.array(raw[body.subset]);p=np.array(raw['probability']);threshold=body.threshold
    if body.kind=='equal_prior':p=expit(np.array(raw['eta'])-np.log(raw['model']['priors'][1]/raw['model']['priors'][0]))
    if body.kind=='oof_threshold':
        if raw['oof_threshold'] is None:raise HTTPException(409,'Duplikasi draft dan aktifkan OOF untuk menghitung ambang dari train.')
        threshold=raw['oof_threshold']
    return db.put('scenario',dict(id=db.uid(),project_id=r['project_id'],parent_run_id=id,status='succeeded',kind=body.kind,evaluation_subset_id=body.subset,settings=body.model_dump(),idempotency_key=body.idempotency_key,request=body.model_dump(),result=db.clean(evaluate(np.array(raw['y'])[indices],p[indices],threshold,body.subset)),simulation_only=body.kind=='threshold_simulation'))
@app.get('/api/v1/scenarios/{id}')
def get_scenario(id:str):return db.get(id,'scenario')
@app.post('/api/v1/projects/{id}/case-study')
def case(id:str):
    project=db.get(id,'project');source=db.ROOT/'outputs/makalah_multivariat/Data_Analisis.csv'
    iid=db.uid();path=db.folder(iid)/'case.csv';shutil.copyfile(source,path)
    imp=dict(id=iid,project_id=id,path=str(path),filename='Data_Analisis.csv',inspection=dict(delimiter=','));db.put('import',imp)
    dataset=service.import_confirm(imp,dict(decimal='.',header_row=1));f=service.dataframe(dataset)
    mapping={c['source_name']:c['id'] for c in dataset['columns']};features=[mapping[k] for k in ['WC_TA','RE_TA','ROA_A','EQ_LIAB','TURNOVER']]
    # Human-readable case IDs are preserved as row keys.
    f['_row_id']=f[mapping['ID']];db.write_json(Path(dataset['path']),f.to_dict('records'))
    project.update(case_type='taiwan_paper');db.put('project',project)
    ids=[]
    for method in ('lda','pca'):
        obj=dict(dataset_version_id=dataset['id'],purpose='Reproduksi makalah' if method=='lda' else 'Ilustrasi PCA train',method=method,feature_ids=features,target_id=mapping['bankrupt'] if method=='lda' else None,positive_label=1 if method=='lda' else None,preprocessing=dict(missing='error',scale='none'),split=dict(mode='saved_membership',column_id=mapping['train'],seed=42,reconstruct_order=True),settings=dict(oof=True,oof_estimator='pooled') if method=='lda' else dict(subset='train',basis='correlation'))
        ids.append(draft(id,DraftInput(**obj))['id'])
    return dict(dataset_id=dataset['id'],draft_ids=ids,columns=dataset['columns'])

@app.post('/api/v1/projects/{id}/documents')
async def document_upload(id:str,file:UploadFile=File(...)):
    from .documents import extract
    db.get(id,'project');name=file.filename or ''
    if Path(name).suffix.lower() not in ('.docx','.pdf'):raise ValueError('Dokumen harus DOCX atau PDF.')
    data=await file.read(20*1024**2+1);service.inspect_upload(data,name,True)
    extracted=await asyncio.to_thread(extract,data,name);did=db.uid();path=db.folder(did)/('source'+Path(name).suffix.lower());path.write_bytes(data)
    return public(db.put('document',dict(id=did,project_id=id,filename=Path(name).name,path=str(path),sha256=db.digest(data),**extracted)))
@app.get('/api/v1/documents/{id}')
def document(id:str):return public(db.get(id,'document'))
@app.post('/api/v1/documents/{id}/analysis-proposal')
def proposal(id:str):
    obj=db.get(id,'document');text=' '.join(c['text'] for c in obj['chunks']).lower()
    methods=[m for m,words in dict(lda=['diskriminan','discriminant'],pca=['komponen utama','principal component'],efa=['analisis faktor','factor analysis'],kmeans=['k-means']).items() if any(w in text for w in words)]
    return dict(status='review_required',candidate_methods=methods,proposed_config=None,evidence=[c['id'] for c in obj['chunks'] if any(w in c['text'].lower() for w in ['diskriminan','komponen utama','factor','k-means'])][:8],message='Metode terdeteksi sebagai kandidat; variabel dan parameter harus dipetakan serta divalidasi pengguna.')
@app.post('/api/v1/projects/{id}/assistant')
def assistant(id:str,body:dict):
    from .documents import retrieve
    db.get(id,'project');evidence=[];answer=[]
    if body.get('run_id'):
        r=require_result(body['run_id'])
        if r['project_id']!=id:raise ValueError('Run bukan milik proyek.')
        blocks=read_bundle(r['id'])['result']['narrative_blocks'];answer.extend(b['text'] for b in blocks);evidence.extend(b['id'] for b in blocks)
    chunks=[]
    for did in body.get('allowed_document_ids',[]):
        doc=db.get(did,'document')
        if doc['project_id']!=id:raise ValueError('Dokumen bukan milik proyek.')
        chunks.extend(dict(c,id=did+':'+c['id']) for c in doc['chunks'])
    matches=retrieve(chunks,body.get('question',''))
    from .assistant import select_evidence,configured
    selection=dict(status='not_requested',selected_ids=[])
    if body.get('send_policy')=='summary_and_quotes':
        selection=select_evidence(body.get('question',''),[dict(id=m['id'],text=m['text'][:5000]) for m in matches])
        if selection['selected_ids']:matches=[m for m in matches if m['id'] in selection['selected_ids']]
    return dict(status='grounded_evidence',answer=' '.join(answer) or 'Kutipan sumber relevan tersedia pada document_evidence.',evidence_ids=evidence,document_evidence=matches,origin='deterministic',ai_selection=selection,ai_available=configured(),message='AI hanya memilih bukti; angka dan kutipan yang diterbitkan berasal langsung dari hasil dan dokumen.')
@app.post('/api/v1/projects/{id}/presentation-plan')
def presentation_plan(id:str,body:dict):
    from .presentation_plan import create_plan
    from .automatic import coverage_sections
    from .suites import view
    db.get(id,'project');run_ids=body.get('run_ids',[]);records=[];assessments=[];sid=body.get('automatic_suite_id')
    if not isinstance(run_ids,list) or len(run_ids)!=len(set(run_ids)):raise ValueError('Run presentasi harus unik.')
    if sid:
        suite=view(db.get(sid,'suite'))
        if suite['project_id']!=id or not suite.get('automatic_plan_id'):raise ValueError('Laporan otomatis bukan milik proyek ini.')
        if not set(run_ids)<=set(suite['successful_run_ids']):raise ValueError('Run bukan hasil laporan otomatis yang dipilih.')
        assessments=coverage_sections(suite,db.get(suite['automatic_plan_id'],'autoplan'))
    for rid in run_ids:
        run=require_result(rid)
        if run['project_id']!=id:raise ValueError('Run bukan milik proyek ini.')
        frame=pd.DataFrame(json.loads((db.folder(rid)/'frame.json').read_text(encoding='utf-8')))
        records.append(dict(run=run,bundle=read_bundle(rid),raw=read_raw(rid),frame=frame,report_sections=presentation_sections(rid)['sections']))
    if not records and not assessments:raise ValueError('Belum ada hasil atau keterangan kelayakan untuk presentasi.')
    return create_plan(id,records,assessments,sid)

@app.post('/api/v1/projects/{id}/snapshots')
def snapshot(id:str,body:dict):
    db.get(id,'project');runs=[]
    body={**body,'run_ids':body.get('run_ids',[])}
    automatic=None
    if body.get('automatic_suite_id'):
        from .suites import view
        automatic=view(db.get(body['automatic_suite_id'],'suite'))
        if automatic['project_id']!=id or not automatic.get('automatic_plan_id'):raise ValueError('Laporan otomatis bukan milik proyek ini.')
        if not set(body.get('run_ids',[]))<=set(automatic['successful_run_ids']):raise ValueError('Run bukan hasil penelaahan otomatis yang dipilih.')
    if len(body.get('run_ids',[]))!=len(set(body.get('run_ids',[]))):raise ValueError('Run snapshot harus unik.')
    for rid in body.get('run_ids',[]):
        r=require_result(rid)
        if r['project_id']!=id:raise ValueError('Run bukan milik proyek.')
        bundle=read_bundle(rid)
        from .charts import figure
        for v in bundle['result']['visual_manifest']:
            if v['status'] in ('shown','available') and v['kind'] not in ('confusion_matrix','heatmap'):
                bundle['visuals'][v['id']]['figure']=json.loads(figure(bundle,v['id']).to_json())
        runs.append(bundle)
    if not runs and not automatic:raise ValueError('Pilih minimal satu run selesai.')
    scenarios=[]
    for sid in body.get('scenario_ids',[]):
        scenario=db.get(sid,'scenario')
        if scenario['project_id']!=id or scenario['parent_run_id'] not in body['run_ids']:raise ValueError('Skenario tidak sesuai run/proyek snapshot.')
        scenarios.append(scenario)
    canonical={s['id']:s for rid in body['run_ids'] for s in presentation_sections(rid)['sections']}
    deck=None
    if body.get('presentation_plan_id'):
        deck=db.get(body['presentation_plan_id'],'deckplan')
        if deck['project_id']!=id or set(deck['run_ids'])!=set(body['run_ids']) or deck.get('automatic_suite_id')!=body.get('automatic_suite_id'):raise ValueError('Rencana presentasi tidak sesuai proyek, run, atau laporan yang dipilih.')
        canonical={s['id']:s for s in deck['sections']}
    if automatic and not deck:
        from .automatic import coverage_sections
        canonical.update({s['id']:s for s in coverage_sections(automatic,db.get(automatic['automatic_plan_id'],'autoplan'))})
    sections=[]
    for section in body.get('ordered_sections',[]):
        if deck:
            original=canonical.get(section.get('id'))
            if not original:raise ValueError('Bagian tidak berasal dari rencana presentasi ini.')
            title=section.get('title',original['title'])
            if not isinstance(title,str) or not title.strip() or len(title)>500:raise ValueError('Judul slide harus berupa teks 1–500 karakter.')
            sections.append({**original,'title':title,'enabled':True})
            continue
        if section.get('kind')=='content':
            if section.get('id') not in canonical:raise ValueError('Bagian presentasi tidak berasal dari run yang dipilih.')
            sections.append({**canonical[section['id']],'title':section.get('title',canonical[section['id']]['title'])})
        else:
            if section.get('kind') not in ('intro','methods','visual','limits','summary'):raise ValueError('Jenis bagian presentasi tidak sah.')
            if section.get('run_id') and section['run_id'] not in body['run_ids']:raise ValueError('Run bagian presentasi tidak sesuai snapshot.')
            if section.get('kind') not in ('intro','methods') and not section.get('run_id'):raise ValueError('Bagian hasil harus merujuk run.')
            if section.get('kind')=='visual':
                target=next(b for b in runs if b['result']['run_id']==section['run_id'])
                if not any(v['id']==section.get('visual_id') and v['status'] in ('shown','available') for v in target['result']['visual_manifest']):raise ValueError('Grafik tidak tersedia pada run yang dipilih.')
            sections.append(section)
    if not sections and deck:raise ValueError('Pilih sedikitnya satu slide presentasi.')
    if len({s['id'] for s in sections})!=len(sections):raise ValueError('Bagian presentasi harus unik.')
    if not runs and not any(s.get('suite_id') for s in sections):raise ValueError('Pilih sedikitnya satu penjelasan untuk laporan ini.')
    hashes=list(dict.fromkeys([b['result']['provenance']['source_sha256'] for b in runs]+[s['source_sha256'] for s in sections if s.get('source_sha256')]))
    return db.put('snapshot',dict(id=db.uid(),project_id=id,run_ids=body['run_ids'],automatic_suite_id=body.get('automatic_suite_id'),presentation_plan_id=body.get('presentation_plan_id'),scenario_ids=body.get('scenario_ids',[]),ordered_sections=sections,speaker_notes=body.get('speaker_notes',{}),created_at=db.now(),bundles=runs,scenarios=scenarios,source_hashes=hashes))
@app.get('/api/v1/snapshots/{id}')
def get_snapshot(id:str):return db.get(id,'snapshot')

def export_work(job):
    try:
        body=job['request'];fmt=body['format'];path=db.folder(job['id'])/('analysis.'+fmt)
        if body.get('run_id'):
            r=require_result(body['run_id']);bundle=read_bundle(r['id']);project_id=r['project_id']
        else:
            snap=db.get(body['snapshot_id'],'snapshot');project_id=snap['project_id'];r=None
            assessment_rows=[dict(question=s['title'],explanation=' '.join(s.get('paragraphs',[]))) for s in snap['ordered_sections'] if s.get('suite_id')]
            bundle=json.loads(db.dumps(snap['bundles'][0])) if snap['bundles'] else dict(result=dict(narrative_blocks=[],metrics=[],visual_manifest=[],provenance={}),tables=dict(assessments=dict(rows=assessment_rows)),visuals={})
            if assessment_rows:bundle['tables']['assessments']=dict(rows=assessment_rows)
            for index,extra in enumerate(snap['bundles'][1:],start=1):
                bundle['result']['narrative_blocks'].extend(extra['result']['narrative_blocks'])
                bundle['result']['metrics'].extend(extra['result']['metrics'])
                for key,value in extra['tables'].items():bundle['tables'][str(index)+'_'+key]=value
                for v in extra['result']['visual_manifest']:
                    key=str(index)+'_'+v['id'];bundle['visuals'][key]=extra['visuals'][v['id']];v=dict(v,id=key);bundle['result']['visual_manifest'].append(v)
            for scenario in snap['scenarios']:
                bundle['result']['narrative_blocks'].append(dict(text=f"Skenario {scenario['kind']}: {db.dumps(scenario['result']['counts'])}"))
        if fmt=='json':db.write_json(path,bundle if r else snap)
        elif fmt in ('csv','xlsx'):
            def safe(v):return "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v
            tables=bundle['tables'];selected=body.get('table_id') or next(iter(tables))
            if not r and not body.get('table_id'):
                tables['snapshot_metrics']=dict(rows=[dict(run_id=b['result']['run_id'],method=b['result']['method'],**m) for b in snap['bundles'] for m in b['result']['metrics']]);selected='snapshot_metrics' if snap['bundles'] else 'assessments'
            def flatten(rows):
                out=[]
                for row_index,row in enumerate(rows):
                    if any(isinstance(v,(list,dict)) for v in row.values()):
                        for key,value in row.items():
                            text=db.dumps(value) if isinstance(value,(list,dict)) else str(value)
                            for i in range(0,max(len(text),1),30000):out.append(dict(row_index=row_index,field=key,part=i//30000+1,value=safe(text[i:i+30000])))
                    else:out.append({k:safe(v) for k,v in row.items()})
                return out
            if fmt=='csv':pd.DataFrame(tables[selected]['rows']).map(safe).to_csv(path,index=False,encoding='utf-8-sig')
            else:
                with pd.ExcelWriter(path,engine='openpyxl') as writer:
                    manifest=[]
                    for i,(name,t) in enumerate(tables.items()):
                        sheet=(str(i)+'_'+name)[:31]
                        pd.DataFrame(flatten(t['rows'])).to_excel(writer,sheet_name=sheet,index=False)
                        owner=r['id'] if r else next((b['result']['run_id'] for j,b in enumerate(snap['bundles']) if name in b['tables'] and j==0 or j>0 and name.startswith(str(j)+'_') and name[len(str(j))+1:] in b['tables']),'all')
                        manifest.append(dict(sheet=sheet,run_id=owner,table_id=t.get('id',name)))
                    pd.DataFrame(manifest).to_excel(writer,sheet_name='table_manifest',index=False)
                    sources=[bundle] if r else snap['bundles']
                    provenance=[]
                    for b in sources:
                        for k,v in b['result']['provenance'].items():
                            value=db.dumps(v)
                            for part in range(0,max(len(value),1),30000):provenance.append(dict(run_id=b['result']['run_id'],key=k,part=part//30000+1,value=value[part:part+30000]))
                    pd.DataFrame(provenance).to_excel(writer,sheet_name='provenance',index=False)
        elif fmt in ('png','svg'):
            from .charts import figure
            figure(bundle,body['visual_id']).write_image(str(path))
        elif fmt=='pdf':
            from .pdf_report import write_report
            if r:
                sections=presentation_sections(r['id'])['sections'];bundles=[bundle]
            else:
                sections=snap['ordered_sections'] or [dict(kind='summary',title='Hasil analisis',run_id=v['result']['run_id']) for v in snap['bundles']];bundles=snap['bundles']
            write_report(path,bundles,sections,r['id'] if r else snap['id'])
        elif fmt=='zip':
            if not r:raise ValueError('Paket reproduksi memerlukan run_id.')
            ds=db.get(r['dataset_version_id'],'dataset')
            files={'config.json':db.dumps(r['config']).encode(),'versions.json':db.dumps(r['provenance']).encode(),'results.json':db.dumps(bundle).encode(),'dataset.json':Path(ds['path']).read_bytes(),'raw.json':(db.folder(r['id'])/'raw.json').read_bytes(),'frame.json':(db.folder(r['id'])/'frame.json').read_bytes(),'README.txt':b'Use backend/README.md. Data and parameters are immutable; no secrets included.'}
            files['SHA256.json']=db.dumps({k:db.digest(v) for k,v in files.items()}).encode()
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
                for k,v in files.items():z.writestr(k,v)
        else:raise ValueError('Format belum tersedia; pilih json,csv,xlsx,pdf,zip.')
        a=artifact(path,project_id,fmt);job.update(status='succeeded',artifact_id=a['id'],artifact=public(a))
    except Exception as e:job.update(status='failed',error=dict(code='EXPORT_FAILED',message=str(e),retryable=False))
    db.put('job',job)
@app.post('/api/v1/exports',status_code=202)
async def export(body:dict):
    if body.get('format') not in ('json','csv','xlsx','pdf','zip','png','svg'):raise ValueError('Format ekspor tidak didukung.')
    if not body.get('idempotency_key'):raise ValueError('idempotency_key diperlukan.')
    if bool(body.get('run_id'))==bool(body.get('snapshot_id')):raise ValueError('Pilih tepat satu sumber ekspor: run atau snapshot.')
    if body['format'] in ('zip','png','svg') and not body.get('run_id'):raise ValueError('Format ini memerlukan satu run.')
    if body.get('run_id'):project_id=require_result(body['run_id'])['project_id']
    else:project_id=db.get(body['snapshot_id'],'snapshot')['project_id']
    for old in db.listing('job',project_id):
        if old.get('idempotency_key')==body['idempotency_key']:
            if old['request']!=body:raise HTTPException(409,'Payload berubah.')
            return dict(job_id=old['id'])
    job=db.put('job',dict(id=db.uid(),project_id=project_id,status='running',phase='exporting',progress=None,idempotency_key=body['idempotency_key'],request=body))
    asyncio.create_task(asyncio.to_thread(export_work,job));return dict(job_id=job['id'])
@app.get('/api/v1/jobs/{id}')
def get_job(id:str):
    try:return db.get(id,'job')
    except KeyError:return db.get(id,'run')

@app.patch('/api/v1/datasets/{id}/columns')
def update_columns(id:str,body:dict):
    source=db.get(id,'dataset');columns=source['columns'];updates=body.get('columns',[])
    roles={'feature','target','id','entity','time','ignored'}
    for update in updates:
        col=next((c for c in columns if c['id']==update['id']),None)
        if col is None or update.get('role',col['role']) not in roles:raise ValueError('Kolom atau peran tidak sah.')
        for key in ('role','unit','display_name'):
            if key in update:
                value=update[key]
                if key in ('unit','display_name') and not (value is None and key=='unit' or isinstance(value,str) and value.strip() and len(value)<=500):raise ValueError('Nama tampilan/satuan harus teks yang tidak kosong, maksimal 500 karakter.')
                col[key]=value
    # Mapping creates a new dataset version; old runs keep their original mapping.
    new_id=db.uid();path=db.folder(new_id)/'data.json';shutil.copyfile(source['path'],path)
    source.update(id=new_id,path=str(path),columns=columns,parent_version_id=id,created_at=db.now())
    return public(db.put('dataset',source))
@app.get('/api/v1/artifacts/{id}/download')
def download(id:str):
    a=db.get(id,'artifact');return FileResponse(a['path'],media_type=a['mime_type'],filename=Path(a['path']).name)

@app.get('/api/v1/projects/{id}/datasets')
def datasets(id:str):
    db.get(id,'project');return page([public(d) for d in db.listing('dataset',id)])

@app.get('/api/v1/datasets/{id}')
def dataset_detail(id:str):return public(db.get(id,'dataset'))

@app.get('/api/v1/projects/{id}/drafts')
def drafts(id:str):return page(db.listing('draft',id))

@app.get('/api/v1/projects/{id}/documents')
def document_list(id:str):return page([public(d) for d in db.listing('document',id)])

@app.get('/api/v1/projects/{id}/snapshots')
def snapshot_list(id:str):return page([{k:v for k,v in d.items() if k!='bundles'} for d in db.listing('snapshot',id)])

@app.get('/api/v1/imports/{id}')
def import_detail(id:str):return public(db.get(id,'import'))

@app.get('/api/v1/runs/{id}/visuals/{visual_id}/figure')
def visual_figure(id:str,visual_id:str):
    from .charts import figure
    require_result(id)
    return json.loads(figure(read_bundle(id),visual_id).to_json())

@app.get('/api/v1/datasets/{id}/columns/{column_id}/values')
def column_values(id:str,column_id:str):
    f=service.dataframe(db.get(id,'dataset'))
    if column_id not in f:raise ValueError('Kolom tidak tersedia.')
    values=f[column_id].dropna().unique().tolist()
    return dict(values=db.clean(values[:100]),total_unique=len(values),truncated=len(values)>100)

@app.get('/api/v1/runs/{id}/presentation')
def presentation_sections(id:str):
    from .presentation import sections_for_run
    run=require_result(id);frame=pd.DataFrame(json.loads((db.folder(id)/'frame.json').read_text(encoding='utf-8')))
    return dict(run_id=id,sections=sections_for_run(run,read_bundle(id),read_raw(id),frame))
