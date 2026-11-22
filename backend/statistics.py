"""Deterministic numerical core. No file/network/UI dependencies."""
import numpy as np
from scipy import linalg, stats
from scipy.special import expit
from sklearn.metrics import (confusion_matrix, roc_auc_score, average_precision_score,
                             roc_curve, precision_recall_curve, silhouette_score)
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split, StratifiedKFold, GroupShuffleSplit, StratifiedGroupKFold, TimeSeriesSplit
from scipy.cluster.hierarchy import linkage, cut_tree


def metric(name, value, subset='test'):
    valid = value is not None and np.isfinite(value)
    return dict(id=name, label=name, value=float(value) if valid else None,
                unit='ratio', subset_id=subset, status='ok' if valid else 'undefined',
                reason=None if valid else dict(code='UNDEFINED', message='Tidak terdefinisi pada subset ini.'),
                evidence_ids=[name])


def evaluate(y, probability, threshold=.5, subset='test'):
    y=np.asarray(y); p=np.asarray(probability)
    if y.ndim!=1 or p.ndim!=1 or len(y)!=len(p) or not len(y):raise ValueError('Subset evaluasi harus nonkosong dan panjang sama.')
    if not np.isfinite(p).all() or np.any((p<0)|(p>1)) or not 0<=threshold<=1:raise ValueError('Probabilitas dan threshold harus finite pada 0..1.')
    if not set(np.unique(y))<=set([0,1]):raise ValueError('Label evaluasi harus 0/1.')
    tn,fp,fn,tp=confusion_matrix(y,p>=threshold,labels=[0,1]).ravel()
    div=lambda a,b: float(a/b) if b else None
    recall=div(tp,tp+fn); specificity=div(tn,tn+fp)
    values=dict(accuracy=div(tp+tn,len(y)), sensitivity=recall,specificity=specificity,
        precision=div(tp,tp+fp), F1=div(2*tp,2*tp+fp+fn),
        balanced_accuracy=(recall+specificity)/2 if recall is not None and specificity is not None else None,
        prevalence=div(sum(y),len(y)), ROC_AUC=None, AP=None)
    curves={}
    if len(np.unique(y))==2:
        values.update(ROC_AUC=roc_auc_score(y,p),AP=average_precision_score(y,p))
        fpr,tpr,th=roc_curve(y,p)
        precision,recall_curve,thresholds=precision_recall_curve(y,p)
        curves=dict(roc=dict(x=fpr,y=tpr,thresholds=[None if not np.isfinite(v) else v for v in th]),
            precision_recall=dict(x=recall_curve,y=precision,thresholds=thresholds))
    return dict(metrics=[metric(k,v,subset) for k,v in values.items()],counts=dict(TN=int(tn),FP=int(fp),FN=int(fn),TP=int(tp)),
                matrix=[[int(tn),int(fp)],[int(fn),int(tp)]],orientation='actual_rows_predicted_columns',curves=curves,n=len(y),threshold=threshold)


def transform_fit(X, options):
    X=np.asarray(X,float).copy(); mode=options.get('missing','error')
    if np.isinf(X).any(): raise ValueError('Nilai tak hingga tidak dapat dianalisis.')
    med=np.nanmedian(X,axis=0)
    if np.isnan(med).any(): raise ValueError('Fitur seluruhnya kosong.')
    if np.isnan(X).any() and mode!='median': raise ValueError('Missing value: pilih median atau complete-case secara eksplisit.')
    X=np.where(np.isnan(X),med,X)
    if options.get('log',False):
        if (X<=0).any(): raise ValueError('Transformasi log memerlukan nilai positif.')
        X=np.log(X)
    scale=options.get('scale','none')
    center=X.mean(0) if scale=='standard' else np.median(X,axis=0) if scale=='robust' else np.zeros(X.shape[1])
    spread=X.std(0,ddof=1) if scale=='standard' else np.diff(np.percentile(X,[25,75],axis=0),axis=0)[0] if scale=='robust' else np.ones(X.shape[1])
    if np.any(spread<=0): raise ValueError('Skala nol; tinjau fitur konstan.')
    return (X-center)/spread,dict(median=med,center=center,scale=spread,log=options.get('log',False),missing=mode)


