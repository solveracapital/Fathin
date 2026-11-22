"""Presentation-first planning. Select valid procedures; explain questions that cannot be fitted."""
from copy import deepcopy
import re
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from scipy import linalg
from . import service,storage as db
from .statistics import transform_fit,split_indices,lda_fit,lda_run,cluster_run,time_values
from .factors import efa_run,parallel_analysis

QUESTIONS={'pca':('Merangkum indikator','Seberapa banyak informasi dapat diringkas menjadi beberapa komponen?'),
           'efa':('Memahami faktor bersama','Apakah hubungan antarindikator dapat dijelaskan oleh faktor bersama?'),
           'kmeans':('Mengenali kelompok','Kelompok profil apa yang muncul dari kemiripan data?'),
           'hierarchical':('Melihat susunan kelompok','Bagaimana kelompok bergabung secara bertahap?'),
           'lda':('Membedakan dua kelas','Seberapa baik indikator membedakan dua label yang sudah diketahui?')}

def token(name):return re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')

def independent_columns(X):
    _,R,piv=linalg.qr(X,mode='economic',pivoting=True)
    tol=max(X.shape)*np.finfo(float).eps*max(float(np.abs(R).max()),1)*100
    rank=int(np.sum(abs(np.diag(R))>tol))
    return sorted(int(i) for i in piv[:rank])

def choose_k(X,seed=42,method='kmeans'):
    rng=np.random.default_rng(seed);ix=np.sort(rng.choice(len(X),min(800,len(X)),replace=False));sample=X[ix]
    maximum=min(6,len(sample)-1,len(np.unique(sample,axis=0)))
    candidates=[]
    for k in range(2,maximum+1):
        result=cluster_run(sample,method,dict(k=k,linkage='ward',metric='euclidean'),seed)
        if result['silhouette'] is not None:candidates.append(dict(k=k,silhouette=float(result['silhouette'])))
    if not candidates:raise ValueError('Data tidak mempunyai cukup profil berbeda untuk membentuk dua kelompok yang dapat dibandingkan.')
    best=max(candidates,key=lambda r:(r['silhouette'],-r['k']))
    return best['k'],dict(candidates=candidates,sample_n=len(sample),population_n=len(X),seed=seed)

