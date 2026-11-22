"""Numerical-to-visual evidence tests, independent of screenshots."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from backend.statistics import lda_run,pca_run,cluster_run
from backend.results import build
from backend.charts import figure
from backend.presentation import sections_for_run
from backend import storage as db

@pytest.fixture(scope='module')
def evidence():
    frame=pd.read_csv(db.ROOT/'outputs/makalah_multivariat/Data_Analisis.csv');frame['_row_id']=frame.ID
    names=['WC_TA','RE_TA','ROA_A','EQ_LIAB','TURNOVER']
    cfg=dict(method='lda',purpose='Reproduksi makalah',feature_ids=names,preprocessing={},split=dict(mode='saved_membership',column_id='train',reconstruct_order=True,seed=42),settings=dict(oof=True))
    raw=lda_run(frame,names,'bankrupt',1,{},cfg['split'],cfg['settings'])
    run=dict(id=db.uid(),config=cfg,provenance=dict(source_sha256='test-source',feature_labels=names))
    return frame,run,raw,build(run,raw,frame)

def test_scores_independently_match_source_observations(evidence):
    f,run,r,b=evidence;X=f[run['config']['feature_ids']].to_numpy();y=f.bankrupt.to_numpy();train=r['train']
    means=np.array([X[train][y[train]==g].mean(0) for g in (0,1)])
    counts=np.bincount(y[train]);pooled=sum((counts[g]-1)*np.cov(X[train][y[train]==g],rowvar=False) for g in (0,1))/(len(train)-2)
    inverse=np.linalg.inv(pooled)
    indices=[0,10,100,3597,6818]
    for i in indices:
        scores=np.array([X[i]@inverse@means[g]-.5*means[g]@inverse@means[g]+np.log(counts[g]/len(train)) for g in (0,1)])
        assert expit(scores[1]-scores[0])==pytest.approx(r['probability'][i],abs=1e-10)
        row=b['tables']['predictions']['rows'][i]
        assert row['row_id']==f.iloc[i].ID and row['posterior']==r['probability'][i]

def test_confusion_plot_and_pdf_orientation_match_counts(evidence):
    _,_,r,b=evidence;plot=figure(b,'confusion_matrix')
    np.testing.assert_array_equal(plot.data[0].z,[[1973,7],[54,12]])
    assert plot.layout.yaxis.autorange=='reversed'
    assert b['visuals']['confusion_matrix']['data']['orientation']=='actual_rows_predicted_columns'

def test_ap_area_matches_step_plot_without_trapezoidal_substitution(evidence):
    _,_,r,b=evidence;curve=b['visuals']['precision_recall']['data'];x=np.array(curve['x']);y=np.array(curve['y'])
    expected=next(m['value'] for m in r['evaluations']['test']['metrics'] if m['id']=='AP')
    assert np.dot(-np.diff(x),y[:-1])==pytest.approx(expected,abs=1e-12)
    plot=figure(b,'precision_recall')
    np.testing.assert_array_equal(plot.data[0].x,x);np.testing.assert_array_equal(plot.data[0].y,y)
    assert plot.data[0].line.shape=='hv'
    table=b['tables']['visual_precision_recall']['rows']
    assert len(table)==len(x) and table[-1]['threshold'] is None
    np.testing.assert_array_equal([row['recall'] for row in table],x)
    np.testing.assert_array_equal([row['precision'] for row in table],y)

def test_pca_browser_trace_uses_supported_type_and_actual_scores():
    rng=np.random.default_rng(41);X=rng.normal(size=(120,4));f=pd.DataFrame(X,columns=list('abcd'));f['_row_id']=list(map(str,range(120)))
    r=pca_run(X);run=dict(id=db.uid(),config=dict(method='pca',feature_ids=list('abcd'),settings={}),provenance={})
    b=build(run,r,f);plot=figure(b,'scores')
    assert plot.data[0].type=='scatter'
    np.testing.assert_allclose(plot.data[0].x,r['scores'][:,0]);np.testing.assert_allclose(plot.data[0].y,r['scores'][:,1])
    assert 'PC1' in plot.layout.xaxis.title.text and '%' in plot.layout.yaxis.title.text
    assert len(plot.data[0].x)==len(f)

def test_cluster_visual_centroids_and_names_are_fitted_values():
    X=np.array([[0,1],[.1,1.1],[.2,1],[3,5],[3.2,4.9],[2.9,5.1]])
    raw=cluster_run(X,'kmeans',dict(k=2));f=pd.DataFrame(X,columns=['a','b']);f['_row_id']=list(map(str,range(6)))
    run=dict(id=db.uid(),config=dict(method='kmeans',feature_ids=['a','b'],settings={}),provenance=dict(feature_labels=['Likuiditas','Profitabilitas']))
    b=build(run,raw,f);plot=figure(b,'profiles')
    assert [t.name for t in plot.data]==['Likuiditas','Profitabilitas']
    for i,t in enumerate(plot.data):np.testing.assert_allclose(t.y,raw['centroids'][:,i])
    assert len(b['result']['visual_manifest'])==1
    for i,row in enumerate(b['tables']['membership']['rows']):assert row['cluster']==int(raw['labels'][i])+1
    assert [r['cluster'] for r in b['tables']['clusters']['rows']]==[1,2]
    assert sorted(set(r['cluster'] for r in b['tables']['visual_profiles']['rows']))==[1,2]

def test_presentation_covers_data_method_math_example_evaluation_and_limits(evidence):
    frame,run,raw,bundle=evidence;s=sections_for_run(run,bundle,raw,frame)
    keys={v['id'].removeprefix(run['id']+'_') for v in s}
    assert {'data_context','variables','procedure','formula','example','summary','confusion_matrix','precision_recall','decisions','reproduction','limitations'}<=keys
    decisions=next(v for v in s if v['id'].endswith('_decisions'))
    assert decisions['rows'][0]['terdeteksi']==12 and decisions['rows'][1]['terdeteksi']==28
    assert decisions['rows'][1]['alarm_keliru']==59
    example=next(v for v in s if v['id'].endswith('_example'))
    assert 'TW03598' in example['title'] and '0.99342294' in example['paragraphs'][1]

def test_pdf_uses_selected_order_and_full_content(tmp_path,evidence):
    from backend.pdf_report import write_report
    from pypdf import PdfReader
    frame,run,raw,bundle=evidence;sections=sections_for_run(run,bundle,raw,frame)
    selected=[next(s for s in sections if s['id'].endswith('_decisions')),next(s for s in sections if s['id'].endswith('_data_context'))]
    out=tmp_path/'audit.pdf';write_report(out,[bundle],selected,run['id'])
    reader=PdfReader(out);assert len(reader.pages)==2
    assert 'Deteksi dan alarm' in reader.pages[0].extract_text()
    assert 'Apa yang diamati' in reader.pages[1].extract_text()
    assert '59' in reader.pages[0].extract_text()

def test_liquidity_names_are_not_misclassified_as_identifiers():
    from backend.service import import_confirm,dataframe
    id=db.uid();path=db.folder(id)/'numbers.csv';path.write_text('ID,Likuiditas,Liquidity,company_id\n001,1.2,2.3,004\n002,2.1,3.2,005\n003,3.1,4.2,006\n')
    d=import_confirm(dict(path=str(path),filename='numbers.csv',project_id='test',inspection=dict(delimiter=',')),dict(decimal='.'))
    assert [c['assigned_type'] for c in d['columns']]==['text','number','number','text']
    assert dataframe(d).c0.tolist()==['001','002','003']

def test_parallel_analysis_plots_the_same_quantile_used_for_retention(tmp_path):
    from backend.factors import efa_run
    rng=np.random.default_rng(9);factors=rng.normal(size=(350,2));L=np.array([[.8,.1],[.7,.1],[.9,.1],[.1,.8],[.1,.7],[.1,.9]])
    X=factors@L.T+rng.normal(size=(350,6))*.3
    out=efa_run(X);pa=out['parallel'];observed=np.array(pa['observed']);boundary=np.array(pa['simulated']);mean=np.array(pa['simulation_mean'])
    assert len(boundary)==6 and np.all(boundary>=mean-1e-10)
    not_greater=np.flatnonzero(observed<=boundary);retained=int(not_greater[0]) if len(not_greater) else 6
    assert retained==pa['recommended']==out['q']==2

def test_pca_pdf_does_not_substitute_a_classification_formula(tmp_path):
    from backend.pdf_report import write_report
    from pypdf import PdfReader
    X=np.random.default_rng(3).normal(size=(30,3));f=pd.DataFrame(X,columns=['a','b','c']);f['_row_id']=list(map(str,range(30)))
    raw=pca_run(X);run=dict(id=db.uid(),config=dict(method='pca',feature_ids=['a','b','c'],settings={}),provenance={})
    b=build(run,raw,f);s=next(v for v in sections_for_run(run,b,raw,f) if v['id'].endswith('_formula'))
    p=tmp_path/'pca.pdf';write_report(p,[b],[s],run['id']);text=PdfReader(p).pages[0].extract_text()
    assert 'Skor T = Z A' in text and 'exp(' not in text

def test_presentation_does_not_drop_indicators_beyond_eight():
    X=np.random.default_rng(4).normal(size=(100,12));names=[f'Indikator {i}' for i in range(12)]
    f=pd.DataFrame(X,columns=names);f['_row_id']=list(map(str,range(100)))
    raw=pca_run(X);run=dict(id=db.uid(),config=dict(method='pca',feature_ids=names,settings={}),provenance={})
    bundle=build(run,raw,f);sections=sections_for_run(run,bundle,raw,f)
    variables=[s for s in sections if '_variables' in s['id']]
    assert [r['indikator'] for s in variables for r in s['rows']]==names
    assert all(len(s['rows'])<=8 for s in variables)

def test_oblique_pattern_heatmap_does_not_clip_coefficients_above_one():
    b=dict(result=dict(run_id='test',provenance={},subset_definitions=dict(all=dict(n=100)),visual_manifest=[dict(id='loadings',kind='heatmap',title='Loading',subset_id='all',reason_text='Pattern')]),visuals=dict(loadings=dict(data=[dict(feature='a',pattern=[1.2,-.2]),dict(feature='b',pattern=[.8,.1])])))
    p=figure(b,'loadings')
    assert p.data[0].zmax==1.2 and p.data[0].zmin==-1.2
    assert p.data[0].z[0][0]==1.2
