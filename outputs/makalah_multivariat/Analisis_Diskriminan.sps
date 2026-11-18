* Disusun berdasarkan dokumentasi IBM SPSS Statistics 30. Belum dieksekusi.
* Ganti direktori berikut ke folder paket hasil pada komputer Anda.
CD 'C:\Users\ADVAN\OneDrive\Desktop\OneDrive\Dokumen\ChatGPT\analisi data rejul\outputs\makalah_multivariat'.
SET DECIMAL=DOT.
GET DATA /TYPE=TXT /FILE='Data_Analisis.csv'
 /ENCODING='UTF8' /DELCASE=LINE /DELIMITERS="," /QUALIFIER='"'
 /ARRANGEMENT=DELIMITED /FIRSTCASE=2
 /VARIABLES=ID A7 bankrupt F1.0 WC_TA F24.16 RE_TA F24.16
 ROA_A F24.16 EQ_LIAB F24.16 TURNOVER F24.16 train F1.0.
DATASET NAME Taiwan.
FILTER OFF.
WEIGHT OFF.
SPLIT FILE OFF.
USE ALL.
VARIABLE LEVEL ID (NOMINAL) bankrupt train (NOMINAL)
 WC_TA RE_TA ROA_A EQ_LIAB TURNOVER (SCALE).
VALUE LABELS bankrupt 0 'Tidak bangkrut' 1 'Bangkrut'
 /train 0 'Test' 1 'Train'.
VARIABLE LABELS WC_TA 'Working Capital to Total Assets; skala dataset'
 RE_TA 'Retained Earnings to Total Assets; skala dataset'
 ROA_A 'ROA(A) before interest and % after tax; skala dataset'
 EQ_LIAB 'Equity to Liability; skala dataset'
 TURNOVER 'Total Asset Turnover; skala dataset'.
FREQUENCIES VARIABLES=bankrupt train.
DESCRIPTIVES VARIABLES=WC_TA RE_TA ROA_A EQ_LIAB TURNOVER
 /STATISTICS=MEAN STDDEV MIN MAX.
DISCRIMINANT GROUPS=bankrupt(0 1)
 /VARIABLES=WC_TA RE_TA ROA_A EQ_LIAB TURNOVER
 /SELECT=train(1)
 /ANALYSIS=ALL
 /METHOD=DIRECT
 /PRIORS=SIZE
 /STATISTICS=MEAN STDDEV UNIVF COV GCOV BOXM RAW COEFF TABLE CROSSVALID
 /CLASSIFY=NONMISSING POOLED
 /SAVE=CLASS=pred_spss PROBS=post_spss SCORES=disc_spss.
SAVE OUTFILE='Data_Hasil_SPSS.sav'.
OUTPUT SAVE OUTFILE='Output_Diskriminan.spv'.
* CROSSVALID adalah leave-one-out pada selected cases, berbeda dari OOF 5-fold Python.
* Bandingkan selected train 4773 dan unselected test 2046 secara terpisah.
* Jangan menamai keluaran di atas sudah tersedia sebelum menjalankan syntax ini.
