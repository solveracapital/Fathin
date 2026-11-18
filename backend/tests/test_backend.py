import os,tempfile,time,json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.statistics import *
from backend.app import app
from backend import storage as db

SOURCE=db.ROOT/'outputs/makalah_multivariat/Data_Analisis.csv'
FEATURES=['WC_TA','RE_TA','ROA_A','EQ_LIAB','TURNOVER']

@pytest.fixture(scope='module')
def taiwan():
    f=pd.read_csv(SOURCE);return f,lda_run(f,FEATURES,'bankrupt',1,{},dict(mode='saved_membership',column_id='train',seed=42,reconstruct_order=True),dict(oof=True,oof_estimator='pooled'))

def test_taiwan(taiwan):
    f,r=taiwan;ev=r['evaluations']['test']
    assert ev['matrix']==[[1973,7],[54,12]]
    vals={m['id']:m['value'] for m in ev['metrics']}
    assert vals['ROC_AUC']==pytest.approx(.903749617385981,abs=1e-10)
    assert vals['AP']==pytest.approx(.30852372633028535,abs=1e-10)
    assert r['evaluations']['test_OOF_threshold']['matrix']==[[1921,59],[38,28]]
    assert r['evaluations']['test_equal_prior']['matrix']==[[1747,233],[20,46]]
    assert r['oof_threshold']==pytest.approx(.12413099063180978,abs=1e-9)
    i=f.index[f.ID=='TW03598'][0]
    assert r['probability'][i]==pytest.approx(.9934229406644826,abs=1e-10)
    assert r['model']['a']@r['model']['Sp']@r['model']['a']==pytest.approx(1)
    assert r['model']['box_m']['M']==pytest.approx(322.463,abs=.002)

def test_pca(taiwan):
    f,r=taiwan;X=f.loc[f.train==1,FEATURES].to_numpy();p=pca_run(X)
    np.testing.assert_allclose(p['eigenvalues'],[1.9683301,1.28136996,.99317763,.46554536,.29157695],atol=1e-7)
    np.testing.assert_allclose(p['scores']@p['directions'].T*p['scale']+p['center'],X,atol=1e-12)
    np.testing.assert_allclose(p['directions'].T@p['directions'],np.eye(5),atol=1e-12)

def test_no_leakage(taiwan):
    f,r=taiwan;changed=f.copy();changed.loc[changed.train==0,FEATURES]=99999
    other=lda_run(changed,FEATURES,'bankrupt',1,dict(scale='standard'),dict(mode='saved_membership',column_id='train',seed=42),dict(oof=True))
    base=lda_run(f,FEATURES,'bankrupt',1,dict(scale='standard'),dict(mode='saved_membership',column_id='train',seed=42),dict(oof=True))
    np.testing.assert_array_equal(base['model']['b'],other['model']['b'])
    assert base['oof_threshold']==other['oof_threshold']

def test_edge_metrics():
    result=evaluate([0,1],[0,0])
    assert next(m for m in result['metrics'] if m['id']=='precision')['value'] is None
    assert result['matrix']==[[1,0],[1,0]]
    result=evaluate([0,0],[.1,.2]);assert result['curves']=={}
    assert expit(-1000)==0 and expit(1000)==1

def test_cluster():
    x=np.array([[0],[.1],[.2],[5],[5.1],[5.2]])
    a=cluster_run(x,'kmeans',dict(k=2));b=cluster_run(x,'kmeans',dict(k=2))
    assert sum(a['counts'])==6;np.testing.assert_array_equal(a['labels'],b['labels'])
    assert a['inertia']==pytest.approx(sum((x[i]-a['centroids'][g])@ (x[i]-a['centroids'][g]) for i,g in enumerate(a['labels'])))
    with pytest.raises(ValueError):cluster_run(x,'hierarchical',dict(k=2,metric='manhattan'))

def wait(client,id):
    for _ in range(900):
        r=client.get('/api/v1/runs/'+id).json()
        if r['status'] in ('succeeded','failed','cancelled'):return r
        time.sleep(.1)
    pytest.fail('Timeout')

