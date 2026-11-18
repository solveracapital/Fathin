# PRD dan brief implementasi backend Multivariat Lab

Normatif bersama README dan SHARED_CONTRACT. Tujuan: mesin multivariat yang transparan, teruji, menghasilkan keluaran relevan, dan dapat direproduksi. Akurasi berarti sesuai definisi dan toleransi yang dibuktikan, bukan janji tanpa kesalahan floating point atau tanpa keterbatasan statistik.

## Arsitektur dan runtime

FastAPI/Pydantic API; service terpisah untuk import, profiling, planning, preprocessing, split, estimators, diagnostics, evaluation, visual_policy, explanations, documents, assistant, snapshots, export. SQLite menyimpan metadata/job; input dan artifact pada `var/projects/{opaque-id}/`. Simpan transaksi secara atomik (temporary file lalu rename); run sukses hanya setelah seluruh artifact wajib tersimpan dan hash valid. Data besar/array tidak dimasukkan ke satu kolom JSON SQLite.

Python: numpy, scipy, pandas, scikit-learn, openpyxl untuk membaca XLSX, pustaka exporter tabel yang sesuai, python-docx untuk extraction, pypdf untuk PDF teks, httpx untuk layanan AI. R: Rscript, psych, GPArotation, jsonlite. Gunakan paket stats sebagai pembanding EFA ML bila cocok, bukan menganggap hasil kedua estimator selalu identik. Environment aplikasi tersendiri dengan lock Python/JS/R; paket desktop authoring bukan runtime aplikasi. Setup Windows mendeteksi path Python/R dan dependensi tanpa menampilkan secret. R hilang tidak menghalangi metode Python, namun EFA wajib berstatus unavailable hingga dipasang.

Queue lokal persisten dengan satu worker proses awal; tidak perlu Redis/Celery. API tetap responsif saat fit; worker memanggil Rscript dengan daftar argumen aman, working dir run, input file terkontrol, stdout JSON, stderr log tersanitasi, timeout dan penghentian process tree. Tidak pernah interpolasi input pengguna menjadi shell/R code. Cleanup temp pada cancel/fail; output parsial tetap internal. Worker recovery menandai job terputus dan mengizinkan retry sebagai run baru.

## Impor dan kualitas data

Default limits dikonfigurasi dan diekspos capabilities: file50MiB, XLSX expanded250MiB, maksimum100000 baris ×200 kolom, PDF200 halaman, dokumen20MiB, job300detik (export120, AI60), satu job statistik serentak. Ini batas operasional V1, bukan jaminan semua kombinasi selesai dalam waktu tersebut. Estimasi memori sebelum matriks pairwise; hierarchical dan full silhouette mempunyai batas tambahan di bawah. Oversize ditolak dengan alasan dan alternatif sebelum alokasi besar.

Periksa signature file dan arsip, bukan extension saja. XLSX jangan menjalankan macro/formula/external link. Kolom berisi formula bukan raw numeric: minta values-only atau pilihan cached value yang dilabeli berpotensi stale; tidak mengevaluasi formula workbook user. XLSX hasil penelitian mengandung sheet hasil: hanya sheet terpilih menjadi input. Workbook Raw_Asli punya95 fitur+target; Data_Analisis punya ID,target,5fitur,train.

CSV deteksi encoding dengan fallback yang bisa ditinjau, delimiter/header/decimal/thousands eksplisit. Angka ambigu tidak dikonversi diam-diam. Pertahankan teks ID, leading zero, nama kolom asli, nomor baris sumber, dan checksum berkas. Dataset baru immutable setelah impor; setiap pemetaan/transformasi memiliki versi/config. Nonnumeric, NaN, ±Inf, constant, duplicate, jumlah unik, min/max, quantile, mean, SD(ddof1), skewness, excess kurtosis dicatat. Duplicate flag bukan bukti perusahaan yang sama. Sorting/filter preview tidak memodifikasi dataset.