def transform_apply(X,t):
    if not np.isfinite(X[~np.isnan(X)]).all():raise ValueError('Nilai tak hingga tidak boleh diprediksi.')
    if np.isnan(X).any() and t.get('missing','error')!='median':raise ValueError('Missing pada test memerlukan kebijakan median eksplisit.')
    X=np.where(np.isnan(X),t['median'],X)
    if t['log']:
        if (X<=0).any(): raise ValueError('Nilai test tidak memenuhi transformasi log.')
        X=np.log(X)
    return (X-t['center'])/t['scale']


def lda_fit(X,y,prior='empirical'):
    n,p=X.shape; ns=np.bincount(y,minlength=2)
    if min(ns)<2: raise ValueError('Setiap kelas train memerlukan minimal dua observasi.')
    means=np.array([X[y==g].mean(0) for g in (0,1)])
    covs=np.array([np.atleast_2d(np.cov(X[y==g],rowvar=False,ddof=1)) for g in (0,1)])
    W=sum((ns[g]-1)*covs[g] for g in (0,1)); Sp=W/(n-2)
    if np.linalg.matrix_rank(Sp)<p: raise ValueError('Kovarians pooled singular; kurangi fitur yang bergantung linear.')
    linalg.cholesky(Sp)
    priors=ns/n if isinstance(prior,str) and prior=='empirical' else np.array([.5,.5]) if isinstance(prior,str) and prior=='equal' else np.asarray(prior,float)
    if priors.shape!=(2,) or not np.isfinite(priors).all() or min(priors)<=0 or not np.isclose(priors.sum(),1,rtol=0,atol=1e-12): raise ValueError('Prior harus positif dan berjumlah satu.')
    b=linalg.solve(Sp,means.T,assume_a='pos').T
    c=-.5*np.sum(means*b,axis=1)+np.log(priors)
    a=linalg.solve(Sp,means[1]-means[0],assume_a='pos'); norm=np.sqrt(a@Sp@a)
    if norm==0: raise ValueError('Pusat kelas sama; fungsi kanonik tidak teridentifikasi.')
    a/=norm; mean=X.mean(0); a0=-a@mean
    B=sum(ns[g]*np.outer(means[g]-mean,means[g]-mean) for g in (0,1))
    eigen=float(linalg.eigvalsh(B,W)[-1]); wilks=1/(1+eigen)
    box=None
    if all(np.linalg.slogdet(s)[0]>0 and np.linalg.matrix_rank(s)==p for s in covs):
        M=(n-2)*np.linalg.slogdet(Sp)[1]-sum((ns[g]-1)*np.linalg.slogdet(covs[g])[1] for g in (0,1))
        correction=(2*p*p+3*p-1)/(6*(p+1))*(sum(1/(ns-1))-1/(n-2))
        chi=(1-correction)*M; df=p*(p+1)/2
        if chi>=0: box=dict(M=M,chi2=chi,df=df,p_value=stats.chi2.sf(chi,df),approximate=True)
    marginal=[]; distances={}
    for g in (0,1):
        for j in range(p):
            x=X[y==g,j];valid=len(x)>=3 and np.ptp(x)>0;sh=stats.shapiro(x) if valid else None
            marginal.append(dict(group=g,feature_index=j,W=sh.statistic if valid else None,p_value=sh.pvalue if valid else None,skew=stats.skew(x,bias=False) if valid else None,kurtosis=stats.kurtosis(x,bias=False) if valid else None,p_value_limited=len(x)>5000,status='ok' if valid else 'unavailable',reason=None if valid else 'Normalitas marginal tidak dapat diuji: sampel kurang dari 3 atau nilai konstan.'))
        if np.linalg.matrix_rank(covs[g])==p:
            z=X[y==g]-means[g]; d=np.sum(z*linalg.solve(covs[g],z.T).T,axis=1)
            distances[str(g)]=dict(values=d,cutoff=stats.chi2.ppf(.99,p),diagnostic_only=True)
    return dict(b=b,c=c,priors=priors,means=means,group_covariances=covs,W=W,B=B,Sp=Sp,a=a,a0=a0,
        standardized=a*np.sqrt(np.diag(Sp)),structure=(Sp@a)/np.sqrt(np.diag(Sp)),
        centroids=means@a+a0,eigenvalue=eigen,canonical_correlation=np.sqrt(eigen/(1+eigen)),wilks=wilks,
        canonical_chi2=-(n-1-(p+2)/2)*np.log(wilks),canonical_df=p,rank=int(np.linalg.matrix_rank(Sp)),
        condition_number=np.linalg.cond(Sp),correlation=np.atleast_2d(np.corrcoef(X.T)),box_m=box,marginal=marginal,mahalanobis=distances)


