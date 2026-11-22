import json,time
import numpy as np
import pandas as pd
import pytest
from scipy import linalg,stats
from fastapi.testclient import TestClient
from backend.factors import efa_run,parallel_analysis
from backend.app import app
from backend import storage as db
from test_contracts import dataset

def known_factor_sample():
    L=np.array([[.8,0],[.7,0],[.9,0],[0,.8],[0,.7],[0,.9]])
    Phi=np.array([[1,.3],[.3,1]]);common=L@Phi@L.T;R=common+np.diag(1-common.diagonal())
    rng=np.random.default_rng(72);X=rng.normal(size=(400,6));Q,_=np.linalg.qr(X-X.mean(0))
    X=Q@linalg.cholesky(R,lower=False)*np.sqrt(399)
    return X,R,common

@pytest.mark.parametrize('extraction',['pa','ml'])
@pytest.mark.parametrize('rotation',['none','varimax','oblimin'])
def test_factor_solution_against_known_population_matrix(extraction,rotation):
    X,R,common=known_factor_sample();r=efa_run(X,q=2,extraction=extraction,rotation=rotation)
    L=np.asarray(r['pattern']);Phi=np.asarray(r['Phi']);structure=L@Phi;h=np.diag(L@Phi@L.T)
    np.testing.assert_allclose(L@Phi@L.T,common,atol=3e-6)
    np.testing.assert_allclose(r['structure'],structure,atol=1e-12)
    np.testing.assert_allclose(r['communalities'],h,atol=1e-12)
    np.testing.assert_allclose(r['uniqueness'],1-h,atol=1e-12)
    np.testing.assert_allclose(r['residual'],R-L@Phi@L.T-np.diag(1-h),atol=1e-12)
    Z=(X-X.mean(0))/X.std(0,ddof=1)
    np.testing.assert_allclose(r['scores'],Z@np.linalg.inv(R)@structure,atol=1e-10)
    inverse=np.linalg.inv(R);P=-inverse/np.sqrt(np.outer(inverse.diagonal(),inverse.diagonal()));np.fill_diagonal(P,0)
    zero=R-np.eye(6);expected=(zero**2).sum()/((zero**2).sum()+(P**2).sum())
    assert r['kmo']==pytest.approx(expected,abs=1e-12)
    chi=-(len(X)-1-(2*6+5)/6)*np.log(np.linalg.det(R))
    assert r['bartlett']['chisq']==pytest.approx(chi,abs=1e-9)
    assert r['bartlett']['df']==15
    assert r['bartlett']['p.value']==pytest.approx(stats.chi2.sf(chi,15),abs=1e-12)

def test_parallel_boundary_seed_and_retention_are_reproducible():
    X,R,_=known_factor_sample();a=parallel_analysis(R,len(X),42);b=parallel_analysis(R,len(X),42)
    np.testing.assert_array_equal(a['simulation_values'],b['simulation_values'])
    np.testing.assert_array_equal(a['simulated'],np.quantile(a['simulation_values'],.95,axis=0))
    assert a['recommended']==2
    c=parallel_analysis(R,len(X),43);assert not np.array_equal(a['simulation_values'],c['simulation_values'])
    assert efa_run(X)['q']==2

def test_invalid_factor_models_fail_without_repair():
    X,R,_=known_factor_sample()
    for q in [0,True,1.5,4,6]:
        with pytest.raises(ValueError):efa_run(X,q=q)
    with pytest.raises(ValueError):efa_run(np.c_[X,X[:,0]],q=2)
    with pytest.raises(ValueError):efa_run(X[:4],q=1)
    with pytest.raises(ValueError):efa_run(np.full((30,4),1.),q=1)
    with pytest.raises(ValueError):efa_run(X,q=2,rotation='bogus')

def test_single_factor_matrix_shapes_and_rotation_identity():
    rng=np.random.default_rng(8);f=rng.normal(size=(250,1));X=f@np.array([[.8,.7,.9,.6]])+rng.normal(size=(250,4))*.4
    r=efa_run(X,q=1);assert r['pattern'].shape==(4,1) and r['scores'].shape==(250,1)
    np.testing.assert_allclose(r['Phi'],[[1.]])