def test_api_case_and_exports():
    with TestClient(app) as c:
        p=c.post('/api/v1/projects',json=dict(name='Test')).json()['id']
        case=c.post(f'/api/v1/projects/{p}/case-study').json()
        assert len(case['draft_ids'])==2
        did=case['draft_ids'][0]
        assert not c.post(f'/api/v1/drafts/{did}/validate').json()['blocking']
        payload=dict(draft_id=did,revision=1,idempotency_key='case')
        start=c.post('/api/v1/runs',json=payload);assert start.status_code==202,start.text
        id=start.json()['run_id'];assert c.post('/api/v1/runs',json=payload).json()['run_id']==id
        done=wait(c,id);assert done['status']=='succeeded',done
        result=c.get(f'/api/v1/runs/{id}/results').json();assert result['method']=='lda'
        observation=c.get(f'/api/v1/runs/{id}/observations/TW03598').json()
        assert observation['posterior']==pytest.approx(.9934229406644826,abs=1e-10)
        scenario=c.post(f'/api/v1/runs/{id}/scenarios',json=dict(kind='oof_threshold',idempotency_key='oof')).json()
        assert scenario['result']['counts']['TP']==28
        for fmt in ['json','csv','xlsx','pdf','zip','svg','png']:
            jid=c.post('/api/v1/exports',json=dict(run_id=id,format=fmt,idempotency_key=fmt,visual_id='confusion_matrix')).json()['job_id']
            for _ in range(200):
                j=c.get('/api/v1/jobs/'+jid).json()
                if j['status'] in ('succeeded','failed'):break
                time.sleep(.1)
            assert j['status']=='succeeded',j
            response=c.get(j['artifact']['download_url']);assert response.status_code==200
        snap=c.post(f'/api/v1/projects/{p}/snapshots',json=dict(run_ids=[id],scenario_ids=[scenario['id']])).json()
        assert snap['scenarios'][0]['result']['counts']['TP']==28
        cancel_payload=dict(draft_id=did,revision=1,idempotency_key='cancel')
        cancelled=c.post('/api/v1/runs',json=cancel_payload).json()['run_id']
        c.post(f'/api/v1/runs/{cancelled}/cancel')
        assert wait(c,cancelled)['status']=='cancelled'
        token=c.get('/api/v1/health').json()['session_token']
        assert c.post('/api/v1/projects',json=dict(name='Blocked'),headers={'Origin':'http://localhost:5173'}).status_code==403
        assert c.post('/api/v1/projects',json=dict(name='Allowed'),headers={'Origin':'http://localhost:5173','X-Session-Token':token}).status_code==200
        path=db.ROOT/'contracts/fixtures';path.mkdir(parents=True,exist_ok=True)
        (path/'taiwan_lda.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (path/'precision_undefined.json').write_text(db.dumps(evaluate([0,1],[0,0])),encoding='utf-8')

def test_import_rejects_formula():
    from openpyxl import Workbook
    from backend.service import inspect_upload,import_confirm
    import io
    w=Workbook();w.active.append(['x']);w.active.append(['=1+1']);b=io.BytesIO();w.save(b)
    iid=db.uid();p=db.folder(iid)/'a.xlsx';p.write_bytes(b.getvalue())
    with pytest.raises(ValueError,match='Formula'):import_confirm(dict(path=str(p),filename='a.xlsx',project_id='none'),dict(sheet_name='Sheet'))

def test_efa():
    from backend.service import r_health
    import subprocess
    if not r_health():pytest.skip('R dependencies absent')
    rng=np.random.default_rng(9);factor=rng.normal(size=(400,2));L=np.array([[.8,.1],[.7,.1],[.9,.1],[.1,.8],[.1,.7],[.1,.9]])
    x=factor@L.T+rng.normal(size=(400,6))*.3
    d=db.folder(db.uid());pd.DataFrame(x).to_csv(d/'x.csv',index=False)
    db.write_json(d/'config.json',dict(data=str(d/'x.csv'),q=2,seed=42,extraction='pa',rotation='oblimin'))
    p=subprocess.run(['Rscript',str(db.ROOT/'backend/efa.R'),str(d/'config.json'),str(d/'out.json')],capture_output=True,timeout=60)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    r=json.loads((d/'out.json').read_text());assert min(r['uniqueness'])>0
    assert np.array(r['pattern']).shape==(6,2)