def predict(model,X):
    eta=X@(model['b'][1]-model['b'][0])+model['c'][1]-model['c'][0]
    return expit(eta),eta


def time_values(source,config):
    import pandas as pd
    if config.get('time_format')=='year':
        years=pd.to_numeric(source,errors='raise')
        if years.isna().any() or (years%1!=0).any():raise ValueError('Tahun harus bilangan bulat dan tidak kosong.')
        return pd.to_datetime(years.astype('int64').astype(str),format='%Y',errors='raise',utc=True)
    # Numeric dates are not silently interpreted as nanoseconds since 1970.
    return pd.to_datetime(source.astype(str) if pd.api.types.is_numeric_dtype(source) else source,errors='raise',utc=True)

def split_indices(frame,y,config):
    mode=config.get('mode','stratified_random'); ids=np.arange(len(y)); seed=config.get('seed',42)
    if mode=='saved_membership':
        membership=frame[config.get('column_id','train')].to_numpy()
        if not set(membership)<=set([0,1]): raise ValueError('Keanggotaan split harus 0 atau 1.')
        tr,te=ids[membership==1],ids[membership==0]
        if config.get('reconstruct_order',False):
            a,b=train_test_split(ids,test_size=config.get('test_size',.3),stratify=y,random_state=seed)
            if set(a)!=set(tr) or set(b)!=set(te):raise ValueError('Urutan seed tidak cocok dengan membership tersimpan.')
            tr,te=a,b
        return tr,te
    if mode=='group':
        groups=frame[config['column_id']]
        if groups.isna().any(): raise ValueError('Entity kosong.')
        return next(GroupShuffleSplit(n_splits=1,test_size=config.get('test_size',.3),random_state=seed).split(ids,y,groups))
    if mode=='temporal':
        import pandas as pd
        times=time_values(frame[config['column_id']],config)
        if times.isna().any():raise ValueError('Waktu kosong tidak boleh diabaikan diam-diam.')
        cut=pd.Timestamp(config['cutoff']); cut=cut.tz_localize('UTC') if cut.tzinfo is None else cut
        gap=pd.Timedelta(days=config.get('gap_days',0))
        if gap<pd.Timedelta(0): raise ValueError('Gap tidak boleh negatif.')
        return ids[times<cut-gap],ids[times>=cut]
    if mode!='stratified_random': raise ValueError('Mode split tidak didukung.')
    return train_test_split(ids,test_size=config.get('test_size',.3),stratify=y,random_state=seed)