General preprocessing default tidak menghapus/mengisi. User dapat memilih complete-case drop atau median imputation untuk fitur numerik; jumlah baris dan alasan dicatat. Target/ID/time tidak diimputasi. Jika missing target, default blocking sampai user memilih mengecualikan baris atau scoring-only yang sesuai. Transformasi didukung standard/robust scale dan log positif pilihan eksplisit; log nilai<=0 blocking. Winsorization/SMOTE tidak termasuk V1. Duplicate/outlier tidak dibuang otomatis.

Pada supervised, split sebelum fit transform; imputer/scaler fit hanya train dan diulang per fold. Metadata cleaning yang mengubah eligibility didefinisikan sebelum split. Kolom train contoh adalah split indicator, bukan fitur. Split eligibility dan row IDs disimpan, fitur urutan stabil. Untuk unsupervised analisis eksplorasi boleh fit pada semua baris eligible dan dilabeli demikian; bukan holdout predictive validation.

## Rencana analisis dan validasi

Planner menerima tujuan, variabel, metadata dan settings, mengembalikan prasyarat, warnings, blocking, preprocessing plan, split plan, result plan. AI boleh mengusulkan, planner deterministik memutuskan kelayakan. Acknowledge warning tidak boleh meloloskan formula yang tak terdefinisi.

LDA V1 tepat dua label, target positif dipilih eksplisit, numeric features>=1. PCA/EFA>=2 fitur untuk cakupan produk multivariat; cluster>=1 numeric feature dengan penjelasan bila satu dimensi. Feature ID, target, entity, time dikecualikan dari pemilihan default. Kelas tunggal blocking. Constant/linear dependence tidak dihapus otomatis: sampaikan kolom dan tindakan. Sample size kecil menjadi warning atau blocking sesuai operasi, jangan rasio n/p rekaan sebagai bukti validitas.

Split LDA: saved_membership (contoh), stratified_random default train70/test30 seed42, group split bila entity ada, temporal bila time ada. Seed dan actual memberships disimpan. Group split menjaga entitas terpisah; tidak menjanjikan proporsi kelas eksak. Temporal menjaga waktu train<test; gap opsional nonnegatif dan aturan cutoff tercatat. Group+time bersamaan butuh rencana eksplisit; V1 blok jika dua kendala tak bisa dipenuhi, jangan fallback random. Train wajib kedua kelas dan tiap group n>=2 untuk kovarians diagnostik; test satu kelas diperbolehkan dengan AUC/AP unavailable sesuai definisi evaluasi yang ditetapkan, confusion matrix tetap bentuk2×2. Stratified OOF5 untuk makalah; general folds=min(requested,min train class count), harus>=2, penurunan fold perlu terlihat sebelum run. Group/temporal OOF mengikuti desain dan tiap fold train harus kedua kelas; invalid fold blocking untuk threshold tuning. Jangan memakai random OOF saat desain meminta temporal/group.

## LDA matematika dan hasil

Default metode klasik full pooled covariance, entry simultan, prior empiris train, threshold0.5. Penelitian Taiwan tidak scaling tambahan. Untuk fitur x, label g, training mean mu_g, n_g, total n dan G=2:

```
W = sum_g sum_i_in_g (x_i-mu_g)(x_i-mu_g)^T
Sp = W/(n-G)
B = sum_g n_g(mu_g-mu)(mu_g-mu)^T
b_g = solve(Sp, mu_g)
c_g = -0.5 * mu_g^T b_g + log(prior_g)
delta_g(x) = x^T b_g + c_g
eta = delta_1 - delta_0
p1 = scipy.special.expit(eta)
prediction = positive iff p1 >= threshold
```

Prior >0, sum1; empirical/same/custom pilihan, custom dinormalisasi hanya setelah user melihat nilai efektif. Jangan hitung inverse eksplisit untuk prediksi. Cholesky/solve dan slogdet memeriksa positive-definite/rank/conditioning. Singular blocking dengan alternatif kurangi fitur; shrinkage/QDA bukan fallback tersembunyi dan di luar V1 utama. Catat singular values dan toleransi rank relatif eps*max(n,p)*largest singular value. Condition number tidak dijadikan batas alamiah validitas; warning default>=1e8 dicatat sebagai kebijakan numerik.

