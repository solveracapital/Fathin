"""Analisis LDA UCI 572. Jalankan dari folder ini: python Analisis_Pembanding.py.
Hasil Python, bukan output SPSS. Seed 42 keputusan penulis, bukan seed sumber.
"""
from pathlib import Path
import json, sys, platform, hashlib
import numpy as np
import pandas as pd
import scipy
from scipy import stats, linalg
from scipy.special import expit
import sklearn
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as SKLDA
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.metrics import confusion_matrix, roc_auc_score, average_precision_score, precision_recall_curve, roc_curve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parent
class LinearDiscriminantAnalysis:
 """LDA dengan kovarians pooled sample W/(n-G), bukan MLE W/n."""
 def __init__(self,solver='svd',store_covariance=False,priors=None): self.priors=priors
 def fit(self,X,y):
  self.means_=np.array([X[y==g].mean(0) for g in [0,1]])
  counts=np.bincount(y); self.priors_=counts/len(y) if self.priors is None else np.array(self.priors)
  self.covariance_=sum((counts[g]-1)*np.cov(X[y==g],rowvar=False) for g in [0,1])/(len(y)-2)
  cc=np.linalg.solve(self.covariance_,self.means_.T).T
  const=-.5*np.einsum('ij,ij->i',cc,self.means_)+np.log(self.priors_)
  self.coef_=(cc[1]-cc[0])[None,:];self.intercept_=np.array([const[1]-const[0]])
  return self
 def predict_proba(self,X):
  p=expit(X@self.coef_[0]+self.intercept_[0]);return np.column_stack([1-p,p])
for d in ['Grafik','Output','Data_Grafik']:(P/d).mkdir(exist_ok=True)
raw=pd.read_csv(P/'Sumber/data_asli.csv')
cols=[' Working Capital to Total Assets',' Retained Earnings to Total Assets',' ROA(A) before interest and % after tax',' Equity to Liability',' Total Asset Turnover']
names=['WC_TA','RE_TA','ROA_A','EQ_LIAB','TURNOVER']
X=raw[cols].to_numpy(); y=raw['Bankrupt?'].to_numpy(dtype=int)
ids=np.array([f'TW{i+1:05d}' for i in range(len(y))])
tr,te=train_test_split(np.arange(len(y)),test_size=.3,random_state=42,stratify=y)
train=np.zeros(len(y),dtype=int);train[tr]=1
data=pd.DataFrame(X,columns=names);data.insert(0,'bankrupt',y);data.insert(0,'ID',ids);data['train']=train
data.to_csv(P/'Data_Analisis.csv',index=False,encoding='utf-8')
model=LinearDiscriminantAnalysis(solver='svd',store_covariance=True).fit(X[tr],y[tr])
probs=model.predict_proba(X)[:,1]
cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
oof=np.empty(len(tr))
for fit_ix,val_ix in cv.split(X[tr],y[tr]):
 oof[val_ix]=LinearDiscriminantAnalysis().fit(X[tr][fit_ix],y[tr][fit_ix]).predict_proba(X[tr][val_ix])[:,1]
pr,re,th=precision_recall_curve(y[tr],oof)
f=np.divide(2*pr[:-1]*re[:-1],pr[:-1]+re[:-1],out=np.zeros(len(th)),where=pr[:-1]+re[:-1]>0)
threshold=float(th[np.argmax(f)])
eq=LinearDiscriminantAnalysis(solver='svd',priors=[.5,.5]).fit(X[tr],y[tr])

def metrics(yy,pp,t=.5):
 tn,fp,fn,tp=confusion_matrix(yy,pp>=t,labels=[0,1]).ravel()
 sens=tp/(tp+fn);spec=tn/(tn+fp)
 return dict(n=len(yy),TN=int(tn),FP=int(fp),FN=int(fn),TP=int(tp),threshold=t,accuracy=float((tn+tp)/len(yy)),sensitivity=float(sens),specificity=float(spec),precision=float(tp/(tp+fp)) if tp+fp else None,F1=float(2*tp/(2*tp+fp+fn)),balanced_accuracy=float((sens+spec)/2),ROC_AUC=float(roc_auc_score(yy,pp)),AP=float(average_precision_score(yy,pp)))
