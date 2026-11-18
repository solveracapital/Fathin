"""Regression coverage for the independent backend audit."""
import concurrent.futures
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.statistics import transform_fit,transform_apply,evaluate,pca_run,cluster_run,lda_run
from backend.app import app
from backend import storage as db

def test_missing_policy_is_not_silently_changed():
    _,t=transform_fit(np.array([[1.,2.],[3.,4.]]),{})
    with pytest.raises(ValueError,match='Missing'):transform_apply(np.array([[np.nan,4.]]),t)
    _,t=transform_fit(np.array([[1.,2.],[3.,4.]]),dict(missing='median'))
    np.testing.assert_equal(transform_apply(np.array([[np.nan,4.]]),t),[[2.,4.]])

@pytest.mark.parametrize('bad',[0,1.5,True])
def test_integer_parameters(bad):
    with pytest.raises(ValueError):pca_run(np.array([[0,1],[1,2],[3,2]]),q=bad)
    with pytest.raises(ValueError):cluster_run(np.array([[0],[1],[2],[3]]),'kmeans',dict(k=bad))

def test_full_variance_target_and_invalid_probabilities():
    r=pca_run(np.random.default_rng(4).normal(size=(20,4)),target=1)
    assert r['selected_q']==4 and r['cumulative'][-1]==1
    for p in ([np.nan,.3],[-1,.1],[2,.3]):
        with pytest.raises(ValueError):evaluate([0,1],p)

def test_pd_missing_is_json_null_and_ids_cannot_escape():
    assert db.dumps({'x':pd.NA})=='{"x": null}'
    for id in ('','-','../','aaa'):
        with pytest.raises(ValueError):db.folder(id)

def test_concurrent_run_creation_and_atomic_cancel():
    with TestClient(app) as c:
        p=c.post('/api/v1/projects',json={'name':'Concurrency audit'}).json()['id']
        case=c.post(f'/api/v1/projects/{p}/case-study').json()
        payload=dict(draft_id=case['draft_ids'][0],revision=1,idempotency_key='same-request')
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            ids=list(pool.map(lambda _:c.post('/api/v1/runs',json=payload).json()['run_id'],range(4)))
        assert len(set(ids))==1
        c.post('/api/v1/runs/'+ids[0]+'/cancel')
        assert db.transition(ids[0],['running'],dict(status='succeeded')) is None
        assert c.post('/api/v1/exports',json=dict(run_id=ids[0],format='../x',idempotency_key='x')).status_code==422

def test_temporal_gap_is_not_test():
    from backend.results import build
    rng=np.random.default_rng(5);n=100
    f=pd.DataFrame(dict(x=rng.normal(size=n),z=rng.normal(size=n),y=np.tile([0,1],50),time=pd.date_range('2020-01-01',periods=n),_row_id=[str(i) for i in range(n)]))
    f.x+=f.y
    r=lda_run(f,['x','z'],'y',1,{},dict(mode='temporal',column_id='time',cutoff='2020-03-01',gap_days=5),{})
    result=build(dict(id=db.uid(),config=dict(method='lda',feature_ids=['x','z'],settings={}),provenance={}),r,f)
    assert sum(row['subset']=='excluded_gap' for row in result['tables']['predictions']['rows'])==5

def test_invalid_archive_is_client_error_and_exports_recover():
    job=db.put('job',dict(id=db.uid(),status='running',project_id='test'))
    with TestClient(app) as c:
        assert db.get(job['id'])['status']=='failed'
        p=c.post('/api/v1/projects',json=dict(name='Malformed upload')).json()['id']
        response=c.post(f'/api/v1/projects/{p}/imports',files={'file':('broken.xlsx',b'PKbroken','application/octet-stream')})
        assert response.status_code==422 and response.json()['error']['code']=='INVALID_ARCHIVE'

def test_explicit_text_type_remains_text():
    from backend.service import import_confirm,dataframe
    id=db.uid();path=db.folder(id)/'data.csv';path.write_text('value,x\n001,1\n002,2\n003,3\n')
    d=import_confirm(dict(path=str(path),filename='data.csv',project_id='test',inspection=dict(delimiter=',')),dict(decimal='.',column_types=dict(c0='text')))
    f=dataframe(d);assert f.c0.tolist()==['001','002','003']
    assert d['columns'][0]['assigned_type']=='text'