Canonical direction binary proporsional solve(Sp,mu1-mu0), dinormalisasi a^T Sp a=1, sign agar centroid positive lebih tinggi. a0=-a^Tmu train, D=a0+a^Tx, centroid per train group. Eigenvalue dari generalized eigensystem B a=lambda W a; bukan Sp^-1B tanpa faktor pembagi. r=sqrt(lambda/(1+lambda)), Wilks=1/(1+lambda). Approx chi2=-(n-1-(p+G)/2)*ln(Wilks), df=p pada binary; label aproksimasi dan suppress jika syarat statistik tidak layak. Standardized a_j sqrt(Sp_jj), structure coefficient corr pooled within-group = (Sp a)_j/sqrt(Sp_jj*a^TSp*a). Jangan mengganti dengan korelasi gabungan yang mencampur mean kelas.

Hasil wajib: n per split/class, prior, means, covariances group, W/B/Sp, rank, condition number raw/correlation, canonical raw/standardized/structure, centroids/eigen/r/Wilks, classification b/c, per-row eta/prediction/posterior/D, transform metadata, metrics dan formula trace. Coefficients pada skala input setelah transform dibedakan dari skala sumber; trace menunjukkan setiap tahap. Persentase canonical function pada binary bukan PVE PCA.

Diagnostics train: Pearson, Shapiro marginal per class/feature (jika n>5000 p-value beri peringatan keterbatasan; tidak membuktikan normalitas multivariat), skew/kurtosis, Mahalanobis per class dengan cutoff chi2 p quantile0.99 yang bersifat diagnostik, Box M approximate:

```
M=(n-G)logdet(Sp)-sum_g(n_g-1)logdet(S_g)
c=[(2p²+3p-1)/(6(p+1)(G-1))] * [sum_g1/(n_g-1)-1/(n-G)]
chi2=(1-c)M; df=(G-1)p(p+1)/2
```

Jika group covariance singular/logdet tak positif atau koreksi invalid, Box M unavailable dengan sebab; pooled fit tetap dapat sah jika Sp PD. Gunakan survival function untuk p-value kecil, underflow dilaporkan sebagai batas, bukan p=0 eksak. Tidak menolak semua penggunaan LDA hanya karena Box M signifikan. Metadata entity/time tidak tersedia harus tetap menjadi limitation walau tes numerik berhasil.

## Evaluasi, threshold, dan skenario

Confusion matrix baris aktual/kolom prediksi [negative,positive]. Metric accuracy=(TP+TN)/N; recall=TP/(TP+FN); specificity=TN/(TN+FP); precision=TP/(TP+FP); F1=2TP/(2TP+FP+FN); BA=(recall+specificity)/2. Denominator0 → null+undefined. BA undefined bila salah satu recall tak terdefinisi. F1 tetap0 bila denominator>0 dan TP0, termasuk baseline semua negatif saat ada positif. ROC-AUC membutuhkan kedua label; evaluasi AP untuk laporan produk ditandai unavailable jika salah satu kelas tidak ada agar tidak menyesatkan. Baseline mayoritas dan prevalensi subset wajib. Baseline semua negatif dengan kedua kelas AUC0.5, AP=prevalensi; precision undefined.

AP diskret sum (recall_k-recall_prev)*precision_k, ties benar, bukan trapezoid PR. Uji ke pustaka teruji. Simpan curve points dan threshold alignment; precision_recall_curve memiliki satu titik lebih banyak daripada thresholds; jangan memasangkan threshold ke titik terakhir tanpa pasangan.

OOF threshold: fit5fold stratified seed42 pada train contoh, prediksi tiap row dari model yang tidak melihat row itu, seluruh preprocessing fold-specific, pilih maksimum F1 pada threshold dari PR; ties pilih threshold pertama urutan ascending API yang dipakai, disimpan eksplisit. Refit model seluruh train, terapkan threshold ke test. OOF metric yang dipakai memilih threshold diberi selection estimate, bukan evaluasi bebas bias. Jangan optimasi threshold/seed/features pada test. OOF threshold0.12413099063180978 adalah referensi, bukan nilai hardcode.