def create_plan(dataset_id):
    d=db.get(dataset_id,'dataset');frame=service.dataframe(d);columns=d['columns'];n=len(frame)
    names={c['id']:c.get('display_name',c['source_name']) for c in columns}
    roles={c['id']:c.get('role','ignored') for c in columns}
    semantics={c['id']:token(c['source_name']) for c in columns}
    notes=[];target=None
    marked=[c['id'] for c in columns if roles[c['id']]=='target']
    candidates=marked or [c['id'] for c in columns if semantics[c['id']] in ('target','label','class','kelas','status','bankrupt','bankruptcy','bangkrut','outcome','y')]
    if len(candidates)==1 and frame[candidates[0]].dropna().nunique()==2:target=candidates[0]
    elif len(candidates)>1:notes.append('Beberapa kolom tampak sebagai label. Sistem tidak menebak makna label; pembahasan pembedaan kelas dijelaskan tanpa membentuk classifier.')
    excluded=[];features=[]
    for c in columns:
        key=c['id'];name=semantics[key];s=frame[key]
        identity=re.search(r'(?:^|_)(id|identifier|identitas|kode|code)(?:$|_)',name)
        protected=roles[key] in ('target','id','entity','time') or key in candidates or identity or name in ('train','test','split','partition','fold','year','tahun','date','tanggal','time','waktu')
        if protected:excluded.append(dict(column=names[key],reason='Identitas, label, atau pembagian/waktu; tidak dijadikan indikator.'));continue
        if not is_numeric_dtype(s):excluded.append(dict(column=names[key],reason='Kolom teks; tidak diubah menjadi angka secara sembarang.'));continue
        x=s.to_numpy(float)
        if np.isinf(x).any() or s.nunique(dropna=True)<2:excluded.append(dict(column=names[key],reason='Nilai tidak finite atau tidak bervariasi; tidak memberi informasi yang layak untuk metode ini.'));continue
        features.append(key)
    missing=int(frame[features].isna().sum().sum()) if features else 0
    preprocessing=dict(missing='median' if missing else 'error',scale='none')
    if missing:notes.append(f'{missing} nilai indikator yang kosong diisi median secara otomatis; untuk klasifikasi, median hanya dipelajari dari data pelatihan.')
    notes.append('Analisis mendeskripsikan pola pada data tersimpan; hasil tidak menetapkan hubungan sebab-akibat atau validitas operasional di populasi baru.')
    project=db.get(d['project_id'],'project')
    source=db.ROOT/'outputs/makalah_multivariat/Data_Analisis.csv'
    paper=project.get('case_type')=='taiwan_paper' and source.exists() and d['source_sha256']==db.digest(source.read_bytes())
    purpose='Pembahasan makalah Taiwan; EFA dan gerombol adalah eksplorasi tambahan.' if paper else 'Laporan otomatis untuk memahami beberapa indikator pada data ini.'
    methods=[]
    def entry(method):
        title,question=QUESTIONS[method]
        return dict(method=method,title=title,question=question,status='explained',explanation='',decisions=[],config=None)
    def cfg(method,selected=None):return dict(dataset_version_id=d['id'],purpose=purpose,method=method,feature_ids=list(features if selected is None else selected),target_id=target,positive_label=None,preprocessing=deepcopy(preprocessing),split=dict(seed=42),settings={})
    def accept(item,config,explanation,decisions):
        decisions=decisions+notes
        if excluded:decisions=decisions+['Kolom sumber yang tidak dijadikan indikator: '+'; '.join(e['column']+' ('+e['reason']+')' for e in excluded)]
        config['settings']['automatic_decisions']=decisions
        check=service.validate(config)
        if check['blocking']:raise ValueError(check['blocking'][0]['message'])
        item.update(status='ready',config=config,explanation=explanation,decisions=decisions)
    for method in QUESTIONS:
        item=entry(method)
        try:
            if not features or n<3:raise ValueError('Belum ada cukup rekaman dan indikator numerik yang bervariasi. Data tetap dijelaskan; angka model tidak dibuat-buat.')
            X,_=transform_fit(frame[features].to_numpy(float),preprocessing)
            if method=='pca':
                if len(features)<2:raise ValueError('Hanya satu indikator numerik yang layak. Merangkum beberapa indikator dengan PCA tidak diperlukan pada data ini.')
                config=cfg(method);config['settings']=dict(basis='correlation',target=.8)
                if paper:
                    split_column=next((key for key,name in semantics.items() if name=='train'),None)
                    if split_column:config['settings']['subset']='train';config['split']['column_id']=split_column
                accept(item,config,'Sistem merangkum variasi indikator menjadi komponen yang lebih sedikit.',[
                    'Varians indikator disetarakan agar perbedaan satuan tidak mendominasi.',
                    'Jumlah komponen dipilih otomatis untuk merangkum sedikitnya 80% variasi.',
                    'Untuk contoh makalah, PCA memakai bagian train yang tersimpan.' if paper else 'Ringkasan memakai semua rekaman yang tersedia; bukan ukuran akurasi prediksi.'])
            elif method=='efa':
                corr_X=(X-X.mean(0))/X.std(0,ddof=1);keep=independent_columns(corr_X)
                selected=[features[i] for i in keep];Z=X[:,keep]
                if len(selected)<3 or n<=len(selected):raise ValueError('Analisis faktor memerlukan sedikitnya tiga indikator independen dan jumlah rekaman yang lebih besar. Pada data ini, syarat tersebut belum terpenuhi.')
                pa=parallel_analysis(np.corrcoef(Z,rowvar=False),n,42);recommended=pa['recommended']
                if recommended<1:raise ValueError('Perbandingan dengan data acak tidak mendukung faktor bersama. Kesimpulannya adalah belum ada dukungan faktor; bukan kegagalan pengaturan.')
                feasible=[q for q in range(1,min(recommended,len(selected)-1)+1) if len(selected)*(len(selected)-1)/2-len(selected)*q+q*(q-1)/2>=0]
                chosen=None;attempts=[]
                for q in reversed(feasible):
                    try:efa_run(Z,q=q,seed=42);chosen=q;break
                    except ValueError as exc:attempts.append(dict(q=q,reason=str(exc)))
                if chosen is None:raise ValueError('Pola korelasi belum menghasilkan model faktor yang layak. Laporan menjelaskan batas ini; hasil faktor yang tidak teridentifikasi atau tidak konvergen tidak dipaksakan.')
                config=cfg(method,selected);config['settings']=dict(q=chosen,extraction='pa',rotation='oblimin',automatic_factor_selection=dict(recommended=recommended,chosen=chosen,attempts=attempts))
                decisions=[f'Simulasi menyarankan {recommended} faktor; model yang memenuhi syarat numerik menggunakan {chosen} faktor.',
                           'Principal axis digunakan untuk faktor bersama, dengan oblimin agar faktor boleh berkorelasi.',
                           'Nama dan makna faktor tetap dibaca dari indikator; kelayakan numerik tidak mengonfirmasi konstruk.']
                if len(selected)!=len(features):decisions.append('Indikator yang bergantung linear tidak dipakai pada EFA; daftar indikator yang benar-benar digunakan tersimpan di laporan.')
                accept(item,config,'Sistem mengeksplorasi pola faktor bersama dengan pemeriksaan kelayakan terlebih dahulu.',decisions)
            elif method in ('kmeans','hierarchical'):
                config=cfg(method);config['preprocessing']['scale']='standard';part=frame
                if method=='hierarchical' and n>1000:
                    ids=np.sort(np.random.default_rng(42).choice(n,1000,replace=False));part=frame.iloc[ids]
                    config['settings']['sample_row_ids']=part['_row_id'].astype(str).tolist()
                xx,_=transform_fit(part[features].to_numpy(float),config['preprocessing']);k,selection=choose_k(xx,method=method)
                config['settings'].update(k=k,automatic_k_selection=selection)
                if method=='hierarchical':config['settings'].update(linkage='ward',metric='euclidean')
                decisions=[f'{k} kelompok dipilih dengan membandingkan pemisahan pada calon jumlah kelompok 2–6 yang memenuhi syarat.',
                           f'Perbandingan silhouette {"Ward" if method=="hierarchical" else "K-means"} memakai {selection["sample_n"]} dari {selection["population_n"]} rekaman secara deterministik; bukan bukti jumlah kelompok benar secara universal.',
                           'Indikator disetarakan; nomor kelompok bukan peringkat risiko.']
                score=max(c['silhouette'] for c in selection['candidates'])
                decisions.append(f'Nilai silhouette calon terpilih adalah {score:.4f}. Pemisahan yang lemah tetap dilaporkan sebagai pola eksploratori, bukan bukti kelompok alami yang pasti.')
                if len(part)!=n:decisions.insert(0,f'Pohon menggunakan contoh acak tetap {len(part)} dari {n} rekaman agar dapat dihitung dan dibaca. Ini bukan hierarki seluruh data.')
                accept(item,config,'Sistem mencari kemiripan profil dan menjelaskan ciri setiap kelompok.',decisions)
            else:
                if target is None:raise ValueError('Tidak ditemukan satu kolom label dua kelas yang maknanya cukup jelas dari nama/peran kolom. Tanpa label yang diketahui, pembedaan kelas tidak dapat dievaluasi; gunakan hasil komponen, faktor, dan kelompok yang sesuai.')
                if frame[target].isna().any():raise ValueError('Sebagian label kelas kosong. Sistem tidak menebak label agar akurasi tidak menyesatkan.')
                values=frame[target].unique().tolist();positive=next((v for v in values if v in (1,True,'1','yes','Yes','positif','positive','bangkrut')),sorted(values,key=str)[-1])
                y=(frame[target]==positive).to_numpy(int);config=cfg(method);config['positive_label']=positive;config['split'].update(mode='stratified_random',test_size=.3)
                if paper:
                    key=next((key for key,name in semantics.items() if name=='train'),None)
                    if key:config['split'].update(mode='saved_membership',column_id=key,reconstruct_order=True)
                else:
                    entities=[key for key,name in semantics.items() if roles[key]=='entity' or (re.search(r'(?:^|_)(id|entity|entitas)(?:$|_)',name) and frame[key].nunique()<n)]
                    times=[key for key,name in semantics.items() if roles[key]=='time' or name in ('date','tanggal','time','waktu','year','tahun')]
                    if entities and times:raise ValueError('Data memuat entitas berulang dan waktu sekaligus. Validasi yang aman memerlukan rancangan longitudinal khusus; laporan tidak mengklaim akurasi dari pembagian acak yang bisa membocorkan informasi.')
                    if len(entities)>1 or len(times)>1:raise ValueError('Beberapa kolom entitas/waktu ditemukan; sistem tidak menebak rancangan evaluasi yang dapat mengubah arti akurasi.')
                    if entities:config['split'].update(mode='group',column_id=entities[0])
                    elif times:
                        key=times[0]
                        time_format='year' if semantics[key] in ('year','tahun') else 'date'
                        dates=time_values(frame[key],dict(time_format=time_format))
                        if dates.isna().any():raise ValueError('Kolom waktu mempunyai nilai kosong; urutan evaluasi tidak dapat ditebak.')
                        ordered=dates.sort_values().unique()
                        if len(ordered)<2:raise ValueError('Kolom waktu hanya mempunyai satu periode; evaluasi pada periode berikutnya belum tersedia.')
                        cutoff=ordered[min(len(ordered)-1,max(1,int(len(ordered)*.7)))]
                        config['split'].update(mode='temporal',column_id=key,cutoff=pd.Timestamp(cutoff).isoformat(),time_format=time_format)
                train,test=split_indices(frame,y,config['split'])
                if len(np.unique(y[train]))!=2 or np.bincount(y[train]).min()<2:raise ValueError('Jumlah contoh kelas terlalu kecil untuk memisahkan pelatihan dan evaluasi dengan layak. Akurasi tidak diklaim dari data yang dipakai belajar sendiri.')
                Xt,_=transform_fit(frame.iloc[train][features].to_numpy(float),preprocessing)
                within=Xt-np.vstack([Xt[y[train]==g].mean(0) for g in (0,1)])[y[train]]
                keep=independent_columns(within)
                if not keep:raise ValueError('Tidak ada variasi dalam kelas yang cukup untuk mengestimasi model diskriminan.')
                config['feature_ids']=[features[i] for i in keep]
                lda_fit(Xt[:,keep],y[train])
                minority=int(np.bincount(y[train]).min());folds=min(5,minority//2)
                config['settings'].update(prior='empirical',threshold=.5,oof=folds>=2,folds=max(2,folds))
                oof_reason=None
                try:lda_run(frame,config['feature_ids'],target,positive,preprocessing,config['split'],config['settings'])
                except ValueError as exc:
                    if not config['settings']['oof']:raise
                    config['settings']['oof']=False;oof_reason=str(exc)
                    lda_run(frame,config['feature_ids'],target,positive,preprocessing,config['split'],config['settings'])
                split_message='Pembagian train/test dan bobot kelas mengikuti contoh makalah.' if paper else {'stratified_random':'Sebanyak 70% data menjadi train dan 30% test, dengan proporsi kelas dijaga.','group':'Entitas yang sama tidak ditempatkan pada train dan test sekaligus.','temporal':'Periode awal menjadi train; periode berikutnya menjadi test agar urutan waktu dijaga.'}[config['split']['mode']]
                accept(item,config,'Sistem mempelajari dua kelas pada data pelatihan, lalu mengevaluasinya pada data yang dipisahkan.',[
                    f'Label dibaca dari {names[target]}; kelas positif = {positive}. Ini konvensi label, bukan penilaian baik/buruk otomatis.',
                    split_message,
                    'Ambang tambahan dipilih dari prediksi silang train; test tetap untuk evaluasi.' if config['settings']['oof'] else 'Pemilihan ambang tambahan tidak dilakukan karena validasi silang belum layak; ambang utama tetap 0,5.'+(' Alasan pemeriksaan: '+oof_reason if oof_reason else ''),
                    'Kolom yang bergantung linear dipilih hanya dari train; data test tidak ikut menentukan indikator model.'])
        except (ValueError,KeyError,TypeError,IndexError,linalg.LinAlgError) as exc:
            item['explanation']=str(exc)
            item['decisions']=['Keterangan ini merekam kelayakan input; estimasi model tidak diterbitkan.']
        methods.append(item)
    plan=dict(id=db.uid(),project_id=d['project_id'],dataset_version_id=d['id'],source_sha256=d['source_sha256'],created_at=db.now(),policy_version='presentation-auto-1',row_count=n,feature_ids=features,feature_names=[names[c] for c in features],target_id=target,target_name=names.get(target),excluded=excluded,notes=notes,analyses=methods)
    plan['plan_hash']=db.digest(db.dumps({k:v for k,v in plan.items() if k not in ('id','created_at')}).encode())
    return db.put('autoplan',plan)

def coverage_sections(suite,plan):
    sections=[]
    for item in suite['analyses']:
        if item['status']!='explained':continue
        _,question=QUESTIONS[item['method']]
        sections.append(dict(id=suite['id']+'_assessment_'+item['method'],kind='content',suite_id=suite['id'],run_id=None,title='Kelayakan: '+QUESTIONS[item['method']][0],enabled=True,
                             paragraphs=[question,item['explanation'],'Penjelasan ini merupakan hasil penelaahan kelayakan data, bukan hasil estimasi model. '+ ' '.join(item.get('decisions',[])),
                                         'Keluaran metode bergantung pada struktur data dan tujuan analisis. Keterangan kelayakan menetapkan batas kesimpulan ilmiah pada data yang tersedia.'],
                             rows=[],columns=[],formula=None,formula_text=None,source_sha256=plan['source_sha256'],evidence_ids=[plan['id']]))
    return sections
