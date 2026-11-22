"""Python EFA: statsmodels extraction/rotation, explicit diagnostics and retention policy.

No smoothing, clipping Heywood solutions, silent imputing, or runtime R dependency.
"""
import warnings
import importlib.metadata
import numpy as np
from scipy import linalg,stats
from statsmodels.multivariate.factor import Factor

def common_spectrum(correlation):
    reduced=np.array(correlation,float,copy=True)
    smc=1-1/np.diag(linalg.solve(reduced,np.eye(len(reduced)),assume_a='pos'))
    np.fill_diagonal(reduced,smc)
    return linalg.eigvalsh(reduced)[::-1]

def parallel_analysis(correlation,n,seed,n_iter=500):
    """Gaussian-null sample correlation via exact Bartlett Wishart sampling (df=n-1)."""
    p=len(correlation);rng=np.random.default_rng(seed);simulations=np.empty((n_iter,p))
    for iteration in range(n_iter):
        lower=np.tril(rng.normal(size=(p,p)),-1)
        np.fill_diagonal(lower,np.sqrt(rng.chisquare(n-1-np.arange(p))))
        scatter=lower@lower.T;sd=np.sqrt(np.diag(scatter))
        simulations[iteration]=common_spectrum(scatter/np.outer(sd,sd))
    observed=common_spectrum(correlation);boundary=np.quantile(simulations,.95,axis=0)
    crossings=np.flatnonzero(observed<=boundary)
    q=int(crossings[0]) if len(crossings) else p
    return dict(observed=observed,simulated=boundary,simulation_mean=simulations.mean(0),n_iter=n_iter,quantile=.95,recommended=q,seed=seed,
                spectrum_method='SMC reduced correlation before extraction',null_method='Bartlett Wishart Gaussian independent indicators; df=n-1',comparison='95th percentile, consecutive factors from first',simulation_values=simulations)

def prepare_factors(X,q=None,seed=42):
    X=np.asarray(X,float)
    if X.ndim!=2 or X.shape[1]<3 or len(X)<=X.shape[1]:raise ValueError('EFA memerlukan minimal 3 indikator dan observasi lebih banyak daripada indikator.')
    n,p=X.shape
    if not np.isfinite(X).all() or np.any(X.std(0,ddof=1)<=0):raise ValueError('EFA memerlukan data finite dan indikator nonkonstan.')
    if type(seed) is not int or not 0<=seed<=2147483647:raise ValueError('Seed EFA tidak sah.')
    R=np.corrcoef(X,rowvar=False)
    if linalg.eigvalsh(R)[0]<=1e-10:raise ValueError('Matriks korelasi tidak positive definite; tinjau ketergantungan indikator.')
    parallel=None
    if q is None:
        parallel=parallel_analysis(R,n,seed);q=parallel['recommended']
    if type(q) is not int or not 1<=q<p:raise ValueError('Tidak ada faktor yang didukung atau jumlah faktor tidak sah. Tinjau indikator dan teori; jangan memaksakan faktor.')
    degrees=p*(p-1)/2-p*q+q*(q-1)/2
    if degrees<0:raise ValueError(f'Jumlah faktor {q} tidak teridentifikasi dari {p} indikator (derajat bebas {degrees:g}). Tinjau teori/jumlah faktor manual atau ubah indikator; model tidak dipaksakan.')
    return R,q,parallel