results={'train':metrics(y[tr],probs[tr]),'test':metrics(y[te],probs[te]),'OOF_train':metrics(y[tr],oof),'test_OOF_threshold':metrics(y[te],probs[te],threshold),'test_equal_prior':metrics(y[te],eq.predict_proba(X[te])[:,1]),'baseline_test':metrics(y[te],np.zeros(len(te)))}
means=np.array([X[tr][y[tr]==g].mean(0) for g in [0,1]])
ns=np.bincount(y[tr]);n=len(tr);p=5;mu=X[tr].mean(0)
covs=np.array([np.cov(X[tr][y[tr]==g],rowvar=False,ddof=1) for g in [0,1]])
W=sum((ns[g]-1)*covs[g] for g in [0,1]);Sp=W/(n-2)
B=sum(ns[g]*np.outer(means[g]-mu,means[g]-mu) for g in [0,1])
ev,vec=linalg.eigh(B,W);a=vec[:,-1];a=a/np.sqrt(a@Sp@a)
if a@(means[1]-means[0])<0:a=-a
a0=-a@mu;D=X@a+a0;cent=means@a+a0
within_sd=np.sqrt(np.diag(Sp));standard=a*within_sd;structure=Sp@a/within_sd
inverse=np.linalg.inv(Sp);classcoef=means@inverse
classconst=-.5*np.einsum('ij,ij->i',classcoef,means)+np.log(ns/n)
manualscore=X@(classcoef[1]-classcoef[0])+classconst[1]-classconst[0]
assert np.max(np.abs(expit(manualscore)-probs))<1e-9
sk=SKLDA(solver='svd').fit(X[tr],y[tr]);skp=sk.predict_proba(X[te])[:,1]
results['test_sklearn_svd']=metrics(y[te],skp)
lam=float(ev[-1]);wilks=1/(1+lam);r=np.sqrt(lam/(1+lam))
chi=-(n-1-(p+2)/2)*np.log(wilks)
M=(n-2)*np.linalg.slogdet(Sp)[1]-sum((ns[g]-1)*np.linalg.slogdet(covs[g])[1] for g in [0,1])
c=(2*p*p+3*p-1)/(6*(p+1))*(sum(1/(ns-1))-1/(n-2))
box_chi=(1-c)*M;boxdf=p*(p+1)/2
diagnostics=[]
for g in [0,1]:
 xx=X[tr][y[tr]==g]
 for j,name in enumerate(names):
  sw=stats.shapiro(xx[:,j]); diagnostics.append(dict(group=g,variable=name,n=len(xx),Shapiro_W=float(sw.statistic),Shapiro_p=float(sw.pvalue),skew=float(stats.skew(xx[:,j],bias=False)),kurtosis_excess=float(stats.kurtosis(xx[:,j],bias=False))))
 md=np.einsum('ij,jk,ik->i',xx-means[g],np.linalg.inv(covs[g]),xx-means[g])
 pd.DataFrame({'ID':ids[tr][y[tr]==g],'D2':md,'flag_99':md>stats.chi2.ppf(.99,p)}).to_csv(P/f'Output/Mahalanobis_g{g}.csv',index=False)
diag=pd.DataFrame(diagnostics);diag.to_csv(P/'Output/Diagnostik.csv',index=False)
desc=[]
for label,ix in [('Semua',np.arange(len(y))),('Train',tr),('Test',te),('Train_0',tr[y[tr]==0]),('Train_1',tr[y[tr]==1])]:
 for j,name in enumerate(names):
  v=X[ix,j];desc.append([label,name,len(v),int(np.isnan(v).sum()),v.mean(),v.std(ddof=1),np.median(v),v.min(),v.max()])
des=pd.DataFrame(desc,columns=['subset','variabel','n','missing','mean','SD','median','min','max']);des.to_csv(P/'Output/Deskriptif.csv',index=False)
pred=data[['ID','bankrupt','train']].copy();pred['posterior']=probs;pred['prediksi_05']=(probs>=.5).astype(int);pred['D']=D
pred['OOF_posterior']=np.nan;pred.loc[tr,'OOF_posterior']=oof;pred.to_csv(P/'Output/Prediksi.csv',index=False)
pred['prediksi_OOF']=np.nan;pred.loc[tr,'prediksi_OOF']=(oof>=.5).astype(int)
pred['prediksi_ambang_OOF']=(probs>=threshold).astype(int)
pred['prediksi_prior_equal']=(eq.predict_proba(X)[:,1]>=.5).astype(int)
pred.to_csv(P/'Output/Prediksi.csv',index=False)
sens=[]
for seed in range(30):
 ti,vi=train_test_split(np.arange(len(y)),test_size=.3,random_state=seed,stratify=y)
 m=LinearDiscriminantAnalysis().fit(X[ti],y[ti]);sens.append({'seed':seed,**metrics(y[vi],m.predict_proba(X[vi])[:,1])})
