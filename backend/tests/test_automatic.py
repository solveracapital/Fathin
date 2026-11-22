import json,time
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend import storage as db
from backend.automatic import create_plan
from backend.service import execute,dataframe
from backend.statistics import split_indices,time_values
from backend.mathematics import math_prose,INLINE
from test_contracts import dataset

def attached(frame):
    project=db.put('project',dict(id=db.uid(),name='Automatic audit',case_type='custom'))
    ds=dataset(frame);ds['project_id']=project['id'];db.put('dataset',ds)
    return project,ds

def item(plan,method):return next(a for a in plan['analyses'] if a['method']==method)

def wait_suite(client,id):
    for _ in range(1600):
        suite=client.get('/api/v1/analysis-suites/'+id).json()
        if suite['status']!='running':return suite
        time.sleep(.05)
    pytest.fail('Automatic suite did not finish')

def test_automatic_real_methods_without_manual_settings():
    rng=np.random.default_rng(583);latent=rng.normal(size=(160,2))
    X=latent@np.array([[.9,.8,.7,.1,.2,.1],[.1,.2,.1,.9,.8,.7]])+rng.normal(size=(160,6))*.35
    frame=pd.DataFrame(X,columns=list('abcdef'));frame['target']=(latent[:,0]>.1).astype(int);frame['ID']=np.arange(160)
    project,ds=attached(frame)
    with TestClient(app) as c:
        response=c.post(f"/api/v1/projects/{project['id']}/automatic-plan",json=dict(dataset_version_id=ds['id']))
        assert response.status_code==200,response.text
        plan=response.json();assert plan['feature_ids']==list('abcdef')
        assert all(a['status']=='ready' for a in plan['analyses']),plan
        body=dict(idempotency_key='automatic-all')
        response=c.post('/api/v1/automatic-plans/'+plan['id']+'/start',json=body);assert response.status_code==202,response.text
        sid=response.json()['id'];assert c.post('/api/v1/automatic-plans/'+plan['id']+'/start',json=body).json()['id']==sid
        suite=wait_suite(c,sid);assert suite['status']=='succeeded',suite
        assert len(suite['successful_run_ids'])==5
        report=c.get('/api/v1/analysis-suites/'+sid+'/presentation').json()
        assert len(report['sections'])>70
        assert any(s.get('formula') for s in report['sections'])
        for rid in suite['successful_run_ids']:
            result=c.get('/api/v1/runs/'+rid+'/results').json()
            assert result['provenance']['automatic_decisions']
        other=c.post('/api/v1/projects',json=dict(name='Other')).json()['id']
        assert c.post(f'/api/v1/projects/{other}/automatic-plan',json=dict(dataset_version_id=ds['id'])).status_code==422

def test_unknown_and_ambiguous_labels_are_explained_without_fabrication():
    rng=np.random.default_rng(56)
    _,ds=attached(pd.DataFrame(dict(a=rng.normal(size=40),b=rng.normal(size=40),flag=np.tile([0,1],20))))
    assert item(create_plan(ds['id']),'lda')['status']=='explained'
    _,ds=attached(pd.DataFrame(dict(a=rng.normal(size=40),b=rng.normal(size=40),target=np.tile([0,1],20),label=np.tile([1,0],20))))
    plan=create_plan(ds['id']);assert item(plan,'lda')['status']=='explained'
    assert 'target' not in plan['feature_ids'] and 'label' not in plan['feature_ids']

def test_missing_duplicate_and_constant_features_are_handled_explicitly():
    rng=np.random.default_rng(39);a=rng.normal(size=100);b=rng.normal(size=100);a[4]=np.nan
    _,ds=attached(pd.DataFrame(dict(a=a,duplicate=a*2,b=b,constant=1,target=np.tile([0,1],50),note='source')))
    plan=create_plan(ds['id']);assert 'constant' not in plan['feature_ids'] and 'note' not in plan['feature_ids']
    config=item(plan,'lda')['config'];assert config and config['preprocessing']['missing']=='median'
    assert len(config['feature_ids'])==2
    run=dict(id=db.uid(),config=config);execute(run)
    raw=json.loads((db.folder(run['id'])/'raw.json').read_text())
    tr,_=split_indices(dataframe(ds),np.tile([0,1],50),config['split'])
    expected=np.nanmedian(dataframe(ds).iloc[tr][config['feature_ids']].to_numpy(float),axis=0)
    np.testing.assert_allclose(raw['transform']['median'],expected)

