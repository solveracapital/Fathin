"""Build result views once; charts and tables reference the same stored values."""
import numpy as np
from .storage import clean

def build(run,raw,frame):
    method=run['config']['method']; features=run['config']['feature_ids']; rid=run['id']
    labels=run['provenance'].get('feature_labels',features)
    titles={'confusion_matrix':'Kasus yang terdeteksi dan terlewat','precision_recall':'Ketepatan sinyal dan cakupan deteksi','roc':'Kurva ROC','scree':'Variasi setiap komponen','scores':'Proyeksi observasi pada PC1 dan PC2','profiles':'Pusat indikator menurut kelompok','dendrogram':'Urutan penggabungan kelompok','loadings':'Pola loading faktor','parallel_analysis':'Faktor teramati dan data acak'}
    default_subset='train' if method=='pca' and run['config'].get('settings',{}).get('subset')=='train' else 'all'
    tables={}; visuals={}; manifest=[]; metrics=[]; diagnostics=[]
    def table(id,rows,subset='all'):
        if subset=='all':subset=default_subset
        rows=clean(rows); keys=list(rows[0]) if rows else []
        tables[id]=dict(id=id,title=id,columns=[dict(key=k,label=k,type='number' if rows and isinstance(rows[0].get(k),(float,int)) else 'text',unit='none',precision=6) for k in keys],rows=rows,row_count=len(rows),subset_id=subset,evidence_ids=[id])
        return id
    def visual(id,kind,data,subset='all',status='shown',reason='Sesuai tujuan dan hasil analisis.',projection=None):
        if subset=='all':subset=default_subset
        rows=[dict(index=i,**v) if isinstance(v,dict) else dict(index=i,value=v) for i,v in enumerate(data)] if isinstance(data,list) else [dict(key=k,value=v) for k,v in data.items()]
        if kind in ('roc','precision_recall'):
            xname,yname=('false_positive_rate','sensitivity') if kind=='roc' else ('recall','precision')
            rows=[{xname:x,yname:data['y'][i],'threshold':data.get('thresholds',[])[i] if i<len(data.get('thresholds',[])) else None} for i,x in enumerate(data['x'])]
        elif kind=='confusion_matrix':
            rows=[dict(actual=data['labels'][i],predicted=data['labels'][j],count=data['matrix'][i][j]) for i in range(2) for j in range(2)]
        elif kind=='bar':
            rows=[dict(cluster=r['cluster']+1,feature=labels[j],center=value,n=r['count']) for r in data for j,value in enumerate(r['centroid'])]
        elif kind=='dendrogram':
            rows=[dict(merge=i,left=v[0],right=v[1],height=v[2],members=v[3]) for i,v in enumerate(data['linkage'])]
        elif kind=='heatmap':
            rows=[dict(feature=r.get('label',r['feature']),factor=j+1,pattern=value) for r in data for j,value in enumerate(r['pattern'])]
        elif kind=='line' and isinstance(data,dict) and 'observed' in data and 'simulated' in data:
            rows=[dict(factor=i+1,observed=value,simulated_95=data['simulated'][i]) for i,value in enumerate(data['observed'])]
        ref=table('visual_'+id,rows,subset)
        visuals[id]=dict(data=clean(data),run_id=rid,subset_id=subset)
        if reason=='Sesuai tujuan dan hasil analisis.':
            reason={'confusion_matrix':'Jumlah kasus; baris aktual dan kolom prediksi. Persentase dibaca per baris aktual.','precision_recall':'Recall adalah bagian kasus positif yang ditemukan; precision adalah bagian sinyal yang benar. Garis bertangga mengikuti definisi average precision.','roc':'Sensitivity terhadap false positive rate; ringkasan pemeringkatan, bukan kalibrasi probabilitas.','scree':'Eigenvalue dihitung dari matriks yang dipilih pada konfigurasi PCA.','scores':'Koordinat proyeksi dua komponen; jarak pada dua sumbu tidak menggantikan seluruh dimensi.','profiles':'Pusat kelompok pada skala setelah pengolahan; nomor kelompok bukan peringkat risiko.','dendrogram':'Cabang dipotong ke 30 daun terakhir; angka dalam kurung adalah jumlah anggota cabang.','loadings':'Koefisien pattern setelah rotasi; bukan bukti konstruk telah terkonfirmasi.','parallel_analysis':'Spektrum faktor bersama dibandingkan dengan data acak; rekomendasi bukan hukum universal.'}.get(id,reason)
        manifest.append(dict(id=id,kind=kind,title=titles.get(id,id),purpose=reason,status=status,reason_code='ELIGIBLE',reason_text=reason,
          data_ref=f'/api/v1/runs/{rid}/visuals/{id}',subset_id=subset,axes={},series=[],encodings={},evidence_ids=[ref],projection=projection,sampling=None,default_order=len(manifest),table_alternative_ref=ref))
    if method=='lda':
        for subset,ev in raw['evaluations'].items():
            for m in ev['metrics']:metrics.append(dict(m,id=subset+'_'+m['id'],evidence_ids=[subset]))
            table(subset,[ev['counts']],ev['metrics'][0]['subset_id'])
        ev=raw['evaluations']['test']; visual('confusion_matrix','confusion_matrix',dict(matrix=ev['matrix'],orientation=ev['orientation'],labels=[raw['negative_label'],raw['positive_label']]),'test')
        for kind,data in ev['curves'].items():visual(kind,kind,data,'test','shown' if kind=='precision_recall' else 'available')
        model=raw['model']; table('coefficients',[dict(feature=f,b0=model['b'][0][j],b1=model['b'][1][j],canonical=model['a'][j],standardized=model['standardized'][j],structure=model['structure'][j]) for j,f in enumerate(features)],'train')
        table('model_summary',[dict(parameter=k,value=model[k]) for k in ('priors','centroids','eigenvalue','canonical_correlation','wilks','canonical_chi2','canonical_df','rank','condition_number','box_m')],'train')
        for name in ['W','B','Sp','means','group_covariances']:
            table(name,[dict(row=i,values=v) for i,v in enumerate(model[name])],'train')
        table('marginal',model['marginal'],'train')
        if model['box_m'] and model['box_m']['p_value']<.05:diagnostics.append(dict(code='UNEQUAL_COVARIANCE',severity='warning',title='Kovarians berbeda',explanation='Box M aproksimasi menentang kesamaan kovarians; evaluasi klasifikasi tetap dibaca terpisah.',evidence_ids=['marginal']))
        diagnostics.append(dict(code='INTERNAL_VALIDATION',severity='warning',title='Batas validasi',explanation='Evaluasi internal bukan bukti validitas temporal, kausal, atau kalibrasi pada populasi sasaran.',evidence_ids=['test']))
        train_members=set(raw['train']);test_members=set(raw['test'])
        table('predictions',[dict(row_id=str(frame.iloc[i]['_row_id']),actual=int(raw['y'][i]),posterior=raw['probability'][i],eta=raw['eta'][i],canonical_score=raw['canonical_scores'][i],subset='train' if i in train_members else 'test' if i in test_members else 'excluded_gap') for i in range(len(frame))])
        text=f"Dari {ev['counts']['TP']+ev['counts']['FN']} kasus positif test, {ev['counts']['TP']} terdeteksi dan {ev['counts']['FN']} terlewat. Terdapat {ev['counts']['FP']} alarm keliru."
    elif method=='pca':
        table('components',[dict(component=i+1,eigenvalue=v,PVE=raw['PVE'][i],cumulative=raw['cumulative'][i]) for i,v in enumerate(raw['eigenvalues'])])
        table('loadings',[dict(feature=f,label=labels[i],values=raw['loadings'][i]) for i,f in enumerate(features)])
        table('pca_directions',[dict(feature=f,values=raw['directions'][i]) for i,f in enumerate(features)])
        table('pca_scores',[dict(row_id=str(frame.iloc[i]['_row_id']),values=row) for i,row in enumerate(raw['scores'])])
        visual('scree','scree',tables['components']['rows'])
        if raw['rank']>=2:
            indices=np.linspace(0,len(frame)-1,min(3000,len(frame)),dtype=int)
            visual('scores','scatter',[dict(x=raw['scores'][i,0],y=raw['scores'][i,1],row_id=str(frame.iloc[i]['_row_id'])) for i in indices],status='available',projection=dict(basis='PCA',dimensions=[1,2],explained_variance=raw['PVE'][:2],scaling_convention='scores'))
            manifest[-1]['sampling']=dict(population_n=len(frame),displayed_n=len(indices),seed=None,strategy='evenly_spaced_source_order')
        metrics=[dict(id='PVE_selected',label='Varians terjelaskan',value=float(raw['cumulative'][raw['selected_q']-1]),unit='ratio',status='ok',reason=None,subset_id=default_subset,evidence_ids=['components'])]
        text=f"{raw['selected_q']} komponen dipilih untuk ringkasan variasi. PCA tidak mengukur akurasi klasifikasi."
    elif method in ('kmeans','hierarchical'):
        rows=[dict(cluster=i,count=int(raw['counts'][i]),centroid=raw['centroids'][i]) for i in range(len(raw['counts']))]
        table('clusters',[{**r,'cluster':r['cluster']+1} for r in rows]);visual('profiles','bar',rows)
        from .statistics import metric
        metrics=[metric('silhouette',raw['silhouette'],'all')]
        metrics[0]['label']='Silhouette (−1 sampai 1)'
        table('cluster_diagnostics',[dict(parameter=k,value=raw.get(k)) for k in ('inertia','iterations','silhouette','silhouette_sample_n','seed')])
        if raw.get('iterations') is not None and raw['iterations']>=300:diagnostics.append(dict(code='ITERATION_LIMIT',severity='warning',title='Batas iterasi tercapai',explanation='K-means mencapai batas 300 iterasi; tinjau stabilitas solusi sebelum interpretasi.',evidence_ids=['cluster_diagnostics']))
        table('membership',[dict(row_id=str(frame.iloc[i]['_row_id']),cluster=int(v)+1) for i,v in enumerate(raw['labels'])])
        if raw['tree'] is not None:visual('dendrogram','dendrogram',dict(linkage=raw['tree'],truncate_last=30,convention='Euclidean Ward variance' if run['config']['settings'].get('linkage','ward')=='ward' else run['config']['settings'].get('linkage')))
        text='Kelompok menggambarkan kemiripan fitur; nomor kelompok bukan urutan risiko.'
    else:
        table('factor_loadings',[dict(feature=f,label=labels[i],pattern=raw['pattern'][i],structure=raw['structure'][i],communality=raw['communalities'][i],uniqueness=raw['uniqueness'][i]) for i,f in enumerate(features)])
        visual('loadings','heatmap',tables['factor_loadings']['rows'])
        from .statistics import metric
        metrics=[metric('KMO',raw['kmo'],'all')]
        if raw['kmo']<.5:diagnostics.append(dict(code='LOW_KMO',severity='warning',title='Kelayakan faktor perlu ditinjau',explanation='KMO kurang dari 0,5; pola korelasi kurang mendukung pemodelan faktor bersama. Batas ini kebijakan diagnostik, bukan bukti konstruk.',evidence_ids=['factor_diagnostics']))
        table('factor_diagnostics',[dict(parameter=k,value=raw[k]) for k in ('Phi','residual','msa','bartlett','warnings','versions')])
        if raw.get('scores') is not None:table('factor_scores',[dict(row_id=str(frame.iloc[i]['_row_id']),values=row) for i,row in enumerate(raw['scores'])])
        if raw.get('parallel'):visual('parallel_analysis','line',raw['parallel'])
        text='Faktor bersifat eksploratori; nama konstruk memerlukan alasan substantif.'
    for d in diagnostics:d.update(affected_column_ids=[],suggested_actions=['Tinjau batas interpretasi.'])
    table('preprocessing',[dict(parameter=k,value=v) for k,v in raw.get('transform',{}).items()],'train' if method=='lda' else default_subset)
    definitions={k:dict(n=len(raw[k])) for k in ('train','test','excluded') if k in raw}
    if not definitions:definitions={default_subset:dict(n=len(frame))}
    result=dict(schema_version='1.0.0',run_id=rid,method=method,subset_definitions=definitions,metrics=metrics,table_index=[{k:v for k,v in t.items() if k!='rows'} for t in tables.values()],formula_index=[dict(id='method_formula',title=method,latex={'lda':r'\eta=x^T(b_1-b_0)+c_1-c_0;\quad p_1=\mathrm{expit}(\eta)','pca':r'T=ZA;\quad PVE_k=\lambda_k/\sum_j\lambda_j','efa':r'\Sigma=L\Phi L^T+\Psi'}.get(method,r'J=\sum_g\sum_{i\in C_g}\|x_i-\mu_g\|^2'),symbol_definitions={'x':'Vektor fitur pada skala pengolahan'},convention='Lihat konfigurasi dan parameter tersimpan.',inputs=features,intermediate_table_ids=list(tables),output_refs=[],explanation=text)],diagnostics=diagnostics,narrative_blocks=[dict(id='summary',title='Interpretasi',text=text,evidence_ids=list(tables)[:2],severity='info',origin='deterministic',run_id=rid)],visual_manifest=manifest,provenance=run['provenance'])

    if method=='hierarchical':
        link=run['config'].get('settings',{}).get('linkage','ward')
        result['formula_index'][0]['latex']={
            'ward':r'\Delta J(A,B)=\frac{n_A n_B}{n_A+n_B}\|\mu_A-\mu_B\|^2',
            'average':r'd(A,B)=\frac{1}{n_A n_B}\sum_{i\in A}\sum_{j\in B}d(x_i,x_j)',
            'complete':r'd(A,B)=\max_{i\in A,j\in B}d(x_i,x_j)',
            'single':r'd(A,B)=\min_{i\in A,j\in B}d(x_i,x_j)'}[link]
    from .schemas import AnalysisResult
    AnalysisResult.model_validate(clean(result))
    return clean(dict(result=result,tables=tables,visuals=visuals))