Simulasi threshold menggunakan posterior tersimpan pada subset yang sama. Prior sama mengubah intercept/probabilitas, bukan koefisien geometri train; AUC/AP binary tidak berubah bila ranking sama. Simpan skenario berbeda. Fitur review capacity topK gunakan ranking dengan tie policy deterministic(row_id), laporkan precision@K, recall@K dan ties; bukan probabilitas kerugian. Simulasi cost opsional FP*C_FP+FN*C_FN dengan biaya hipotetis eksplisit, tidak expected loss. Calibration plot/Brier opsional hanya request dan kelas/jumlah data memadai; belum ada klaim posterior kalibrasi baik. Tidak menerapkan calibration ulang V1 otomatis.

## PCA

Basis correlation default untuk beda skala, covariance pilihan eksplisit. Center mean sampel, correlation scale SD ddof1, constant blocking. SVD/eigh dengan eigenvalue descending; simpan center, scale, eigenvectors, scores dan eigenvalue. Covariance dibagi n-1 konsisten. Correlation basis sum eigenvalue=p; PVE=lambda/sumlambda; score=Z*A. Loading correlation=A*sqrt(lambda) hanya jika Z unit variance; covariance PCA corr loading_jk=A_jk sqrt(lambda_k)/SD_j. Koefisien arah dibedakan dari loading. Sign align largest absolute element positive untuk deterministik; sign flip tidak substantif. Pilihan q=manual atau cumulative target default0.80; rekomendasi bukan kebenaran universal. Scree eigen>1 relevan hanya correlation. Contoh laporkan dua komponen dan tiga tanpa mengubah LDA.

Biplot jika q>=2 dan rank>=2: koordinat observasi scores PC1/2; arrows correlation loadings pada overlay axes -1..1 terpisah dan berlabel, bukan mengklaim jarak arrows sebanding jarak skor. Tampilkan PVE proyeksi. Tidak memasukkan target ke fit; warna label hanya anotasi opsional. Jika PCA dipakai di prediktor masa depan, fit dalam fold; V1 tidak menggabung PCA-LDA otomatis.

## EFA melalui R

Pearson correlation untuk indikator numeric kontinu V1. Ordinal/polychoric tidak otomatis disamakan dengan kontinu; user harus menegaskan asumsi atau metode unavailable. KMO overall/MSA dan Bartlett sphericity dengan n tepat, df=p(p-1)/2; singular matrix membuat diagnostik terkait unavailable/blocking. KMO<0.5 warning kelayakan (kebijakan, bukan bukti semua nilai di atas valid). Bartlett signifikan tidak menjamin konstruk. User menyatakan alasan indikator sebagai faktor bersama.

Ekstraksi `psych::fa` fm='pa' atau 'ml', default pa, jumlah faktor manual atau parallel analysis common-factor yang menyimpan konfigurasi. Parallel analysis seeded500 simulasi, quantile0.95, n/p sesuai eligible, mode common-factor bukan PCA; simpan actual implementation/version dan spectrum pembanding. Jika rekomendasi0faktor, laporkan tidak ada dukungan faktor; jangan paksa1. Manual q integer>=1,<p; ML perlu df=p(p-1)/2-p*q+q(q-1)/2>=0 serta solusi teridentifikasi layak, blok overspecified. PA juga periksa rank dan kelayakan parameter, hindari q besar dengan interpretasi palsu.

Rotasi varimax/oblimin/none, default oblimin. Tetapkan smoothing false, tidak imputasi/pairwise deletion otomatis; data lengkap prepared upstream. Tangkap warnings/convergence/Heywood uniqueness<=0 atau mendekati batas, residual, objective. Jangan mengembalikan angka gagal converge seolah valid. Simpan pattern L, Phi, structure=L*Phi untuk oblique, communalities diag(L Phi L^T), uniqueness=diag(R)-communalities, residual R-(L Phi L^T+Psi). Orthogonal Phi=I. Jelaskan factor naming saran tentatif dari indikator, bukan penemuan konstruk pasti. Score method regression default eksplisit; factor score optional, tidak tersedia jika solusi invalid. Ambang display abs loading0.30 menyembunyikan tampilan saja; full table tersedia. Sign/permutation/rotation equivalence diperhitungkan dalam test, jangan raw compare faktor yang tertukar.