def lda_run(frame,features,target,positive,options,split,settings):
    X=frame[features].to_numpy(float); labels=frame[target]
    if labels.isna().any() or labels.nunique()!=2 or positive not in labels.unique(): raise ValueError('Target harus dua kelas lengkap dengan kelas positif yang sah.')
    y=(labels==positive).to_numpy(int); train,test=split_indices(frame,y,split)
    if len(train)==0 or len(test)==0: raise ValueError('Split kosong.')
    Xt,t=transform_fit(X[train],options); Xall=transform_apply(X,t)
    model=lda_fit(Xt,y[train],settings.get('prior','empirical')); prob,eta=predict(model,Xall)
    threshold=settings.get('threshold',.5)
    if not 0<=threshold<=1: raise ValueError('Threshold di luar 0..1.')
    ev={name:evaluate(y[idx],prob[idx],threshold,name) for name,idx in [('train',train),('test',test)]}
    ev['baseline_test']=evaluate(y[test],np.full(len(test),float(np.mean(y[train])>.5)),.5,'test')
    oof=None; selected=None
    if settings.get('oof',False):
        folds=min(settings.get('folds',5),int(np.bincount(y[train]).min()))
        if folds<2: raise ValueError('Kelas minoritas tidak cukup untuk OOF.')
        oof=np.full(len(train),np.nan)
        mode=split.get('mode')
        if mode=='group':
            groups=frame.iloc[train][split['column_id']].to_numpy()
            folds=min(folds,len(np.unique(groups)))
            if folds<2:raise ValueError('Entitas tidak cukup untuk OOF.')
            partitions=StratifiedGroupKFold(folds,shuffle=True,random_state=split.get('seed',42)).split(X[train],y[train],groups)
        elif mode=='temporal':
            import pandas as pd
            times=time_values(frame.iloc[train][split['column_id']],split)
            unique=np.sort(times.unique())
            if len(unique)<=folds:raise ValueError('Waktu unik tidak cukup untuk OOF temporal.')
            partitions=[]
            for a,b in TimeSeriesSplit(folds).split(unique):
                boundary=unique[b[0]]-pd.Timedelta(days=split.get('gap_days',0))
                partitions.append((np.where(times<boundary)[0],np.where(times.isin(unique[b]))[0]))
        else:partitions=StratifiedKFold(folds,shuffle=True,random_state=split.get('seed',42)).split(X[train],y[train])
        for a,b in partitions:
            xx,tt=transform_fit(X[train][a],options)
            if settings.get('oof_estimator')=='sklearn_svd':
                from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
                prior=settings.get('prior','empirical');svd_priors=None if isinstance(prior,str) and prior=='empirical' else [.5,.5] if isinstance(prior,str) and prior=='equal' else prior
                oof[b]=LinearDiscriminantAnalysis(solver='svd',priors=svd_priors).fit(xx,y[train][a]).predict_proba(transform_apply(X[train][b],tt))[:,1]
            else:
                mm=lda_fit(xx,y[train][a],settings.get('prior','empirical'))
                oof[b]=predict(mm,transform_apply(X[train][b],tt))[0]
        covered=np.isfinite(oof)
        if len(np.unique(y[train][covered]))!=2:raise ValueError('OOF tidak mempunyai kedua kelas untuk pemilihan ambang.')
        precision,recall,thresholds=precision_recall_curve(y[train][covered],oof[covered])
        f1=np.divide(2*precision*recall,precision+recall,out=np.zeros_like(precision),where=(precision+recall)!=0)
        selected=float(thresholds[np.argmax(f1[:-1])]); ev['OOF_train']=evaluate(y[train][covered],oof[covered],.5,'train_oof')
        ev['test_OOF_threshold']=evaluate(y[test],prob[test],selected,'test')
    equal_prob=expit(eta-np.log(model['priors'][1]/model['priors'][0]))
    ev['test_equal_prior']=evaluate(y[test],equal_prob[test],.5,'test')
    return dict(model=model,transform=t,probability=prob,eta=eta,canonical_scores=Xall@model['a']+model['a0'],
        train=train,test=test,y=y,evaluations=ev,oof=oof,oof_threshold=selected,transformed=Xall,excluded=np.setdiff1d(np.arange(len(y)),np.r_[train,test]),
        negative_label=next(v for v in labels.unique() if v!=positive),positive_label=positive)