def efa_run(X,q=None,seed=42,extraction='pa',rotation='oblimin'):
    X=np.asarray(X,float);R,q,parallel=prepare_factors(X,q,seed);n,p=X.shape
    if extraction not in ('pa','ml') or rotation not in ('none','varimax','oblimin'):raise ValueError('Ekstraksi atau rotasi EFA tidak didukung.')
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        model=Factor(corr=R,n_factor=q,nobs=n,method=extraction,smc=True)
        fit=model.fit(maxiter=1000,tol=1e-8,opt={'maxiter':1000,'gtol':1e-7},rng=np.random.default_rng(seed))
        original=np.asarray(fit.loadings_no_rot)
        if original.shape!=(p,q):raise ValueError('Jumlah faktor positif aktual tidak memenuhi permintaan.')
        if extraction=='ml' and not fit.mle_retvals.success:raise ValueError('Estimasi maximum likelihood tidak konvergen; tinjau data atau gunakan principal axis.')
        if extraction=='pa':
            reduced=R.copy();np.fill_diagonal(reduced,np.sum(original**2,axis=1));values,vectors=linalg.eigh(reduced)
            next_h=np.sum(vectors[:,-q:]**2*np.maximum(values[-q:],0),axis=1)
            if np.linalg.norm(next_h-np.sum(original**2,axis=1))>5e-8:raise ValueError('Principal axis belum konvergen; hasil tidak diterbitkan.')
        if rotation!='none' and q>1:fit.rotate(rotation)
    notes=[str(w.message) for w in captured]
    if any('converg' in w.lower() for w in notes):raise ValueError('Estimasi atau rotasi tidak konvergen.')
    L=np.asarray(fit.loadings);T=np.asarray(fit.rotation_matrix);Phi=T.T@T
    common=L@Phi@L.T
    if not np.allclose(common,original@original.T,atol=1e-8,rtol=1e-8):raise ValueError('Rotasi tidak mempertahankan kovarians bersama.')
    h=np.diag(common);u=1-h
    if not np.isfinite(L).all() or np.any(u<=1e-8) or np.any(h<0):raise ValueError('Solusi faktor tidak layak (Heywood/keunikan tidak positif). Tinjau indikator atau jumlah faktor.')
    # Canonical signs and ordering aid comparison; change all linked arrays together.
    order=np.argsort(-np.sum(L**2,axis=0),kind='stable');L=L[:,order];Phi=Phi[np.ix_(order,order)]
    signs=np.where(L[np.argmax(abs(L),axis=0),np.arange(q)]<0,-1.,1.)
    L=L*signs;Phi=Phi*np.outer(signs,signs);structure=L@Phi
    score_coefficients=linalg.solve(R,structure,assume_a='pos')
    Z=(X-X.mean(0))/X.std(0,ddof=1);scores=Z@score_coefficients
    inverse=linalg.solve(R,np.eye(p),assume_a='pos');partial=-inverse/np.sqrt(np.outer(inverse.diagonal(),inverse.diagonal()));np.fill_diagonal(partial,0)
    corr_sq=R**2;np.fill_diagonal(corr_sq,0);partial_sq=partial**2
    denominators=corr_sq.sum(0)+partial_sq.sum(0)
    msa=np.divide(corr_sq.sum(0),denominators,out=np.full(p,np.nan),where=denominators>0)
    denominator=corr_sq.sum()+partial_sq.sum()
    if denominator<=0 or not np.isfinite(msa).all():raise ValueError('KMO tidak terdefinisi: tidak ada pola korelasi yang dapat dimodelkan.')
    kmo=corr_sq.sum()/denominator;chi=-(n-1-(2*p+5)/6)*np.linalg.slogdet(R)[1];df=p*(p-1)/2
    p_value=float(stats.chi2.sf(chi,df))
    return dict(pattern=L,Phi=Phi,structure=structure,communalities=h,uniqueness=u,residual=R-(L@Phi@L.T+np.diag(u)),scores=scores,q=q,kmo=kmo,msa=msa,
                bartlett={'chisq':chi,'df':df,'p.value':p_value,'p_value_status':'below_numeric_precision' if p_value==0 else 'ok','p_value_display':'< 1e-300' if p_value==0 else f'{p_value:.6g}'},parallel=parallel,warnings=notes,
                score_coefficients=score_coefficients,correlation=R,center=X.mean(0),scale=X.std(0,ddof=1),
                extraction=extraction,rotation=rotation,converged=True,seed=seed,engine='statsmodels',engine_policy_version='efa-python-1',
                versions={package:importlib.metadata.version(package) for package in ('statsmodels','numpy','scipy')})