## Clustering

K-means Euclidean, mean-based, standardization default sesuai fitur (pilihan none harus ditinjau); k-means++ init, n_init20, max_iter300,tol1e-4,seed42. Simpan actual iterations/convergence/inertia, centroid skala transform dan original, counts, distributions, membership. K manual default3 hanya jika n/unique memadai; sarankan range2..min(10,n_unique-1) dengan cap biaya. Tidak menjalankan pencarian K tanpa request/rencana. K<=n_unique; solusi cluster lebih sedikit akibat duplicate diberi status invalid untuk K yang diminta.

Hierarchical agglomerative: Ward default Euclidean, average/complete/single tersedia Euclidean atau Manhattan; Ward+Manhattan ditolak. SciPy linkage ward memakai observation matrix Euclidean, tidak squared-distance input yang dikuadratkan ulang; tulis konvensi Ward variance objective. K atau cut height dipilih eksplisit. Maksimum n3000 untuk full hierarchical V1: lebih besar tawarkan sampled exploratory run dengan seed/jumlah disetujui atau kmeans full; tidak diam-diam clustering sample lalu mengklaim seluruh populasi.

Silhouette valid2<=n_clusters<=n-1, metric sesuai fit. n>2000 pakai deterministic sample maksimal2000 dengan seed dan label approximate, atau unavailable bila sampling tak mewakili kelompok; jangan alokasi pairwise penuh100k. Full membership tetap disimpan jika fit full. Profile cluster adalah penjelasan utama; scatter2D hanya opsional bila dimensi/proyeksi layak, label projection. Dendrogram truncate last30leaves dengan jumlah anggota dan caption, data full tree bisa diunduh pada batas n. Tidak memakai true label untuk memilih cluster; cross-tab terhadap label bila diminta berstatus perbandingan setelah fit.

## Kebijakan visual deterministik

Visual dipilih melalui fungsi murni `plan_visuals(purpose,method,profile,result,request,limits)`, diuji dengan fixture. Default jangan lebih dua visual utama per bagian; detail opsional available. Simpan alasan untuk shown/available/omitted/unavailable. Tidak ada chart tanpa data finite layak, caption, subset,n,unit,provenance dan alternatif tabel.

| Konteks | Default | Kondisi tambahan / kapan dihilangkan |
|---|---|---|
| Profil numeric | Tabel ringkas; histogram fitur pilihan pertama nonconstant | Jangan semua95histogram; user pilih fitur. Boxplot perkelas hanya label tersedia dan group cukup; singleton tampil titik, bukan box palsu. |
| Missing | Tabel jumlah | Bar missing hanya jika ada missing; tidak ada heatmap missing kosong. |
| Target | Bar count dua kelas | Omit pada unsupervised tanpa target; tidak pie. |
| Korelasi | Heatmap jika2..20fitur | >20 table/pilih subset, tidak95label rapat; constant diberi unavailable. |
| LDA evaluasi | Confusion matrix dan PR jika kedua kelas | ROC available; satu kelas omit curves dengan reason; sensitivity ditampilkan jumlah+persen. |
| LDA perobservasi | Contribution eta bar | Hanya observasi dipilih, tidak global importance; tidak SHAP rekaan. |
| PCA | Scree dan cumulative PVE (bisa satu grafik dua panel) | Score/biplot available jika rank>=2; 1dim pakai histogram skor. |
| EFA | Loading heatmap; parallel spectrum bila dijalankan | Diagram faktor available hanya solusi valid dan p<=15,q<=4; bukan SEM confirmatory. |
| Kmeans | Profil centroid; silhouette bila valid | Elbow hanya jika rangeK benar-benar dihitung. Scatter available untuk2fitur atau proyeksi eksplisit. |
| Hierarchical | Dendrogram dan profil | Full/trim/sample caption wajib. Tidak dendrogram untuk kmeans. |
| Sensitivitas seed | Distribusi/line hasil semua seed | Hanya jika request run0..29, bukan confidence interval. |