def pca_run(X,basis='correlation',q=None,target=.8):
    if q is not None and (type(q) is not int or q<1):raise ValueError('Jumlah komponen harus bilangan bulat positif.')
    if basis not in ('correlation','covariance') or not 0<target<=1:raise ValueError('Basis/target PCA tidak valid.')
    X=np.asarray(X,float); center=X.mean(0); sd=X.std(0,ddof=1)
    if np.any(sd==0) or not np.isfinite(X).all(): raise ValueError('PCA memerlukan fitur finite nonkonstan.')
    scale=sd if basis=='correlation' else np.ones(X.shape[1]); Z=(X-center)/scale
    eigen,A=linalg.eigh(np.atleast_2d(np.cov(Z,rowvar=False,ddof=1))); eigen=eigen[::-1]; A=A[:,::-1]
    for j in range(A.shape[1]):
        if A[np.argmax(abs(A[:,j])),j]<0:A[:,j]*=-1
    pve=np.maximum(eigen,0)/sum(eigen); cumulative=np.cumsum(pve);cumulative[-1]=1.
    selected=q if q is not None else min(len(eigen),int(np.searchsorted(cumulative,target)+1))
    if not 1<=selected<=X.shape[1]: raise ValueError('Jumlah komponen tidak sah.')
    return dict(center=center,scale=scale,eigenvalues=eigen,directions=A,scores=Z@A,loadings=A*np.sqrt(np.maximum(eigen,0))/(sd/scale)[:,None],PVE=pve,cumulative=cumulative,selected_q=selected,rank=int(np.linalg.matrix_rank(Z)),basis=basis)


def cluster_run(X,method,settings,seed=42):
    n=len(X); k=settings.get('k',3); unique=len(np.unique(X,axis=0))
    if type(k) is not int:raise ValueError('K harus bilangan bulat.')
    if not 2<=k<min(n,unique+1): raise ValueError('K memerlukan 2<=K<n dan K<=jumlah titik unik.')
    metric_name=settings.get('metric','euclidean'); tree=None
    if method=='kmeans':
        if metric_name!='euclidean': raise ValueError('K-means hanya Euclidean.')
        fit=KMeans(n_clusters=k,init='k-means++',n_init=20,max_iter=300,tol=1e-4,random_state=seed).fit(X)
        labels=fit.labels_; inertia=fit.inertia_; iterations=fit.n_iter_
    else:
        if n>3000: raise ValueError('Hierarchical full dibatasi 3000 baris; gunakan subset eksplisit atau k-means.')
        link=settings.get('linkage','ward')
        if link not in ('ward','average','complete','single'): raise ValueError('Linkage tidak didukung.')
        if metric_name not in ('euclidean','cityblock','manhattan'): raise ValueError('Jarak tidak didukung.')
        if link=='ward' and metric_name!='euclidean': raise ValueError('Ward memerlukan Euclidean.')
        tree=linkage(X,method=link,metric='cityblock' if metric_name=='manhattan' else metric_name)
        labels=cut_tree(tree,n_clusters=k).ravel(); inertia=None; iterations=None
    if len(np.unique(labels))!=k: raise ValueError('Jumlah cluster aktual tidak sama dengan K.')
    rng=np.random.default_rng(seed)
    sample=np.arange(n) if n<=2000 else np.sort(rng.choice(n,2000,replace=False))
    sil=None
    if len(np.unique(labels[sample]))==k and len(sample)>k:
        sil=silhouette_score(X[sample],labels[sample],metric=metric_name)
    return dict(labels=labels,centroids=np.array([X[labels==i].mean(0) for i in range(k)]),counts=np.bincount(labels),inertia=inertia,iterations=iterations,silhouette=sil,silhouette_sample_n=len(sample),tree=tree,seed=seed)