def test_snapshots_and_exports_keep_every_run_and_reject_invalid_refs():
    ds=dataset(pd.DataFrame(np.random.default_rng(6).normal(size=(50,3)),columns=list('abc')))
    with TestClient(app) as c:
        p=c.post('/api/v1/projects',json=dict(name='Export integrity')).json()['id'];ds['project_id']=p;db.put('dataset',ds)
        runs=[]
        for method in ['pca','kmeans']:
            d=c.post(f'/api/v1/projects/{p}/drafts',json=dict(dataset_version_id=ds['id'],method=method,feature_ids=list('abc'),settings=dict(k=2))).json()
            run=c.post('/api/v1/runs',json=dict(draft_id=d['id'],revision=1,idempotency_key=method)).json()['run_id']
            for _ in range(600):
                state=c.get('/api/v1/runs/'+run).json()
                if state['status']=='succeeded':break
                assert state['status']!='failed',state;time.sleep(.05)
            assert state['status']=='succeeded';runs.append(run)
        endpoint=f'/api/v1/projects/{p}/snapshots'
        assert c.post(endpoint,json=dict(run_ids=[runs[0],runs[0]])).status_code==422
        assert c.post(endpoint,json=dict(run_ids=runs,ordered_sections=[dict(kind='visual',run_id=runs[0],visual_id='confusion_matrix')])).status_code==422
        sections=c.get('/api/v1/runs/'+runs[0]+'/presentation').json()['sections']
        snap=c.post(endpoint,json=dict(run_ids=runs,ordered_sections=sections,speaker_notes={'note':'preserved'})).json()
        payload=dict(snapshot_id=snap['id'],format='json',idempotency_key='same-export')
        first=c.post('/api/v1/exports',json=payload).json();second=c.post('/api/v1/exports',json=payload).json();assert first==second
        for _ in range(100):
            job=c.get('/api/v1/jobs/'+first['job_id']).json()
            if job['status']!='running':break
            time.sleep(.05)
        assert job['status']=='succeeded',job
        actual=c.get(job['artifact']['download_url']).json()
        assert actual['run_ids']==runs and len(actual['bundles'])==2 and actual['speaker_notes']=={'note':'preserved'}
        assert actual['ordered_sections']==snap['ordered_sections']
        assert c.post('/api/v1/exports',json={**payload,'run_id':runs[0]}).status_code==422
        for fmt in ('csv','xlsx'):
            response=c.post('/api/v1/exports',json=dict(snapshot_id=snap['id'],format=fmt,idempotency_key=fmt)).json()
            for _ in range(100):
                job=c.get('/api/v1/jobs/'+response['job_id']).json()
                if job['status']!='running':break
                time.sleep(.05)
            assert job['status']=='succeeded',job
            import io
            content=io.BytesIO(c.get(job['artifact']['download_url']).content)
            if fmt=='csv':
                exported=pd.read_csv(content);assert set(exported['run_id'])==set(runs) and set(exported['method'])=={'pca','kmeans'}
                assert len(exported)==sum(len(b['result']['metrics']) for b in actual['bundles'])
            else:assert set(pd.read_excel(content,sheet_name='provenance')['run_id'])==set(runs)

@pytest.mark.parametrize('method',['efa','kmeans'])
def test_dense_visuals_are_not_forced_and_report_preserves_every_feature(method):
    from backend.service import execute
    from backend.presentation import sections_for_run
    rng=np.random.default_rng(82);f=rng.normal(size=(150,2));L=np.array([[.8,.05]]*6+[[.05,.8]]*6)
    names=[f'indicator_{i}' for i in range(12)];ds=dataset(pd.DataFrame(f@L.T+rng.normal(size=(150,12))*.3,columns=names))
    r=dict(id=db.uid(),config=dict(dataset_version_id=ds['id'],method=method,feature_ids=names,preprocessing={},split={},settings=dict(q=2,k=3)))
    execute(r);root=db.folder(r['id']);raw=json.loads((root/'raw.json').read_text());bundle=json.loads((root/'result.json').read_text());frame=pd.DataFrame(json.loads((root/'frame.json').read_text()))
    sections=sections_for_run(r,bundle,raw,frame)
    if method=='efa':
        assert not any(s['kind']=='visual' and s['visual_id']=='loadings' for s in sections)
        values=[row['indikator'] for s in sections if '_efa_pattern_1_' in s['id'] for row in s['rows']]
        assert values==names
    else:
        assert next(v for v in bundle['result']['visual_manifest'] if v['id']=='profiles')['status']=='available'
        assert not any(s['kind']=='visual' and s['visual_id']=='profiles' for s in sections)
        assert [row['indikator'] for s in sections if '_cluster_profile_1_' in s['id'] for row in s['rows']]==names
