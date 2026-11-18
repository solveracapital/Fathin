import json,os
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch
from backend import storage as db
from backend.service import execute,validate,import_confirm
from backend.schemas import AnalysisResult
from backend.statistics import split_indices,lda_fit,predict,cluster_run

def dataset(frame):
    id=db.uid();frame=frame.copy();frame['_row_id']=[str(i) for i in range(len(frame))];frame['_source_row']=np.arange(len(frame))+2
    path=db.folder(id)/'data.json';db.write_json(path,frame.to_dict('records'))
    cols=[dict(id=c,source_name=c,display_name=c,inferred_type='number',assigned_type='number',role='ignored',unit=None,source_index=i) for i,c in enumerate(frame.columns) if not c.startswith('_')]
    return db.put('dataset',dict(id=id,project_id='test',path=str(path),columns=cols,source_sha256=db.digest(path.read_bytes()),row_count=len(frame)))

@pytest.mark.parametrize('method',['pca','kmeans','hierarchical','efa'])
def test_result_contracts(method):
    rng=np.random.default_rng(13);factors=rng.normal(size=(100,2));L=np.array([[.8,.1],[.7,.2],[.9,.1],[.1,.8],[.2,.7],[.1,.9]])
    frame=pd.DataFrame(factors@L.T+rng.normal(size=(100,6))*.3,columns=list('abcdef'))
    ds=dataset(frame);settings=dict(q=2) if method=='efa' else dict(k=3)
    cfg=dict(dataset_version_id=ds['id'],method=method,feature_ids=list('abcdef'),settings=settings,preprocessing={},split={})
    assert not validate(cfg)['blocking']
    r=dict(id=db.uid(),config=cfg);execute(r)
    b=json.loads((db.folder(r['id'])/'result.json').read_text(encoding='utf-8'))
    AnalysisResult.model_validate(b['result'])
    assert all(v['data_ref'] and v['table_alternative_ref'] for v in b['result']['visual_manifest'] if v['status']=='shown')
    fixtures=db.ROOT/'contracts/fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    (fixtures/(method+'_synthetic.json')).write_text(db.dumps(dict(synthetic=True,result=b['result'])),encoding='utf-8')

def test_affine_invariance():
    rng=np.random.default_rng(42);x=rng.normal(size=(100,3));y=np.array([0]*50+[1]*50);x[y==1]+=1
    m=lda_fit(x,y);A=np.diag([2,4,.5]);offset=np.array([7,-2,3]);other=lda_fit(x@A+offset,y)
    np.testing.assert_allclose(predict(m,x)[0],predict(other,x@A+offset)[0],atol=1e-12)

def test_group_temporal_splits():
    f=pd.DataFrame(dict(entity=np.repeat(np.arange(20),4),date=pd.date_range('2020-01-01',periods=80)))
    y=np.tile([0,1],40)
    a,b=split_indices(f,y,dict(mode='group',column_id='entity',seed=42))
    assert not set(f.iloc[a].entity)&set(f.iloc[b].entity)
    a,b=split_indices(f,y,dict(mode='temporal',column_id='date',cutoff='2020-02-15',gap_days=2))
    assert max(f.iloc[a].date)<min(f.iloc[b].date)

def test_one_feature_visual_policy():
    ds=dataset(pd.DataFrame(dict(x=[0,.1,.2,4,4.1,4.2])))
    run=dict(id=db.uid(),config=dict(dataset_version_id=ds['id'],method='kmeans',feature_ids=['x'],settings=dict(k=2),preprocessing={},split={}))
    execute(run);b=json.loads((db.folder(run['id'])/'result.json').read_text())
    assert [v['kind'] for v in b['result']['visual_manifest']]==['bar']

def test_document_and_ai_allowlist():
    from backend.documents import extract,retrieve
    from backend.assistant import select_evidence
    from docx import Document
    import io
    d=Document();d.add_paragraph('Analisis diskriminan menggunakan label kelompok.');b=io.BytesIO();d.save(b)
    chunks=extract(b.getvalue(),'a.docx')['chunks'];assert retrieve(chunks,'diskriminan')
    class Response:
        def raise_for_status(self):pass
        def json(self):return dict(choices=[dict(message=dict(content='{"selected_ids":["invented"]}'))])
    with patch.dict(os.environ,dict(AI_API_KEY='test',AI_MODEL='test',AI_BASE_URL='https://example.invalid')),patch('httpx.Client.post',return_value=Response()):
        assert select_evidence('question',[dict(id='real',text='data')])['status']=='unavailable'

def test_archive_limits():
    from backend.service import guard_archive
    import io,zipfile
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:z.writestr('../escape','bad')
    with pytest.raises(ValueError):guard_archive(b.getvalue())

def test_constrained_oof():
    from backend.statistics import lda_run
    rng=np.random.default_rng(8)
    n=120;f=pd.DataFrame(dict(x=rng.normal(size=n),z=rng.normal(size=n),y=np.tile([0,1],60),entity=np.repeat(np.arange(30),4),time=pd.date_range('2020-01-01',periods=n)))
    f.x+=f.y
    for split in [dict(mode='group',column_id='entity',seed=42),dict(mode='temporal',column_id='time',cutoff='2020-04-01')]:
        result=lda_run(f,['x','z'],'y',1,{},split,dict(oof=True,folds=3))
        assert 0<result['oof_threshold']<1
        if split['mode']=='temporal':assert np.isnan(result['oof']).any()
