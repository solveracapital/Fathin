"""Full, deterministic reading report. All numerical statements use frozen run arrays."""
import numpy as np

NAMES={'lda':'analisis diskriminan','pca':'analisis komponen utama','efa':'analisis faktor','kmeans':'k-means','hierarchical':'gerombol hierarkis'}

def detailed_sections(add,run,bundle,raw,frame):
    cfg=run['config'];method=cfg['method'];features=cfg['feature_ids'];names=bundle['result']['provenance'].get('feature_labels',features)
    settings=cfg.get('settings',{});options=cfg.get('preprocessing',{});p=len(features);n=len(frame)
    f=lambda x: 'tidak terdefinisi' if x is None else f'{float(x):.6g}'
    def p_display(value):return '< 1e-300 (di bawah presisi numerik; bukan peluang nol)' if value==0 else f(value)
    def pages(key,title,paragraphs,rows,columns,size=4):
        for start in range(0,len(rows),size):
            add(key+f'_{start//size+1}',title+(f' · bagian {start//size+1}' if len(rows)>size else ''),paragraphs,rows[start:start+size],columns)
    purpose=cfg.get('purpose') or 'menelaah struktur beberapa indikator pada observasi yang sama'
    questions={'pca':'seberapa jauh variasi banyak indikator dapat diringkas dengan beberapa arah komponen','efa':'apakah korelasi indikator mendukung pola faktor bersama yang dapat diinterpretasikan','kmeans':'bagaimana observasi dapat dibagi menurut kedekatan profil numeriknya','hierarchical':'bagaimana kelompok terbentuk bertahap dan bagaimana pilihan pemotongan mengubah keanggotaan','lda':'seberapa baik indikator yang diketahui dapat membedakan dua kelas pada data evaluasi yang dipisahkan'}
    add('research','Pertanyaan, ruang lingkup, dan cara membaca laporan',[
        f"Tujuan yang dicatat pengguna adalah: {purpose}. Dalam {NAMES[method]}, pertanyaan operasionalnya ialah {questions[method]}. Unit perhitungannya adalah satu rekaman data dengan {p} indikator terpilih; arti substantif setiap indikator mengikuti definisi sumber, bukan ditebak dari besar angkanya.",
        'Laporan ini membedakan langkah pengolahan, hasil numerik, dan interpretasi. Jika beberapa metode dijalankan bersama, setiap metode memulai perhitungan dari data sumber dengan konfigurasinya sendiri. Komponen, faktor, kelompok, dan kelas prediksi mempunyai makna berbeda sehingga tidak boleh saling menggantikan atau dibandingkan sebagai satu ukuran akurasi.'
    ])
    t=raw.get('transform',{});missing=options.get('missing','error');scale=options.get('scale','standard' if method in ('kmeans','hierarchical') else 'none')
    add('processing_policy','Bagaimana data disiapkan dan apa yang berubah',[
        f"Perhitungan memakai {n} rekaman eligible. Kebijakan nilai kosong adalah {missing}; transformasi log natural {'digunakan' if options.get('log') else 'tidak digunakan'}; penskalaan tambahan adalah {scale}. Data dengan nilai tak hingga, fitur konstan, atau parameter yang tidak sah tidak dipaksakan menghasilkan model. Pengeluaran baris hanya mengikuti kebijakan yang dipilih, bukan untuk memperindah hasil.",
        ('Median pengisian, pusat, dan skala LDA dipelajari dari train saja, kemudian diterapkan ke test. OOF mengestimasi ulang pengolahan di setiap fold, sehingga observasi validasi fold tidak ikut menentukan parameter pengolahannya.' if method=='lda' else 'Parameter pengolahan dipelajari dari subset analisis yang disebutkan dalam laporan. PCA basis korelasi dan EFA menggunakan standardisasi/korelasi internal metode; memilih tanpa penskalaan tambahan tidak berarti metode tersebut mengabaikan pemusatan atau korelasi.')
    ])
    transformrows=[dict(indikator=names[j],median=t.get('median',[None]*p)[j],pusat=t.get('center',[None]*p)[j],skala=t.get('scale',[None]*p)[j]) for j in range(p)]
    pages('processing_values','Parameter pengolahan yang benar-benar digunakan',[
        'Tabel ini menunjukkan median, pusat, dan pembagi skala yang disimpan saat fitting. Untuk standard, pusat adalah mean dan skala adalah SD sampel; untuk robust, pusat adalah median dan skala adalah rentang antarkuartil. Pada pilihan none, pusat nol dan pembagi satu berarti tidak ada penskalaan tambahan.',
        'Urutan pengolahan adalah menangani nilai kosong, menerapkan log bila diminta, lalu mengurangi pusat dan membagi skala. Median pengisian ditampilkan pada skala sebelum log. Angka tampilan dibulatkan; perhitungan memakai presisi numerik tersimpan.'
    ],transformrows,['indikator','median','pusat','skala'])
    rows=[]
    subset=np.asarray(raw['train'],int) if method=='lda' else np.arange(n)
    for j,c in enumerate(features):
        x=frame.iloc[subset][c].to_numpy(float);finite=x[np.isfinite(x)]
        rows.append(dict(indikator=names[j],n_valid=len(finite),kosong=int(np.isnan(x).sum()),mean=float(np.mean(finite)),sd=float(np.std(finite,ddof=1))))
    pages('descriptive','Profil numerik sebelum pengolahan',[
        ('Deskripsi berikut memakai train, agar karakteristik test tidak dipakai untuk menentukan model.' if method=='lda' else 'Deskripsi berikut memakai subset analisis yang sama dengan metode ini.')+' Mean menunjukkan pusat aritmetik dan SD menunjukkan penyebaran sampel dengan penyebut n−1. Keduanya bukan ukuran pengaruh sebab-akibat atau tingkat risiko.',
        'Nilai valid menghitung observasi yang tersedia pada indikator tersebut. Jika kebijakan median dipilih, ringkasan sumber ini tetap menjelaskan data sebelum pengisian. Satuan dan kurasi sumber perlu diperhatikan; dua mean dari indikator dengan satuan berbeda tidak otomatis dapat dibandingkan langsung.'
    ],rows,['indikator','n_valid','kosong','mean','sd'])
    if method=='pca':
        eigen=np.asarray(raw['eigenvalues']);pv=np.asarray(raw['PVE']);q=raw['selected_q'];cumulative=np.asarray(raw['cumulative'])
        add('pca_selection','Mengapa jumlah komponen ini dipilih',[
            f"Basis yang digunakan adalah {raw['basis']}. Dari {p} komponen yang mungkin, konfigurasi memilih {q} komponen. Dasar pemilihannya adalah {'jumlah manual '+str(settings['q']) if settings.get('q') else 'target varians kumulatif '+f(settings.get('target',.8)*100)+'%'}. Komponen terpilih menjelaskan {f(100*cumulative[q-1])}% variasi pada subset analisis; sisanya {f(100*(1-cumulative[q-1]))}% tidak dipertahankan dalam ringkasan tersebut.",
            'Eigenvalue mengukur variasi pada arah komponen. PVE membagi eigenvalue dengan jumlah seluruh eigenvalue, sedangkan kumulatif menjumlahkan PVE dari komponen pertama sampai komponen yang dibaca. Pemilihan berdasarkan variasi tidak menjamin bahwa informasi yang penting untuk target klasifikasi atau teori penelitian ikut dipertahankan.'
        ])
        pages('pca_spectrum','Eigenvalue dan akumulasi variasi',[
            'Komponen diurutkan dari eigenvalue terbesar. Arah komponen saling ortogonal, sehingga komponen berikutnya menangkap variasi yang berbeda dari komponen sebelumnya. Nilai ini dihitung dari matriks basis yang dipilih, bukan hasil pengelompokan atau prediksi label.',
            'Kolom dipilih menunjukkan apakah komponen termasuk ringkasan konfigurasi ini. Tanda arah eigenvector dapat dibalik tanpa mengubah solusi PCA; aplikasi menetapkan tanda secara deterministik. Perbedaan tanda dengan software lain perlu diperiksa bersama konvensi, bukan langsung dinyatakan sebagai kesalahan.'
        ],[dict(komponen=i+1,eigenvalue=float(v),pve_persen=float(100*pv[i]),kumulatif_persen=float(100*cumulative[i]),dipilih='Ya' if i<q else 'Tidak') for i,v in enumerate(eigen)],['komponen','eigenvalue','pve_persen','kumulatif_persen','dipilih'])
        for k in range(q):
            load=np.asarray(raw['loadings'])[:,k];directions=np.asarray(raw['directions'])[:,k];order=np.argsort(-abs(load));top=', '.join(names[j] for j in order[:min(3,p)])
            pages(f'pca_loading_{k+1}',f'Makna dan pembentuk komponen {k+1}',[
                f"PC{k+1} menjelaskan {f(100*pv[k])}% variasi. Indikator dengan besar korelasi loading tertinggi adalah {top}. Tanda yang sama menunjukkan hubungan searah dengan skor komponen pada konvensi ini; tanda berlawanan menunjukkan arah berlawanan. Nama substantif komponen tetap memerlukan pengetahuan tentang indikator.",
                'Arah adalah koefisien untuk memperoleh skor dari data yang telah dipusatkan dan diskalakan sesuai basis PCA. Loading pada tabel adalah korelasi indikator dengan komponen, sehingga berbeda dari koefisien arah. Loading besar tidak berarti kontribusi sebab-akibat, dan nilai kecil tidak otomatis membenarkan penghapusan indikator.'
            ],[dict(indikator=names[j],arah=float(directions[j]),loading=float(load[j])) for j in range(p)],['indikator','arah','loading'])
        pages('pca_observation','Contoh skor komponen pada satu observasi',[
            f"Observasi contoh adalah {frame.iloc[0]['_row_id']}. Setelah pengolahan tambahan, data dikurangi pusat PCA dan dibagi skala PCA. Hasil vektor itu dikalikan matriks arah A untuk memperoleh skor T = Z A. Tabel menampilkan seluruh komponen terpilih dari skor yang disimpan.",
            'Skor positif atau negatif menyatakan posisi relatif pada arah komponen, bukan perusahaan baik atau buruk. Grafik dua sumbu hanya memakai PC1 dan PC2, sedangkan perhitungan mempertahankan jumlah komponen yang ditetapkan. Karena itu jarak pada gambar tidak boleh dianggap identik dengan jarak pada seluruh fitur.'
        ],[dict(komponen=k+1,skor=float(raw['scores'][0][k])) for k in range(q)],['komponen','skor'])
    elif method=='lda':
        m=raw['model'];train=np.asarray(raw['train']);test=np.asarray(raw['test']);ev=raw['evaluations']['test'];counts=ev['counts'];values={v['id']:v['value'] for v in ev['metrics']}
        add('lda_split_design','Mengapa pelatihan dan evaluasi harus dipisahkan',[
            f"Pembagian yang disimpan menggunakan mode {cfg.get('split',{}).get('mode','stratified_random')} dengan seed {cfg.get('split',{}).get('seed',42)}. Train berisi {len(train)} rekaman dan test {len(test)} rekaman. Model, pengolahan, dan prior empiris ditaksir dari train. Test menyediakan pengukuran kinerja pada observasi yang tidak ikut fitting model utama.",
            'Pembagian acak tidak otomatis menjaga pemisahan perusahaan atau periode waktu. Jika beberapa baris berasal dari entitas sama, gunakan pemisahan entitas; untuk pertanyaan masa depan gunakan desain temporal yang sesuai. Angka evaluasi ini adalah validasi internal sesuai split yang tersimpan, bukan bukti validasi pada populasi baru.'
        ])
        pages('lda_means','Pusat setiap kelas yang dipelajari model',[
            'LDA menghitung vektor mean untuk kelas negatif dan positif pada skala setelah pengolahan. Perbedaan pusat menjadi sumber arah pemisah, tetapi setiap perbedaan dibaca bersama kovarians antarprediktor. Karena itu selisih mean terbesar belum tentu mempunyai koefisien diskriminan terbesar.',
            f"Prior yang benar-benar digunakan adalah negatif {f(m['priors'][0])} dan positif {f(m['priors'][1])}. Prior merupakan bobot awal kelas dalam fungsi klasifikasi. Mengubah prior memengaruhi posterior serta keputusan, sehingga perbandingan hasil harus menyebutkan prior dan ambangnya."
        ],[dict(indikator=names[j],mean_negatif=m['means'][0][j],mean_positif=m['means'][1][j],selisih=m['means'][1][j]-m['means'][0][j]) for j in range(p)],['indikator','mean_negatif','mean_positif','selisih'])
        for start in range(0,p,3):
            cols=['indikator']+[f'kolom_{j+1}' for j in range(start,min(start+3,p))]
            pages(f'lda_covariance_{start}', 'Kovarians pooled yang masuk fungsi diskriminan',[
                'Matriks ini menggunakan Sp = W/(n_train−2), yaitu variasi dalam kedua kelas dengan derajat bebas gabungan. Diagonal menyatakan varians setiap indikator dan elemen di luar diagonal menyatakan kovarians. Invers/penyelesaian sistem matriks ini memperhitungkan hubungan antarindikator.',
                'Kolom pada bagian ini: '+ '; '.join(f"kolom_{j+1} = {names[j]}" for j in range(start,min(start+3,p)))+'. Matriks singular tidak diatasi dengan perbaikan tersembunyi; konfigurasi harus ditinjau. Kesamaan kovarians kelas adalah asumsi model, sedangkan keberhasilan membalik matriks hanya syarat komputasi.'
            ],[dict(indikator=names[i],**{f'kolom_{j+1}':m['Sp'][i][j] for j in range(start,min(start+3,p))}) for i in range(p)],cols)
        pages('lda_coefficients','Koefisien yang menghubungkan indikator dengan skor',[
            'Dua fungsi klasifikasi mempunyai koefisien b0 dan b1. Untuk setiap observasi, selisih skor adalah η = xᵀ(b1−b0) + c1−c0. Koefisien berikut berada pada skala setelah pengolahan yang telah dijelaskan; membandingkan besar koefisien mentah antarsatuan dapat menyesatkan.',
            'Koefisien kanonik membentuk satu proyeksi pemisah untuk dua kelas. Skor kanonik tidak sama dengan posterior: posterior adalah expit dari selisih fungsi klasifikasi, sedangkan skor kanonik mempunyai normalisasi tersendiri. Arah tanda kanonik ditetapkan untuk konsistensi interpretasi.'
        ],[dict(indikator=names[j],b0=m['b'][0][j],b1=m['b'][1][j],selisih=m['b'][1][j]-m['b'][0][j],kanonik=m['a'][j]) for j in range(p)],['indikator','b0','b1','selisih','kanonik'])
        add('lda_decoding','Membaca setiap jenis benar dan salah secara konkret',[
            f"Pada test, {counts['TN']} observasi negatif diprediksi negatif (TN), sedangkan {counts['FP']} observasi negatif mendapat sinyal positif (FP atau alarm keliru). Dari kelas positif, {counts['TP']} ditemukan (TP), tetapi {counts['FN']} diprediksi negatif dan terlewat (FN). Seluruh empat jumlah ini menjumlah menjadi {ev['n']} observasi evaluasi.",
            f"Keputusan utama menggunakan ambang {f(ev['threshold'])}: posterior yang mencapai ambang menjadi prediksi positif. Kelas positif mengikuti label yang dipilih pengguna, bukan otomatis kondisi yang diinginkan. Konsekuensi kesalahan FP dan FN perlu dibaca sesuai konteks penelitian; jumlah keduanya tidak mempunyai biaya ekonomi yang otomatis sama."
        ])
        definitions={
            'accuracy':('Akurasi','(TP+TN)/n','bagian seluruh prediksi yang benar; dapat tinggi karena kelas mayoritas'),
            'sensitivity':('Sensitivity','TP/(TP+FN)','bagian kasus positif yang berhasil ditemukan'),
            'specificity':('Specificity','TN/(TN+FP)','bagian kasus negatif yang benar-benar tidak diberi sinyal'),
            'precision':('Precision','TP/(TP+FP)','bagian sinyal positif yang merupakan kasus positif sebenarnya'),
            'F1':('F1','2TP/(2TP+FP+FN)','rata-rata harmonik precision dan sensitivity, bukan ukuran biaya finansial'),
            'balanced_accuracy':('Balanced accuracy','(sensitivity+specificity)/2','rata-rata cakupan kedua kelas dengan bobot sama'),
            'prevalence':('Prevalensi','(TP+FN)/n','proporsi kelas positif aktual dalam subset test'),
            'ROC_AUC':('ROC-AUC','luas kurva sensitivity terhadap false positive rate','kemampuan pemeringkatan; tidak mengukur kalibrasi probabilitas'),
            'AP':('Average precision','jumlah kenaikan recall × precision pada langkah itu','ringkasan diskret kurva precision–recall, bukan luas trapezoid')}
        for key,(label,formula,meaning) in definitions.items():
            value=values[key];baseline=next(v['value'] for v in raw['evaluations']['baseline_test']['metrics'] if v['id']==key)
            add('metric_'+key,f'{label}: nilai, definisi, dan cara menafsirkannya',[
                f"{label} pada model test adalah {f(value)} pada skala 0–1. Definisi matematisnya ditampilkan di bawah; ukuran ini menyatakan {meaning}. Nilai tidak terdefinisi ditampilkan secara eksplisit ketika pembilang/penyebut atau komposisi kelas tidak memenuhi syarat, sehingga tidak diganti dengan nol untuk membuat hasil tampak lengkap.",
                f"Baseline yang selalu memilih kelas mayoritas train menghasilkan {label} sebesar {f(baseline)} pada test yang sama. Baseline membantu menilai nilai tambah model, tetapi bukan pembanding semua model yang mungkin. Baca ukuran ini bersama jumlah FP/FN, prevalensi, dan tujuan penelitian; satu ukuran saja tidak cukup untuk menetapkan model siap digunakan."
            ])
        add('lda_assumptions','Apa yang dikatakan diagnostik model',[
            f"Rank kovarians pooled adalah {m['rank']} dari {p} fitur, dengan condition number {f(m['condition_number'])}. Condition number besar menunjukkan kepekaan numerik terhadap perubahan input. Wilks lambda sebesar {f(m['wilks'])} dan korelasi kanonik {f(m['canonical_correlation'])} merangkum pemisahan pada train; keduanya tidak menggantikan evaluasi test.",
            ('Box M aproksimasi menghasilkan p-value '+p_display(m['box_m']['p_value'])+'. Nilai kecil menentang asumsi kovarians yang sama, tetapi juga dipengaruhi ukuran sampel dan penyimpangan distribusi. ' if m.get('box_m') else 'Box M tidak dapat dihitung secara layak pada konfigurasi ini. ')+'Uji normalitas marginal memeriksa tiap indikator, bukan normalitas multivariat secara utuh. Tidak ada diagnostik tunggal yang membuktikan model pasti benar di luar data.'
        ])
        add('lda_oof_explanation','Logika pemilihan ambang dan sensitivitas keputusan',[
            (f"Prediksi OOF tersedia untuk {int(np.isfinite(np.asarray(raw['oof'],float)).sum())} dari {len(train)} rekaman train. Setiap skor OOF berasal dari model yang tidak mempelajari observasi tersebut. Ambang dengan F1 maksimum pada prediksi OOF adalah {f(raw['oof_threshold'])}; model utama tetap dipelajari dari train lalu diuji dengan ambang tersebut." if raw.get('oof') is not None else 'Pemilihan ambang OOF tidak diminta pada run ini. Ambang utama berasal dari konfigurasi pengguna; laporan tidak mengarang ambang optimal dari test.'),
            'Menurunkan ambang biasanya meningkatkan cakupan kasus positif sekaligus menambah alarm keliru. Skenario prior sama mengubah bobot awal kelas dan berbeda dari sekadar menggeser ambang pada posterior lama. Perbandingan skenario menjelaskan trade-off; test tidak digunakan untuk memilih ambang yang diklaim optimal atau membuktikan biaya kesalahan tertentu.'
        ])
    elif method=='efa':
        q=raw['q'];phi=np.asarray(raw['Phi']);res=np.asarray(raw['residual']);off=res[~np.eye(p,dtype=bool)];bart=raw['bartlett']
        add('efa_fit','Kelayakan korelasi dan hasil pemilihan faktor',[
            f"Solusi memuat {q} faktor dari {p} indikator, dengan ekstraksi {settings.get('extraction','pa')} dan rotasi {settings.get('rotation','oblimin')}. KMO keseluruhan adalah {f(raw['kmo'])}. KMO membandingkan korelasi sederhana dengan korelasi parsial; nilai rendah meminta peninjauan pola indikator, bukan otomatis membuktikan salahnya teori.",
            f"Bartlett menghasilkan chi-square {f(bart.get('chisq'))}, df {f(bart.get('df'))}, dan p-value {p_display(bart.get('p.value'))}. Uji ini memeriksa hipotesis matriks korelasi identitas, bukan mengesahkan jumlah faktor atau nama konstruk. RMS residual di luar diagonal sebesar {f(np.sqrt(np.mean(off**2)))} menunjukkan sisa korelasi yang belum dijelaskan model faktor."
        ])
        for k in range(q):
            pages(f'efa_pattern_{k+1}',f'Pola hubungan indikator dengan faktor {k+1}',[
                'Pattern merupakan koefisien indikator terhadap faktor setelah memperhitungkan faktor lain. Structure merupakan korelasi indikator dengan faktor. Pada rotasi oblique keduanya dapat berbeda karena faktor diizinkan berkorelasi; tanda dan urutan faktor mengikuti solusi tersimpan.',
                'Komunalitas adalah variasi indikator yang dijelaskan oleh semua faktor bersama, sedangkan uniqueness adalah sisa variasi dalam model korelasi. Loading besar membantu mengusulkan nama faktor berdasarkan isi indikator; laporan tidak menetapkan nama psikologis atau finansial tanpa alasan substantif.'
            ],[dict(indikator=names[j],pattern=raw['pattern'][j][k],structure=raw['structure'][j][k],komunalitas=raw['communalities'][j],keunikan=raw['uniqueness'][j]) for j in range(p)],['indikator','pattern','structure','komunalitas','keunikan'])
        pages('efa_phi','Korelasi antarfaktor dan batas skor faktor',[
            'Matriks Φ menyatakan korelasi antarfaktor. Pada solusi ortogonal elemen luar diagonal adalah nol; pada solusi oblique korelasi merupakan bagian model yang harus ikut dibaca. Menggunakan L Lᵀ saja untuk solusi oblique akan mengabaikan Φ dan dapat menghasilkan komunalitas yang keliru.',
            'Rekonstruksi model adalah L Φ Lᵀ + Ψ. Skor faktor dihitung dengan metode regresi dan merupakan taksiran, bukan pengamatan langsung variabel laten. Karena ketaktertentuan skor faktor, dua prosedur penaksiran dapat memberi skor berbeda meskipun model korelasinya serupa.'
        ],[dict(faktor_a=i+1,faktor_b=j+1,korelasi=phi[i,j]) for i in range(q) for j in range(i,q)],['faktor_a','faktor_b','korelasi'])
        add('efa_retention','Dasar jumlah faktor dan keterbatasan solusi',[
            (f"Jumlah faktor dipilih melalui parallel analysis faktor bersama dengan {raw['parallel']['n_iter']} simulasi. Eigenvalue teramati dibandingkan dengan persentil {raw['parallel']['quantile']*100:g}% simulasi pada urutan yang sama. Rekomendasi yang tersimpan adalah {raw['parallel']['recommended']} faktor; garis pembanding memakai persentil tersebut, bukan mean simulasi." if raw.get('parallel') else f"Jumlah {q} faktor ditetapkan manual. Parallel analysis tidak dijalankan, sehingga laporan ini tidak menyatakan bahwa simulasi mendukung pilihan itu. Jumlah faktor perlu dibenarkan oleh teori, interpretabilitas, dan residual model."),
            ('Pilihan otomatis menggunakan '+str(q)+' faktor yang memenuhi identifikasi dan kelayakan estimasi; rekomendasi simulasi tetap ditampilkan sebagai pembanding. ' if raw.get('automatic_factor_selection') else '')+'Perhitungan menolak matriks korelasi yang tidak positive definite, jumlah faktor berlebih, uniqueness tidak positif, dan kegagalan konvergensi yang terdeteksi. Solusi yang dapat dihitung tetap bersifat eksploratori. Pemeriksaan pada sampel independen diperlukan sebelum faktor dianggap sebagai konstruk yang terkonfirmasi.'
        ])
        if raw.get('engine')=='statsmodels':
            add('efa_conventions','Konvensi estimasi Python dan makna simulasi',[
                'Mesin EFA menggunakan statsmodels di Python. Principal axis dimulai dari squared multiple correlations (SMC), lalu memperbarui komunalitas sampai konvergen. Maximum likelihood mengestimasi model korelasi dengan optimasi yang diperiksa keberhasilannya. Rotasi oblimin memakai konvensi quartimin; untuk satu faktor rotasi tidak diperlukan. Tanda dan urutan faktor ditetapkan konsisten, tanpa mengubah kovarians yang dijelaskan.',
                'Jika jumlah faktor dipilih otomatis, spektrum awal menggunakan matriks korelasi dengan diagonal SMC. Pembandingnya berasal dari 500 simulasi indikator normal yang saling independen dengan jumlah observasi yang sama. Simulasi Wishart Bartlett menghasilkan korelasi sampel tersebut secara langsung; tidak mengurangi jumlah observasi secara diam-diam. Kebijakan ini dicatat terpisah dari konfigurasi ekstraksi. Jika jumlah faktor ditetapkan manual, simulasi tidak dijalankan.'
            ])
    else:
        labels=np.asarray(raw['labels']);centers=np.asarray(raw['centroids']);k=len(centers);scale=options.get('scale','standard')
        add('cluster_fit','Apa yang dilakukan algoritme pada data ini',[
            f"Metode {NAMES[method]} membentuk {k} kelompok dari {n} observasi pada {p} indikator. Penskalaan tambahan yang dipilih adalah {scale}, sehingga jarak dan pusat harus ditafsirkan pada skala tersebut. Nomor kelompok hanya identitas solusi; kelompok 1 tidak berarti paling aman, paling buruk, atau mempunyai risiko paling rendah.",
            (f"K-means menggunakan k-means++, 20 inisialisasi, seed {raw['seed']}, dan batas 300 iterasi. Solusi berhenti setelah {raw['iterations']} iterasi dengan inertia {f(raw['inertia'])}. Inertia adalah jumlah kuadrat jarak Euclidean anggota ke pusatnya; makin kecil pada data dan K yang sama berarti solusi lebih rapat, bukan otomatis lebih benar secara substantif." if method=='kmeans' else f"Hierarki memakai linkage {settings.get('linkage','ward')} dan jarak {settings.get('metric','euclidean')}. Semua penggabungan disimpan, kemudian pohon dipotong menjadi {k} kelompok. Pusat kelompok adalah ringkasan sesudah pemotongan; keanggotaan hierarkis tidak dihitung dengan aturan pusat terdekat k-means.")
        ])
        pages('cluster_sizes','Ukuran kelompok dan ketidakseimbangan anggota',[
            'Ukuran dan proporsi kelompok membantu menilai apakah solusi didominasi satu kelompok besar atau membentuk kelompok kecil. Kelompok kecil dapat mewakili profil khusus atau observasi ekstrem; jumlah anggota saja belum menjelaskan penyebab kemunculannya.',
            'Jumlah seluruh anggota harus sama dengan jumlah observasi eligible. Keanggotaan dapat ditelusuri pada tabel observasi dengan identitas baris. Jika K, skala, indikator, atau metode diubah, nomor kelompok dapat bertukar; perbandingan antarsolusi harus memakai anggota/profil, bukan menyamakan nomor secara langsung.'
        ],[dict(kelompok=g+1,jumlah=int(raw['counts'][g]),persen=float(100*raw['counts'][g]/n)) for g in range(k)],['kelompok','jumlah','persen'])
        for g in range(k):
            pages(f'cluster_profile_{g+1}',f'Pembacaan profil kelompok {g+1}',[
                f"Kelompok {g+1} berisi {int(raw['counts'][g])} observasi. Pusat setiap indikator dihitung sebagai mean anggota kelompok pada skala pengolahan. Jika standard dipilih, pusat positif berarti berada di atas pusat seluruh subset pada indikator tersebut; jika none dipilih, besar angka tetap mengikuti satuan sumber.",
                'Tabel menampilkan semua indikator agar penjelasan tidak hanya memilih indikator yang tampak menarik. Bandingkan pusat indikator yang sama antar kelompok, lalu gunakan definisi sumber untuk memberi arti profilnya. Hasil ini menyatakan kemiripan numerik dan tidak membuktikan perbedaan kausal atau label risiko yang resmi.'
            ],[dict(indikator=names[j],pusat=float(centers[g,j])) for j in range(p)],['indikator','pusat'])
        add('cluster_validation','Kualitas pemisahan dan hal yang belum dibuktikan',[
            f"Silhouette keseluruhan adalah {f(raw['silhouette'])}, dihitung pada {raw['silhouette_sample_n']} observasi. Skala silhouette berkisar −1 sampai 1: nilai lebih besar menunjukkan anggota relatif lebih dekat ke kelompok sendiri, nilai mendekati nol menunjukkan batas yang berimpit, dan nilai negatif menunjukkan anggota yang mungkin lebih dekat ke kelompok lain.",
            'Jika data melebihi batas sampel silhouette, sampel deterministik yang dicatat digunakan sehingga ukuran ini bukan evaluasi seluruh pasangan pada seluruh populasi. Solusi tunggal tidak membuktikan bahwa K optimal atau kelompok stabil terhadap semua seed dan perubahan data. Pilihan K memerlukan tujuan analisis, interpretasi profil, serta pemeriksaan sensitivitas yang sesuai.'
        ])
    if method=='lda':
        conclusion=f"Pada {ev['n']} observasi test, model menemukan {counts['TP']} kasus positif dan melewatkan {counts['FN']}, dengan {counts['FP']} alarm keliru. Sensitivity {f(values['sensitivity'])}, precision {f(values['precision'])}, ROC-AUC {f(values['ROC_AUC'])}, dan AP {f(values['AP'])} dibaca bersama pada ambang {f(ev['threshold'])}. Hasil ini menunjukkan kemampuan serta kesalahan model pada split internal yang tersimpan; posterior belum terbukti terkalibrasi pada populasi lain."
    elif method=='pca':
        conclusion=f"Sebanyak {q} komponen dipertahankan dari {p} indikator dan menjelaskan {f(100*cumulative[q-1])}% variasi subset analisis. Ringkasan menyisakan {f(100*(1-cumulative[q-1]))}% variasi di luar komponen terpilih. Indikator dengan besar loading PC1 tertinggi adalah {names[int(np.argmax(abs(np.asarray(raw['loadings'])[:,0])))]}. Hubungan tersebut membantu membaca arah komponen; varians terjelaskan tidak menyatakan akurasi klasifikasi."
    elif method=='efa':
        conclusion=f"Model eksploratori menghasilkan {q} faktor dengan KMO {f(raw['kmo'])} dan RMS residual di luar diagonal {f(np.sqrt(np.mean(off**2)))}. Makna faktor harus ditetapkan dari isi indikator beserta pattern, structure dan korelasi faktor yang disajikan. Hasil belum mengonfirmasi konstruk pada populasi lain; jumlah faktor dan rotasinya perlu alasan substantif."
    else:
        sizes='; '.join(f"kelompok {g+1}: {int(raw['counts'][g])} observasi" for g in range(k))
        conclusion=f"Solusi membagi {n} observasi menjadi {k} kelompok: {sizes}. Silhouette sebesar {f(raw['silhouette'])} pada {raw['silhouette_sample_n']} observasi merangkum pemisahan relatif. Profil setiap kelompok telah dijabarkan per indikator pada skala {scale}. Kelompok merupakan hasil kemiripan fitur, bukan label risiko resmi; solusi ini belum membuktikan K optimal atau kestabilan pada semua perubahan data."
    add('conclusion','Kesimpulan hasil dan tindak lanjut yang dapat dipertanggungjawabkan',[
        conclusion,
        'Gunakan tabel dan grafik sebagai bukti untuk menjelaskan pola yang benar-benar dihitung. Untuk penggunaan di luar sampel, langkah berikutnya adalah memeriksa definisi variabel, kualitas dan independensi rekaman, stabilitas solusi, serta validasi pada data lain. Laporan ini tidak mengubah pola eksploratori menjadi klaim sebab-akibat atau rekomendasi keuangan otomatis.'
    ])
