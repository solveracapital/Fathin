import json,os,sys,shutil,subprocess,zipfile,io,csv,importlib.metadata,time,re
from pathlib import Path
import pandas as pd
import numpy as np
from . import storage as db
from .statistics import lda_run,pca_run,cluster_run,transform_fit
from .results import build
from .factors import efa_run,prepare_factors

METHODS=['lda','pca','efa','kmeans','hierarchical']
def versions():return {p:importlib.metadata.version(p) for p in ['numpy','scipy','pandas','scikit-learn','fastapi','statsmodels']}
def guard_archive(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if sum(i.file_size for i in z.infolist())>250*1024**2:raise ValueError('Arsip expanded melebihi 250 MiB.')
        if any('..' in Path(i.filename).parts for i in z.infolist()):raise ValueError('Path arsip tidak aman.')

def inspect_upload(data,name,document=False):
    suffix=Path(name).suffix.lower()
    if len(data)>(20 if document else 50)*1024**2:raise ValueError('File melebihi batas ukuran.')
    if suffix in ('.xlsx','.docx'):
        if not data.startswith(b'PK'):raise ValueError('Signature ZIP tidak sesuai.')
        guard_archive(data)
    elif suffix=='.pdf':
        if not data.startswith(b'%PDF'):raise ValueError('Signature PDF tidak sesuai.')
    elif suffix!='.csv':raise ValueError('Format tidak didukung.')
    if suffix=='.xlsx':
        from openpyxl import load_workbook
        w=load_workbook(io.BytesIO(data),read_only=True,data_only=False,keep_links=False)
        sheets=w.sheetnames;w.close();return dict(sheet_names=sheets,requires_confirmation=True)
    if suffix=='.csv':
        text=data.decode('utf-8-sig',errors='strict')
        try:delimiter=csv.Sniffer().sniff(text[:8192],delimiters=',;\t|').delimiter
        except csv.Error:delimiter=','
        return dict(encoding='utf-8-sig',delimiter=delimiter,preview=text[:2000],requires_confirmation=True)
    return {}

def import_confirm(imp,options):
    if options.get('decimal','.') not in ('.',','):raise ValueError('Decimal harus titik atau koma.')
    if options.get('thousands')==options.get('decimal','.'):raise ValueError('Pemisah ribuan tidak boleh sama dengan decimal.')
    path=Path(imp['path']);data=path.read_bytes();suffix=Path(imp['filename']).suffix.lower()
    if suffix=='.xlsx':
        from openpyxl import load_workbook
        w=load_workbook(io.BytesIO(data),read_only=True,data_only=False,keep_links=False)
        sheet=options.get('sheet_name')
        if sheet not in w.sheetnames:raise ValueError('Pilih sheet yang tersedia.')
        if w[sheet].max_row>100001 or w[sheet].max_column>200:w.close();raise ValueError('Dimensi sheet melebihi batas.')
        rows=list(w[sheet].values);w.close()
        if any(isinstance(v,str) and v.startswith('=') for row in rows for v in row):raise ValueError('Formula ditemukan; unggah values-only.')
    else:
        if 'decimal' not in options:raise ValueError('Tentukan decimal secara eksplisit: titik atau koma.')
        text=data.decode(options.get('encoding','utf-8-sig'))
        rows=list(csv.reader(io.StringIO(text),delimiter=options.get('delimiter',imp['inspection']['delimiter'])))
    header=int(options.get('header_row',1))-1
    if header<0 or header>=len(rows):raise ValueError('Baris header tidak sah.')
    names=[str(v) if v is not None else f'Kolom {i+1}' for i,v in enumerate(rows[header])]
    if len(names)>200 or len(rows)-header-1>100000:raise ValueError('Maksimal 100000 baris dan 200 kolom.')
    if not names or not rows[header+1:]:raise ValueError('Dataset kosong.')
    records=[]
    for i,row in enumerate(rows[header+1:]):
        if len(row)!=len(names):raise ValueError(f'Lebar baris {header+i+2} tidak sama dengan header.')
        records.append(dict(zip([f'c{j}' for j in range(len(names))],row),_row_id=str(i+1),_source_row=header+i+2))
    frame=pd.DataFrame(records); columns=[]; assigned=options.get('column_types',{})
    for j,name in enumerate(names):
        id=f'c{j}';s=frame[id].replace('',None)
        typ=assigned.get(id)
        # ID-like names preserve text/leading zero. Numeric conversion requires an unambiguous locale.
        identifier_name=re.search(r'(?:^|[\W_])(id|identifier|identitas|kode|code)(?:$|[\W_])',name.lower()) is not None
        candidate=(typ=='number' or not identifier_name) and typ!='text'
        if candidate:
            ss=s.astype('string')
            thousands=options.get('thousands')
            if thousands:ss=ss.str.replace(thousands,'',regex=False)
            if options.get('decimal','.')==',':ss=ss.str.replace(',','.',regex=False)
            parsed=pd.to_numeric(ss,errors='coerce')
            if np.isinf(parsed.to_numpy(dtype=float,na_value=np.nan)).any():raise ValueError(f'Nilai tak hingga pada {name}.')
            if typ=='number' and (parsed.isna() & s.notna()).any():raise ValueError(f'Nilai nonnumerik pada {name}.')
            if not (parsed.isna() & s.notna()).any():s=parsed
        if typ=='text':s=s.map(lambda v:str(v) if pd.notna(v) else None)
        frame[id]=s
        num=pd.api.types.is_numeric_dtype(s)
        columns.append(dict(id=id,source_name=name,display_name=name,inferred_type='number' if num else 'text',assigned_type=typ or ('number' if num else 'text'),role='ignored',unit=None,source_index=j))
    id=db.uid();p=db.folder(id)/'data.json';db.write_json(p,frame.replace({np.nan:None}).to_dict('records'))
    obj=db.put('dataset',dict(id=id,project_id=imp['project_id'],source_sha256=db.digest(data),parser_version='1.0.0',filename=imp['filename'],sheet_name=options.get('sheet_name'),header_row=header+1,import_options=options,row_count=len(frame),columns=columns,path=str(p),created_at=db.now()))
    return obj

def dataframe(dataset):return pd.DataFrame(json.loads(Path(dataset['path']).read_text(encoding='utf-8')))
def profile(dataset):
    f=dataframe(dataset);out=[]
    for col in dataset['columns']:
        s=f[col['id']];numeric=pd.api.types.is_numeric_dtype(s)
        d=dict(column_id=col['id'],missing=int(s.isna().sum()),unique=int(s.nunique()),constant=s.nunique()<=1)
        if numeric:
            a=s.to_numpy(float);finite=a[np.isfinite(a)]
            d.update(nonfinite=int(np.isinf(a).sum()),mean=float(np.mean(finite)) if len(finite) else None,SD=float(np.std(finite,ddof=1)) if len(finite)>1 else None,quantiles=np.quantile(finite,[0,.25,.5,.75,1]).tolist() if len(finite) else [])
        out.append(d)
    return dict(status='succeeded',row_count=len(f),columns=out,duplicates=int(f[[c['id'] for c in dataset['columns']]].duplicated().sum()),diagnostics=[])

def validate(config):
    errors=[];warnings=[]
    try:
        d=db.get(config['dataset_version_id'],'dataset');f=dataframe(d);features=config['feature_ids'];method=config['method'];s=config.get('settings',{});split=config.get('split',{})
        if s.get('sample_row_ids'):
            ids=s['sample_row_ids']
            if len(ids)!=len(set(ids)) or not set(ids)<=set(f['_row_id'].astype(str)):raise ValueError('Identitas sampel tidak sah.')
            f=f[f['_row_id'].astype(str).isin(ids)].reset_index(drop=True)
        if config.get('preprocessing',{}).get('missing')=='drop':f=f.dropna(subset=features).reset_index(drop=True)
        if len(f)<3:raise ValueError('Minimal tiga baris eligible diperlukan.')
        seed=split.get('seed',42)
        if type(seed) is not int or not 0<=seed<=2147483647:raise ValueError('Seed harus bilangan bulat 0 sampai 2147483647.')
        for key in ('k','q','folds'):
            if key in s and s[key] is not None and (type(s[key]) is not int or s[key]<1):raise ValueError(f'{key} harus bilangan bulat positif.')
        if 'folds' in s and s['folds']<2:raise ValueError('OOF minimal dua fold.')
        if s.get('oof_estimator','pooled') not in ('pooled','sklearn_svd'):raise ValueError('Estimator OOF tidak didukung.')
        if method=='efa' and s.get('q') is not None:
            p=len(features);q=s['q']
            if q>=p or p*(p-1)/2-p*q+q*(q-1)/2<0:raise ValueError('Model faktor overspecified.')
        if method=='pca' and s.get('q') is not None and s['q']>len(features):raise ValueError('Jumlah komponen melebihi fitur.')
        if method not in METHODS:raise ValueError('Metode tidak tersedia.')
        if config.get('preprocessing',{}).get('scale','none') not in ('none','standard','robust'):raise ValueError('Skala tidak didukung.')
        if config.get('preprocessing',{}).get('missing','error') not in ('error','median','drop'):raise ValueError('Kebijakan missing tidak didukung.')
        if method=='pca' and s.get('basis','correlation') not in ('correlation','covariance'):raise ValueError('Basis PCA tidak didukung.')
        if method=='pca' and not 0<s.get('target',.8)<=1:raise ValueError('Target PVE harus 0..1.')
        if method=='efa' and s.get('extraction','pa') not in ('pa','ml'):raise ValueError('Ekstraksi EFA tidak didukung.')
        if method=='efa' and s.get('rotation','oblimin') not in ('oblimin','varimax','none'):raise ValueError('Rotasi tidak didukung.')
        if not features or len(features)!=len(set(features)):raise ValueError('Pilih fitur unik.')
        if method in ('pca','efa') and len(features)<2:raise ValueError('Metode ini memerlukan minimal dua fitur.')
        protected=[config.get('target_id'),split.get('column_id'),'_row_id','_source_row']
        if any(c in protected for c in features):raise ValueError('Target/identitas/split tidak boleh menjadi fitur.')
        for c in features:
            col=next((col for col in d['columns'] if col['id']==c),None)
            if col and col['role'] in ('target','id','entity','time'):raise ValueError('Kolom identitas/target/waktu tidak boleh menjadi fitur.')
            if not pd.api.types.is_numeric_dtype(f[c]):raise ValueError('Prediktor harus numerik.')
            if f[c].nunique()<=1:raise ValueError('Fitur konstan tidak dapat digunakan.')
        x=f[features].to_numpy(float)
        if np.isinf(x).any():raise ValueError('Nilai tak hingga ditemukan.')
        if np.isnan(x).any() and config.get('preprocessing',{}).get('missing','error')=='error':raise ValueError('Missing value memerlukan keputusan pengolahan.')
        if method=='lda':
            labels=f[config['target_id']]
            positive=config.get('positive_label');positive=positive.get('value') if isinstance(positive,dict) else positive
            if labels.isna().any() or labels.nunique()!=2 or positive not in labels.unique():raise ValueError('Target harus dua kelas dan positive_label harus sah.')
            if labels.value_counts().min()<2:raise ValueError('Kelas minoritas terlalu kecil.')
            from .statistics import split_indices
            yy=(labels==positive).to_numpy(int);tr,te=split_indices(f,yy,split)
            if not len(te) or len(np.unique(yy[tr]))!=2 or np.bincount(yy[tr]).min()<2:raise ValueError('Train tidak mempunyai minimal dua observasi per kelas atau test kosong.')
            if s.get('oof'):
                folds=min(s.get('folds',5),int(np.bincount(yy[tr]).min()))
                if folds<2:raise ValueError('Jumlah fold OOF tidak sah.')
                if folds<s.get('folds',5):warnings.append(dict(code='REDUCED_FOLDS',message=f'OOF menggunakan {folds} fold karena jumlah kelas minoritas.'))
        if method=='efa' and (len(features)<3 or len(f)<=len(features)):raise ValueError('EFA memerlukan minimal 3 indikator dan observasi lebih banyak daripada indikator.')
        if method=='efa':
            prepared,_=transform_fit(x,config.get('preprocessing',{}))
            _,factor_count,_=prepare_factors(prepared,s.get('q'),seed)
            if s.get('q') is None:warnings.append(dict(code='AUTO_FACTORS',message=f'Parallel analysis memilih {factor_count} faktor; konvergensi dan keunikan tetap diperiksa saat estimasi.'))
        if method in ('kmeans','hierarchical'):
            k=s.get('k',3)
            if not 2<=k<len(f) or k>len(np.unique(x,axis=0)):raise ValueError('K harus minimal 2, kurang dari jumlah observasi, dan tidak melebihi titik unik.')
            metric=s.get('metric','euclidean')
            if method=='kmeans' and metric!='euclidean':raise ValueError('K-means hanya menggunakan Euclidean.')
            if method=='hierarchical' and (s.get('linkage','ward') not in ('ward','average','complete','single') or metric not in ('euclidean','cityblock','manhattan')):raise ValueError('Linkage atau jarak tidak didukung.')
        if method=='hierarchical' and len(f)>3000:raise ValueError('Batas hierarchical adalah 3000 observasi.')
        if method=='hierarchical' and s.get('linkage','ward')=='ward' and s.get('metric','euclidean')!='euclidean':raise ValueError('Ward hanya Euclidean.')
        if len(features)>20:warnings.append(dict(code='LARGE_FEATURE_SET',message='Heatmap lengkap tidak ditampilkan default.'))
    except (KeyError,ValueError,TypeError,IndexError,OverflowError) as e:errors.append(dict(code='INVALID_ANALYSIS',message=str(e)))
    return dict(blocking=errors,warnings=warnings,estimated_work=None,plan=dict(method=config.get('method'),features=config.get('feature_ids'),split=config.get('split'),automatic_deletion=False))

def execute(run):
    cfg=run['config'];d=db.get(cfg['dataset_version_id'],'dataset');f=dataframe(d);features=cfg['feature_ids'];settings=cfg.get('settings',{});options=cfg.get('preprocessing',{})
    source_n=len(f)
    if settings.get('sample_row_ids'):f=f[f['_row_id'].astype(str).isin(settings['sample_row_ids'])].reset_index(drop=True)
    if options.get('missing')=='drop':f=f.dropna(subset=features).reset_index(drop=True)
    run['provenance']=dict(source_sha256=d['source_sha256'],dataset_version_id=d['id'],config_hash=db.digest(db.dumps(cfg).encode()),engine_versions=versions(),visual_policy_version='1.0.0')
    run['provenance']['feature_labels']=[next((c.get('display_name',c.get('source_name',name)) for c in d['columns'] if c['id']==name),name) for name in features]
    run['provenance']['feature_ids']=features
    run['provenance']['source_row_count']=source_n
    run['provenance']['automatic_decisions']=settings.get('automatic_decisions',[])
    if settings.get('sample_row_ids'):run['provenance']['sampling']=dict(population_n=source_n,used_n=len(f),seed=42,strategy='fixed_random_source_rows')
    if cfg['method']=='lda':
        positive=cfg.get('positive_label');positive=positive.get('value') if isinstance(positive,dict) else positive
        raw=lda_run(f,features,cfg['target_id'],positive,options,cfg.get('split',{}),settings)
        run['provenance']['target_label']=next((c.get('display_name',c.get('source_name',cfg['target_id'])) for c in d['columns'] if c['id']==cfg['target_id']),cfg['target_id'])
        run['provenance']['positive_label']=raw['positive_label'];run['provenance']['negative_label']=raw['negative_label']
        run['provenance']['split_manifest_hash']=db.digest(db.dumps(dict(train=f.iloc[raw['train']]['_row_id'].tolist(),test=f.iloc[raw['test']]['_row_id'].tolist())).encode())
    else:
        if cfg['method'] in ('kmeans','hierarchical') and 'scale' not in options:options={**options,'scale':'standard'}
        if cfg['method']=='pca' and settings.get('subset')=='train':
            f=f[f[cfg['split']['column_id']]==1].reset_index(drop=True)
        x,t=transform_fit(f[features].to_numpy(float),options)
        if cfg['method']=='pca':raw=pca_run(x,settings.get('basis','correlation'),settings.get('q'),settings.get('target',.8))
        elif cfg['method']=='efa':
            raw=efa_run(x,q=settings.get('q'),seed=cfg.get('split',{}).get('seed',42),extraction=settings.get('extraction','pa'),rotation=settings.get('rotation','oblimin'))
            if settings.get('automatic_factor_selection'):
                from .factors import parallel_analysis
                raw['parallel']=parallel_analysis(raw['correlation'],len(x),cfg.get('split',{}).get('seed',42))
                raw['automatic_factor_selection']=settings['automatic_factor_selection']
        else:raw=cluster_run(x,cfg['method'],settings,cfg.get('split',{}).get('seed',42))
        raw['transform']=t
    bundle=build(run,raw,f)
    db.write_json(db.folder(run['id'])/'raw.json',raw)
    db.write_json(db.folder(run['id'])/'frame.json',f.to_dict('records'))
    db.write_json(db.folder(run['id'])/'result.json',bundle)
    return run['provenance']
