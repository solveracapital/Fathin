import json,time
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scipy.cluster.hierarchy import linkage
from backend import storage as db
from backend.app import app
from backend.suites import configurations
from backend.statistics import pca_run,cluster_run
from backend.service import execute
from backend.service import validate
from backend.presentation import sections_for_run
from test_contracts import dataset

def test_suite_options_are_independent_and_do_not_mutate_source():
    d=dict(dataset_version_id='x',purpose='y',feature_ids=['a','b'],target_id='target',analysis_options={'pca':dict(settings=dict(q=1)), 'kmeans':dict(preprocessing=dict(scale='standard'),settings=dict(k=3))})
    copies=configurations(d);copies[0]['feature_ids'].append('c');copies[0]['settings']['q']=2
    assert d['feature_ids']==['a','b'] and d['analysis_options']['pca']['settings']['q']==1
    assert copies[1]['settings']==dict(k=3) and copies[1]['feature_ids']==['a','b']
    with pytest.raises(ValueError):configurations(dict(d,analysis_options={'bogus':{}}))

def test_multiple_real_methods_and_blocked_method_have_separate_results():
    rng=np.random.default_rng(86);X=rng.normal(size=(160,4));y=np.tile([0,1],80);X[:,0]+=y
    ds=dataset(pd.DataFrame(dict(a=X[:,0],b=X[:,1],c=X[:,2],d=X[:,3],target=y)))
    with TestClient(app) as c:
        project=c.post('/api/v1/projects',json=dict(name='Several questions')).json()['id']
        ds.update(project_id=project);db.put('dataset',ds)
        opts={m:dict(preprocessing=dict(scale='standard' if m=='kmeans' else 'none'),settings=dict(q=9) if m=='efa' else dict(k=3),split=dict(seed=42)) for m in ['pca','kmeans','hierarchical','lda','efa']}
        d=c.post(f'/api/v1/projects/{project}/drafts',json=dict(dataset_version_id=ds['id'],method='pca',feature_ids=['a','b','c','d'],target_id='target',positive_label=1,analysis_options=opts)).json()
        plan=c.post(f"/api/v1/drafts/{d['id']}/validate-suite").json()
        assert len(plan['analyses'])==5 and plan['analyses'][-1]['blocking']
        body=dict(draft_id=d['id'],revision=d['revision'],idempotency_key='one-suite')
        response=c.post('/api/v1/analysis-suites',json=body);assert response.status_code==202,response.text
        suite=response.json();assert c.post('/api/v1/analysis-suites',json=body).json()['id']==suite['id']
        assert c.post('/api/v1/analysis-suites',json={**body,'revision':9}).status_code==409
        for _ in range(800):
            suite=c.get('/api/v1/analysis-suites/'+suite['id']).json()
            if suite['status']!='running':break
            time.sleep(.1)
        assert suite['status']=='partial',suite
        assert len(suite['successful_run_ids'])==4
        assert suite['analyses'][-1]['status']=='blocked' and 'run_id' not in suite['analyses'][-1]
        for item in suite['analyses'][:-1]:
            r=c.get('/api/v1/runs/'+item['run_id']).json();assert r['config']['method']==item['method']
            result=c.get('/api/v1/runs/'+item['run_id']+'/results').json();assert result['method']==item['method']
            report=c.get('/api/v1/runs/'+item['run_id']+'/presentation');assert report.status_code==200,report.text
            sections=report.json()['sections'];assert len(sections)>10
            assert all(len(s.get('rows',[]))<=4 for s in sections)
            assert any('conclusion' in s['id'] for s in sections)
            if item['method']=='pca':
                raw=json.loads((db.folder(r['id'])/'raw.json').read_text());independent=pca_run(X)
                np.testing.assert_allclose(raw['eigenvalues'],independent['eigenvalues'],atol=1e-12)

def test_pca_eigenvalues_and_directions_against_independent_svd():
    X=np.random.default_rng(82).normal(size=(160,5))*[1,2,3,4,5]
    for basis in ['correlation','covariance']:
        raw=pca_run(X,basis);Z=(X-X.mean(0))/(X.std(0,ddof=1) if basis=='correlation' else 1)
        U,S,V=np.linalg.svd(Z,full_matrices=False)
        np.testing.assert_allclose(raw['eigenvalues'],S*S/(len(X)-1),rtol=1e-12)
        np.testing.assert_allclose(np.abs(raw['directions'].T@V.T),np.eye(5),atol=1e-12)

def test_invalid_seed_and_cluster_configuration_are_blocked_before_running():
    ds=dataset(pd.DataFrame(dict(a=[0,1,2,3,4],b=[1,3,2,4,5])))
    cfg=dict(dataset_version_id=ds['id'],feature_ids=['a','b'],method='kmeans',settings=dict(k=2))
    for seed in [-1,1.5,True,2147483648]:assert validate({**cfg,'split':dict(seed=seed)})['blocking']
    for k in [1,5,6]:assert validate({**cfg,'settings':dict(k=k)})['blocking']
    assert validate({**cfg,'method':'hierarchical','settings':dict(k=2,linkage='bad')})['blocking']
    assert not validate(cfg)['blocking']


def test_hierarchical_memberships_and_centers_match_actual_tree():
    X=np.random.default_rng(66).normal(size=(55,3))
    for rule in ['ward','complete','single','average']:
        r=cluster_run(X,'hierarchical',dict(k=4,linkage=rule));np.testing.assert_allclose(r['tree'],linkage(X,method=rule))
        for k,center in enumerate(r['centroids']):np.testing.assert_allclose(center,X[r['labels']==k].mean(0))
        assert sum(r['counts'])==len(X)

def test_long_report_retains_every_indicator_and_value():
    names=[f'feature_{i}' for i in range(13)];frame=pd.DataFrame(np.random.default_rng(82).normal(size=(100,13)),columns=names)
    ds=dataset(frame);run=dict(id=db.uid(),config=dict(dataset_version_id=ds['id'],method='pca',feature_ids=names,settings=dict(q=3),preprocessing={},split={}))
    execute(run);raw=json.loads((db.folder(run['id'])/'raw.json').read_text());bundle=json.loads((db.folder(run['id'])/'result.json').read_text());frame=pd.DataFrame(json.loads((db.folder(run['id'])/'frame.json').read_text()))
    sections=sections_for_run(run,bundle,raw,frame)
    values=[r for s in sections if '_pca_spectrum_' in s['id'] for r in s['rows']]
    assert len(values)==13
    np.testing.assert_allclose([r['eigenvalue'] for r in values],raw['eigenvalues'])
    assert sum(len(s.get('paragraphs',[])) for s in sections)>30