pd.DataFrame(sens).to_csv(P/'Output/Sensitivitas_Seed.csv',index=False)
z=(X[tr]-mu)/X[tr].std(0,ddof=1);R=np.corrcoef(z,rowvar=False);pe,pv=np.linalg.eigh(R);pe=pe[::-1];pv=pv[:,::-1]
pd.DataFrame(R,index=names,columns=names).to_csv(P/'Output/Korelasi_Train.csv')
pd.DataFrame({'komponen':np.arange(1,6),'eigenvalue':pe,'PVE':pe/5,'kumulatif':np.cumsum(pe)/5}).to_csv(P/'Data_Grafik/PCA.csv',index=False)
pd.DataFrame(pv,index=names,columns=[f'PC{i}' for i in range(1,6)]).to_csv(P/'Output/PCA_eigenvector.csv')
idx=int(te[np.flatnonzero(y[te]==1)[0]])
summary={'versions':{'Python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit-learn':sklearn.__version__,'matplotlib':matplotlib.__version__},'source_sha256':hashlib.sha256((P/'Sumber/data_asli.csv').read_bytes()).hexdigest(),'n':len(y),'counts':np.bincount(y).tolist(),'train_counts':ns.tolist(),'test_counts':np.bincount(y[te]).tolist(),'missing':int(raw.isna().sum().sum()),'duplicates_all':int(raw.duplicated().sum()),'duplicates_five':int(data[names+['bankrupt']].duplicated().sum()),'features':dict(zip(names,cols)),'results':results,'canonical':{'a':a.tolist(),'constant':float(a0),'standardized':standard.tolist(),'structure':structure.tolist(),'centroids':cent.tolist(),'eigenvalue':lam,'correlation':float(r),'wilks':float(wilks),'chi_approx':float(chi),'p_approx':float(stats.chi2.sf(chi,p))},'classification':{'coefficients':classcoef.tolist(),'constants':classconst.tolist(),'logit_coefficients':model.coef_[0].tolist(),'logit_intercept':float(model.intercept_[0]),'prior':model.priors_.tolist(),'manual_max_error':float(np.max(abs(expit(manualscore)-probs)))},'diagnostics':{'Box_M':float(M),'Box_chi':float(box_chi),'Box_df':boxdf,'Box_p':float(stats.chi2.sf(box_chi,boxdf)),'rank_Sp':int(np.linalg.matrix_rank(Sp)),'condition_Sp':float(np.linalg.cond(Sp)),'condition_R':float(np.linalg.cond(R))},'example':{'ID':ids[idx],'X':X[idx].tolist(),'actual':int(y[idx]),'D':float(D[idx]),'posterior':float(probs[idx]),'predicted':int(probs[idx]>=.5),'delta':(classcoef@X[idx]+classconst).tolist(),'contributions':(X[idx]*model.coef_[0]).tolist()},'PCA':{'eigenvalues':pe.tolist(),'PVE':(pe/5).tolist()},'seed_sensitivity':{k:{'min':float(min(v[k] for v in sens)),'max':float(max(v[k] for v in sens)),'mean':float(np.mean([v[k] for v in sens]))} for k in ['ROC_AUC','AP','sensitivity','F1']}}
(P/'Output/Hasil_Python.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
for name,mat in [('W',W),('B',B),('Sp',Sp),('means',means)]:pd.DataFrame(mat).to_csv(P/f'Output/{name}.csv',index=False)
pd.DataFrame(results).T.to_csv(P/'Output/Evaluasi.csv')
try:
 import pyreadstat
 pyreadstat.write_sav(data,str(P/'Data_Analisis.sav'),column_labels=['ID baris UCI','Label kebangkrutan']+cols+['1 pelatihan 0 pengujian'],variable_value_labels={'bankrupt':{0:'Tidak bangkrut',1:'Bangkrut'},'train':{0:'Test',1:'Train'}})
except ImportError:pass

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def save(name):
 plt.savefig(P/f'Grafik/{name}.png',dpi=300,bbox_inches='tight');plt.savefig(P/f'Grafik/{name}.svg',bbox_inches='tight');plt.close()
fig,ax=plt.subplots(figsize=(7,3));counts=np.bincount(y);ax.barh(['Tidak bangkrut','Bangkrut'],counts,color=['#60666d','#222222']);ax.set_xlabel('Jumlah observasi');
for i,v in enumerate(counts):ax.text(v+70,i,f'{v:,} ({v/len(y):.2%})',va='center')
ax.set_xlim(0,8000);save('Gambar_5_1_Komposisi')
pd.DataFrame({'kelompok':[0,1],'n':counts}).to_csv(P/'Data_Grafik/Komposisi.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(8,3))
for g,style in [(0,'-'),(1,'--')]:
 axes[0].hist(X[y==g,2],bins=np.linspace(0,1,31),density=True,histtype='step',linestyle=style,label=f'Kelompok {g}',color='black')
 axes[1].hist(D[te][y[te]==g],bins=35,density=True,histtype='step',linestyle=style,label=f'Kelompok {g}',color='black')
axes[0].set_xlabel('ROA_A pada skala dataset');axes[1].set_xlabel('Skor kanonik D pada test');axes[0].set_ylabel('Kepadatan');axes[1].legend();save('Gambar_5_2_Distribusi')
pd.DataFrame({'ID':ids,'label':y,'ROA_A':X[:,2],'D':D,'train':train}).to_csv(P/'Data_Grafik/Distribusi.csv',index=False)
fig,axes=plt.subplots(1,5,figsize=(9,3))
for j,ax in enumerate(axes):
 ax.boxplot([X[y==g,j] for g in [0,1]],tick_labels=['0','1'],showfliers=True,flierprops={'markersize':1});ax.set_title(names[j],fontsize=9);ax.tick_params(labelsize=8)
fig.supxlabel('Kelompok asli, skala numerik dataset');fig.tight_layout();save('Gambar_5_3_Boxplot')
fig,ax=plt.subplots(figsize=(5,4));im=ax.imshow(R,vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(5),names,rotation=35,ha='right');ax.set_yticks(range(5),names)
for i in range(5):
 for j in range(5):ax.text(j,i,f'{R[i,j]:.2f}',ha='center',va='center',fontsize=9)
fig.colorbar(im,ax=ax,label='Korelasi Pearson train');save('Gambar_5_4_Korelasi')
pd.DataFrame(R,index=names,columns=names).to_csv(P/'Data_Grafik/Korelasi.csv')
fig,axes=plt.subplots(1,2,figsize=(8,3))
for ax,key,title in zip(axes,['test','test_OOF_threshold'],['Ambang 0,5','Ambang dari OOF train']):
 mm=results[key];cm=np.array([[mm['TN'],mm['FP']],[mm['FN'],mm['TP']]])
 ax.imshow(cm,cmap='Greys',vmin=0,vmax=2200)
 for i in range(2):
  for j in range(2):ax.text(j,i,f'{cm[i,j]}\n{cm[i,j]/cm[i].sum():.1%} baris',ha='center',va='center',color='white' if cm[i,j]>1100 else 'black')
 ax.set_xticks([0,1],['0','1']);ax.set_yticks([0,1],['0','1']);ax.set_xlabel('Prediksi');ax.set_ylabel('Aktual');ax.set_title(title)
save('Gambar_5_5_Confusion')
fig,axes=plt.subplots(1,2,figsize=(8,3));fpr,tpr,_=roc_curve(y[te],probs[te]);precision,recall,_=precision_recall_curve(y[te],probs[te]);axes[0].plot(fpr,tpr,color='black');axes[0].plot([0,1],[0,1],'--',color='gray');axes[0].set(xlabel='False positive rate',ylabel='Sensitivity',title=f"ROC AUC {results['test']['ROC_AUC']:.3f}");axes[1].plot(recall,precision,color='black');axes[1].axhline(y[te].mean(),color='gray',linestyle='--');axes[1].set(xlabel='Recall',ylabel='Precision',title=f"Average precision {results['test']['AP']:.3f}");save('Gambar_5_6_ROC_PR')
pd.DataFrame({'FPR':fpr,'TPR':tpr}).to_csv(P/'Data_Grafik/ROC.csv',index=False);pd.DataFrame({'recall':recall,'precision':precision}).to_csv(P/'Data_Grafik/PR.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(8,3));axes[0].plot(range(1,6),pe,'ko-');axes[0].axhline(1,color='gray',linestyle='--');axes[0].set(xlabel='Komponen',ylabel='Eigenvalue',xticks=range(1,6));axes[1].bar(range(1,6),np.cumsum(pe)/5,color='#60666d');axes[1].set(xlabel='Jumlah komponen',ylabel='PVE kumulatif',ylim=(0,1),xticks=range(1,6));save('Gambar_5_7_PCA')
fig,ax=plt.subplots(figsize=(7,3));ax.plot(range(30),[v['ROC_AUC'] for v in sens],'ko-',markersize=3,label='Analisis ulang');ax.axhline(.904,color='gray',linestyle='--',label='Laporan sumber 0,904; split berbeda');ax.set(xlabel='Seed sensitivitas yang ditetapkan',ylabel='ROC AUC test');ax.legend(fontsize=8);save('Gambar_5_8_Seed')
print(json.dumps(summary,ensure_ascii=False,indent=2))
