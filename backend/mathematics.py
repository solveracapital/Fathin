"""Shared formula markup for slides and PDF. Plain prose remains plain prose."""
import re
INLINE=re.compile(r'\\\((.*?)\\\)',re.S)
LITERALS={'Sp = W/(n_train−2)':r'S_p=\frac{W}{n_{\mathrm{train}}-2}','W/(n−2)':r'\frac{W}{n-2}','T = Z A':r'T=ZA','η = xᵀ(b1−b0) + c1−c0':r'\eta=x^T(b_1-b_0)+c_1-c_0','L Φ Lᵀ + Ψ':r'L\Phi L^T+\Psi','L Lᵀ':r'LL^T','η':r'\eta','Φ':r'\Phi','Ψ':r'\Psi','Σ':r'\Sigma'}
PATTERN=re.compile('|'.join(re.escape(k) for k in sorted(LITERALS,key=len,reverse=True)))
METRICS={'accuracy':r'\mathrm{Accuracy}=\frac{TP+TN}{TP+TN+FP+FN}','sensitivity':r'\mathrm{Sensitivity}=\frac{TP}{TP+FN}','specificity':r'\mathrm{Specificity}=\frac{TN}{TN+FP}','precision':r'\mathrm{Precision}=\frac{TP}{TP+FP}','F1':r'F_1=\frac{2TP}{2TP+FP+FN}','balanced_accuracy':r'\mathrm{BA}=\frac{\mathrm{Sensitivity}+\mathrm{Specificity}}{2}','prevalence':r'\mathrm{Prevalence}=\frac{TP+FN}{n}','ROC_AUC':r'\mathrm{AUC}=\int_0^1 \mathrm{TPR}(u)\,du,\quad u=\mathrm{FPR}','AP':r'\mathrm{AP}=\sum_j (R_j-R_{j-1})P_j'}
def math_prose(text):
    parts=INLINE.split(text)
    return ''.join(('\\('+part+'\\)') if i%2 else PATTERN.sub(lambda m:'\\('+LITERALS[m.group()]+'\\)',part) for i,part in enumerate(parts))