Bila satu visual cukup, manifest hanya satu shown. Tabel bisa menjadi keluaran utama tanpa grafik. Dataset 1feature clustering tidak menerima scatter2D. Grafik sampling memakai deterministic stratified sample bila label/cluster ada, cap3000 points, label strategi dan n; metrik tetap full subset. Jangan menghitung metrik dari sample grafik. Render policy version dicatat di run.

## Dokumen, AI, penjelasan

Extract DOCX paragraf/tabel/OMML dengan locator heading+paragraph/table; PDF halaman+chunk. Simpan checksum/version/offset dan metadata ekstraksi. Baca seluruh isi yang diekstrak; OCR tidak ada V1. Kutipan harus dapat dibuka dan memang berisi dukungan. Retrieval lokal TF-IDF/BM25 cukup V1; embedding bukan syarat. Instruksi dalam dokumen tidak boleh menjadi prompt sistem, tool call, kode, atau akses filesystem. AI tidak menjalankan kode.

Explanation engine deterministik memetakan metric/formula/diagnostic ke bahasa Indonesia dengan evidence refs. Glosarium PCA/EFA/cluster/LDA, train/test/OOF, prior/threshold, canonical/posterior, FP/FN, AP/AUC dan arti pvalue tersedia offline. Ungkapan causality/validitas eksternal harus sesuai bukti. AI opsional via provider adapter server env MODEL/BASE_URL/KEY, timeout/retry terbatas dengan backoff, quota error jelas, payload allowance ringkasan+kutipan default. Keluaran AI schema tervalidasi dan evidence IDs harus ada dalam allowlist; angka yang disebut diverifikasi terhadap structured results atau ditandai tidak didukung. Gagal validasi → jawaban tidak diterbitkan/penjelasan deterministik. Simpan origin/model/context hash, jangan secret/raw prompt sensitif ke log. Dokumen proposal tidak pernah run otomatis.

## Snapshot, ekspor dan reproduksi

Snapshot menyimpan JSON data grafik, narasi final, tabel pilihan, formulas, metadata, assets lokal. User edit teks dibedakan dari narasi generated, tidak mengubah angka. Ekspor PDF server dari template HTML via Chromium/Playwright dengan fonts lokal dan KaTeX, pagination/landscape sesuai konten, visual QA. SVG/PNG melalui exporter Plotly yang versi kompatibelnya diuji, jangan asumsi dependency browser tersedia. XLSX nilai/table dan formula aman bila dibuat, CSV UTF8 locale documented. Package ZIP berisi dataset yang user izinkan, config.json, split row IDs, predictions, matrices, versions/lock, script rerun, README, SHA256 manifest; jangan sertakan env, API key, temp, file di luar project. Kegagalan exporter bukan run statistik gagal; job export failed terpisah dan hasil tetap tersedia.

Model scoring persisted hanya artifact internal terpercaya (JSON/npz aman), schema+ordered features+units+transforms+versions, tidak unsafe pickle user. Model Taiwan baru boleh scoring input eksternal jika kesetaraan transform donor dapat dibuktikan; karena sekarang tidak tersedia, default scoring model contoh terhadap raw rasio eksternal diblokir. User masih bisa melatih model baru pada data sendiri.

## Acuan Taiwan dan toleransi wajib

Gunakan Data_Analisis.csv asli dari paket, baca split train yang tersimpan; hitung ulang dari X/y. Fixture reference metadata bukan mesin prediksi. Assert n6819,train4773,test2046; train class[4619,154],test[1980,66]; missing/duplicate pada5fitur+label0.

