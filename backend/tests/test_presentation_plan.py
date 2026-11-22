import json
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from backend.app import app
from backend import storage as db
from backend.service import execute
from test_contracts import dataset

def ready(project,cfg):
    r=dict(id=db.uid(),project_id=project,config=cfg,dataset_version_id=cfg['dataset_version_id'],created_at=db.now(),status='succeeded')
    execute(r);db.put('run',r);return r['id']

def test_paper_deck_is_curated_keeps_essential_evidence_and_preserves_full_report():
    with TestClient(app) as c:
        project=c.post('/api/v1/projects',json=dict(name='Curated paper')).json()['id']
        example=c.post(f'/api/v1/projects/{project}/case-study').json()
        runs=[ready(project,db.get(d,'draft')) for d in example['draft_ids']]
        # Add a genuine clustering exploration on the same source.
        cfg=db.get(example['draft_ids'][1],'draft').copy();cfg.update(method='kmeans',preprocessing=dict(scale='standard'),settings=dict(k=2),purpose='Eksplorasi tambahan')
        extra=ready(project,cfg);runs.append(extra)
        response=c.post(f'/api/v1/projects/{project}/presentation-plan',json=dict(run_ids=runs));assert response.status_code==200,response.text
        plan=response.json();core=[s for s in plan['sections'] if s['enabled']]
        assert 15<=len(core)<=22 and plan['core_count']==len(core)
        assert all(s['tier']=='core' for s in core)
        assert not any(s['run_id']==extra for s in core)
        optional=[s for s in plan['sections'] if s['group_id']=='kmeans'];assert len(optional)>=2 and not any(s['enabled'] for s in optional)
        assert all(not s['enabled'] for s in plan['sections'] if s['group_id']=='technical')
        text=' '.join(' '.join(s.get('paragraphs',[])) for s in core)
        for phrase in ('1973','54','12','Box M','reproduksi parsial','SPSS','0,903750','0,308524','premi','PCA','EFA'):
            assert phrase in text,phrase
        assert any(s.get('formula') and r'\frac' in s['formula'] for s in core)
        assert any(s.get('visual_id')=='precision_recall' for s in core)
        assert any(s.get('visual_id')=='confusion_matrix' for s in core)
        assert any('indikator' in s.get('columns',[]) and len(s['rows'])==5 for s in core)
        # Untrusted browser text cannot replace numerical or scientific content.
        selected=json.loads(json.dumps(core));selected[0]['paragraphs']=['Angka palsu'];selected[0]['title']='Judul disunting'
        body=dict(run_ids=runs,presentation_plan_id=plan['id'],ordered_sections=selected)
        snap=c.post(f'/api/v1/projects/{project}/snapshots',json=body);assert snap.status_code==200,snap.text
        assert snap.json()['ordered_sections'][0]['title']=='Judul disunting'
        assert snap.json()['ordered_sections'][0]['paragraphs']==core[0]['paragraphs']
        assert len(snap.json()['ordered_sections'])==len(core)
        assert len(c.get('/api/v1/runs/'+runs[0]+'/presentation').json()['sections'])>30
        assert c.post(f'/api/v1/projects/{project}/snapshots',json={**body,'ordered_sections':[]}).status_code==422
        other=c.post('/api/v1/projects',json=dict(name='Other')).json()['id']
        assert c.post(f'/api/v1/projects/{other}/presentation-plan',json=dict(run_ids=runs)).status_code==422
        assert c.post(f'/api/v1/projects/{other}/snapshots',json=body).status_code==422

def test_generic_dataset_does_not_inherit_paper_claims_or_actuarial_conclusions():
    with TestClient(app) as c:
        project=c.post('/api/v1/projects',json=dict(name='Generic PCA')).json()['id']
        ds=dataset(pd.DataFrame(np.random.default_rng(18).normal(size=(60,4)),columns=list('abcd')));ds['project_id']=project;db.put('dataset',ds)
        rid=ready(project,dict(dataset_version_id=ds['id'],feature_ids=list('abcd'),method='pca',purpose='Makalah dataset mandiri',preprocessing={},settings={},split={}))
        p=c.post(f'/api/v1/projects/{project}/presentation-plan',json=dict(run_ids=[rid])).json()
        assert not p['paper_case'] and p['core_count']<12
        text=' '.join(' '.join(s.get('paragraphs',[])) for s in p['sections'] if s['enabled'])
        assert 'ROC-AUC 0,904' not in text and 'Dataset Taiwan' not in text
        assert not any(s.get('visual_id')=='confusion_matrix' for s in p['sections'] if s['enabled'])