def test_only_explanations_can_be_presented_and_exported():
    project,ds=attached(pd.DataFrame(dict(name=['Ana','Budi','Citra'],constant=[1,1,1])))
    with TestClient(app) as c:
        plan=create_plan(ds['id']);assert all(a['status']=='explained' for a in plan['analyses'])
        suite=c.post('/api/v1/automatic-plans/'+plan['id']+'/start',json=dict(idempotency_key='no-numbers')).json()
        assert suite['status']=='succeeded' and not suite['successful_run_ids']
        sections=c.get('/api/v1/analysis-suites/'+suite['id']+'/presentation').json()['sections'];assert len(sections)==5
        response=c.post(f"/api/v1/projects/{project['id']}/snapshots",json=dict(automatic_suite_id=suite['id'],ordered_sections=sections))
        assert response.status_code==200,response.text
        snap=response.json();assert not snap['bundles'] and snap['source_hashes']==[ds['source_sha256']]
        for fmt in ('pdf','json','csv','xlsx'):
            response=c.post('/api/v1/exports',json=dict(snapshot_id=snap['id'],format=fmt,idempotency_key=db.uid()))
            assert response.status_code==202,response.text
            for _ in range(200):
                job=c.get('/api/v1/jobs/'+response.json()['job_id']).json()
                if job['status'] not in ('running','queued'):break
                time.sleep(.05)
            assert job['status']=='succeeded',job
        other=c.post('/api/v1/projects',json=dict(name='Other')).json()['id']
        assert c.post(f'/api/v1/projects/{other}/snapshots',json=dict(automatic_suite_id=suite['id'],ordered_sections=sections)).status_code==422
        assert c.delete('/api/v1/projects/'+project['id']).status_code==200
        with pytest.raises(KeyError):db.get(plan['id'])

def test_hierarchy_samples_with_exact_row_provenance():
    _,ds=attached(pd.DataFrame(np.random.default_rng(61).normal(size=(1100,3)),columns=list('abc')))
    plan=create_plan(ds['id']);config=item(plan,'hierarchical')['config'];assert config
    assert len(config['settings']['sample_row_ids'])==1000
    run=dict(id=db.uid(),config=config);execute(run)
    bundle=json.loads((db.folder(run['id'])/'result.json').read_text())
    assert bundle['result']['subset_definitions']['sample']['n']==1000
    assert bundle['result']['provenance']['sampling']['population_n']==1100
    frame=json.loads((db.folder(run['id'])/'frame.json').read_text())
    assert {r['_row_id'] for r in frame}==set(config['settings']['sample_row_ids'])

def test_paper_reproduction_is_bound_to_source_not_project_name():
    with TestClient(app) as c:
        project=c.post('/api/v1/projects',json=dict(name='Taiwan')).json()['id']
        dsid=c.post(f'/api/v1/projects/{project}/case-study').json()['dataset_id']
        plan=create_plan(dsid);lda=item(plan,'lda')['config'];assert lda and lda['split']['mode']=='saved_membership'
        assert item(plan,'pca')['config']['settings']['subset']=='train'
        run=dict(id=db.uid(),config=lda);execute(run)
        raw=json.loads((db.folder(run['id'])/'raw.json').read_text());assert raw['evaluations']['test']['counts']==dict(TN=1973,FP=7,FN=54,TP=12)
        frame=pd.DataFrame(np.random.default_rng(70).normal(size=(60,3)),columns=list('abc'));frame['target']=np.tile([0,1],30)
        new=dataset(frame);new['project_id']=project;db.put('dataset',new)
        fresh=create_plan(new['id']);assert item(fresh,'lda')['config']['split']['mode']=='stratified_random'
        assert 'makalah' not in item(fresh,'lda')['config']['purpose'].lower()

@pytest.mark.parametrize('column,values,expected',[('entity_id',np.repeat(np.arange(40),4),'group'),('year',np.repeat(np.arange(2000,2020),8),'temporal')])
def test_entity_or_time_split_is_chosen_without_user_settings(column,values,expected):
    rng=np.random.default_rng(32);frame=pd.DataFrame(dict(a=rng.normal(size=160),b=rng.normal(size=160),target=np.tile([0,1],80)));frame[column]=values
    _,ds=attached(frame);plan=create_plan(ds['id']);config=item(plan,'lda')['config'];assert config,item(plan,'lda')
    assert config['split']['mode']==expected and column not in config['feature_ids']
    train,test=split_indices(dataframe(ds),frame.target.to_numpy(),config['split'])
    if expected=='group':assert not set(values[train])&set(values[test])
    else:assert max(values[train])<min(values[test])

def test_math_markup_is_idempotent_and_not_plain_formula_text():
    text='Skor T = Z A, dengan η dan L Φ Lᵀ + Ψ.'
    marked=math_prose(text);assert marked==math_prose(marked)
    assert len(INLINE.findall(marked))==3 and r'\Phi' in marked

def test_numeric_years_and_dates_are_not_nanoseconds_since_epoch():
    years=time_values(pd.Series([2020.,2021.]),dict(time_format='year'))
    assert years.dt.year.tolist()==[2020,2021]
    dates=time_values(pd.Series([20200101,20210203]),dict(time_format='date'))
    assert dates.dt.year.tolist()==[2020,2021]
    with pytest.raises(ValueError):time_values(pd.Series([2020.5]),dict(time_format='year'))