| Besaran | Referensi |
|---|---|
| TN,FP,FN,TP | 1973,7,54,12 (eksak) |
| AUC | 0.903749617385981 |
| AP | 0.30852372633028535 |
| eta slopes (urutan WC_TA RE_TA ROA_A EQ_LIAB TURNOVER) | -9.93478521152798,-3.064545067805284,-23.27870514660725,-3.710613797764182,0.23311138307288992 |
| eta intercept | 19.151833358695626 |
| canonical intercept | 13.36077078627681 |
| canonical slopes | -5.514369155618946,-1.7009962911226426,-12.921001401645457,-2.0596010723072204,0.12939003644982536 |
| eigen canonical / r / Wilks | 0.1013895332862575 /0.3034073445309147 /0.9079439832846987 |
| centroid0/1 | -0.05812887693485891 /1.7434888478061108 |
| PCA correlation train eigen | 1.9683301,1.28136996,0.99317763,0.46554536,0.29157695 (angka pembulatan) |
| TW03598 eta / posterior | 5.017568759537845 /0.9934229406644826 |
| OOF threshold test TN,FP,FN,TP | 1921,59,38,28 |
| prior sama test TN,FP,FN,TP | 1747,233,20,46 |
| Box M / corrected chi2 / df | sekitar322.463 /318.712 /15 |

Counts/membership/order eksak; full precision coef atol1e-8 rtol1e-8; posterior atol1e-10; AUC/AP atol1e-10 untuk input dan konvensi identik; eigen pembulatan atol1e-7; Box M pembulatan atol0.002. Toleransi sumber artikel3desimal ±0.0005 berbeda dari toleransi internal. Jika gagal, cari sebab dan laporkan, jangan melonggarkan toleransi agar lolos. OOF tie/order dan library version harus dijelaskan jika threshold beda. Sklearn solver SVD boleh label/ranking sama dan posterior sedikit beda; jangan memaksa posterior identik dengan pooled convention tanpa audit.

## Pengujian wajib dan definisi selesai

- Unit formula fixture kecil hitung tangan; expit stabil untuk eta±1000; confusion denominator0, all-negative, one-class, ties AP/AUC; conservation TN+FP+FN+TP=N.
- LDA invariant posterior sum1, pooled covariance symmetric PD saat fit, canonical a^TSp a=1, centroid/sign, sigmoid(delta difference), affine transform nonsingular menjaga prediksi dalam toleransi. Compare solve versus independent implementation; jangan hanya membandingkan fungsi dengan dirinya sendiri.
- PCA reconstruction dengan seluruh komponen, orthonormal A, eigen sum, SDddof1, sign equivalence. EFA covariance reconstruction, Phi symmetry/PD, uniqueness, sign/permutation aligned, nonconverged failure; R output divalidasi finite/schema.
- Clustering n_members conservation, inertia independent recomputation, reproducibility seed, Ward metric invalid, silhouette sample metadata, K impossible. Performance cap mencegah pairwise OOM.
- Leakage test: ubah nilai test ekstrem tanpa mengubah fit train/scaler/OOF selected threshold. Entity overlap0, temporal ordering, row membership persistence. Test target tidak dapat masuk fitur dan train indicator tidak jadi feature.
- Visual policy table-driven cases: no target, one numeric, constant, missing0, p95, rank1 PCA, one class, k1, missing EFA convergence, no elbow request. Assert grafik tak relevan omitted dan tak ada payload palsu.
- API contract fixtures dan pagination, idempotency, cancel R, restart worker, stale revision, invalid uploads/path traversal/zipbomb, formulas safe, secret/log checks, AI evidence injection dan unavailable.
- Integrasi ekspor hasil sesuai run, SHA256 benar, PDF/grafik visual diperiksa, package rerun pada environment bersih menghasilkan metrik sama dalam toleransi.
- Bukti akhir: OpenAPI/schema/types/fixtures, test report lengkap beserta versi aktual, command setup/start/test, dependency health, benchmark Taiwan dan batas data, daftar keterbatasan. Jangan menyebut SPSS sudah diuji atau menghasilkan SPV; syntax SPSS opsional referensi belum dieksekusi.

Urutan: kontrak+fixture → ingestion/profiling/job → Taiwan LDA/PCA+tests → EFA/clustering+visual policy → explanations/docs/AI → snapshots/exports → integrasi FE dan acceptance. Semua tahap bagian V1 selesai, bukan alasan berhenti setelah demo hardcode.
