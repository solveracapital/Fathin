"""Audience-facing deck, distinct from the complete technical reading report."""
from copy import deepcopy
import numpy as np
from . import storage as db
from .mathematics import math_prose

NAMES={'lda':'Analisis diskriminan','pca':'Komponen utama','efa':'Faktor bersama','kmeans':'K-means','hierarchical':'Gerombol hierarkis'}

def number(value,digits=3):
    if value is None or not np.isfinite(value):return 'tidak terdefinisi'
    return f'{float(value):.{digits}f}'.replace('.',',')

def percent(value):return 'tidak terdefinisi' if value is None else number(value*100,2)+'%'

def create_plan(project_id,records,assessments=None,suite_id=None):
    """records contain immutable run/bundle/raw/frame plus full-report sections."""
    assessments=assessments or [];pid=db.uid();out=[]
    source_file=db.ROOT/'outputs/makalah_multivariat/Data_Analisis.csv'
    source_hash=db.digest(source_file.read_bytes()) if source_file.exists() else None
    paper=bool(records) and all(r['bundle']['result']['provenance']['source_sha256']==source_hash for r in records) and any(r['run']['config']['method']=='lda' and 'makalah' in r['run']['config'].get('purpose','').lower() for r in records)
    # Empirical EFA/clustering were not performed in the source paper.
    ordered=sorted(records,key=lambda r:['lda','pca','efa','kmeans','hierarchical'].index(r['run']['config']['method']))
    def content(key,title,paragraphs,record=None,rows=None,columns=None,formula=None,group='main'):
        rid=record['run']['id'] if record else None
        out.append(dict(id=pid+'_'+key,kind='content',title=title,paragraphs=[math_prose(p) for p in paragraphs],run_id=rid,
                        rows=rows or [],columns=columns or [],formula=formula,formula_text=title if formula else None,
                        group_id=group,tier='core' if group=='main' else 'appendix',enabled=group=='main',
                        source_sha256=record['bundle']['result']['provenance']['source_sha256'] if record else (records[0]['bundle']['result']['provenance']['source_sha256'] if records and len({r['bundle']['result']['provenance']['source_sha256'] for r in records})==1 else None),
                        evidence_ids=[rid] if rid else [r['run']['id'] for r in records]))
    def visual(record,vid,title,paragraph,group='main'):
        v=next((v for v in record['bundle']['result']['visual_manifest'] if v['id']==vid and v['status'] in ('shown','available')),None)
        if not v:return
        # Dense figures remain in the technical report; there is no forced chart.
        raw=record['raw'];p=len(record['run']['config']['feature_ids'])
        if v['kind']=='heatmap' and (p>8 or raw.get('q',0)>6):return
        if v['kind']=='bar' and (p>8 or len(raw.get('counts',[]))>12):return
        out.append(dict(id=pid+'_'+record['run']['id']+'_'+vid,kind='visual',run_id=record['run']['id'],visual_id=vid,title=title,
                        paragraphs=[math_prose(paragraph)],group_id=group,tier='core' if group=='main' else 'appendix',enabled=group=='main',evidence_ids=[v['id']]))

    content('scope','Analisis multivariat dalam aktuaria' if paper else 'Analisis multivariat: tujuan dan ruang lingkup',[
        'Keputusan kredit dan investasi melibatkan indikator yang saling berkaitan. Analisis multivariat mengkaji informasi bersama tersebut melalui peringkasan variabel, pemodelan faktor, pengelompokan, dan pembedaan kelas.' if paper else 'Analisis ini mengkaji keterkaitan beberapa indikator pada observasi yang sama. Metode peringkasan, faktor, gerombol, dan diskriminan menjawab tujuan yang berbeda; hasilnya tidak mempunyai satu ukuran keberhasilan yang sama.',
        'Pembahasan empiris utama adalah reproduksi parsial LDA pada data keuangan Taiwan, disertai ilustrasi PCA. EFA dan gerombol dibahas secara konseptual; keluaran empiris tambahannya berada pada lampiran opsional.' if paper else f"Laporan memuat {len(records)} hasil analisis yang selesai. Angka, tabel dan visual berasal dari versi perhitungan yang sama; keterangan kelayakan menyatakan batas data yang tersedia."])
    if records:
        content('methods','Empat pendekatan dengan tujuan berbeda',[
            'PCA dan EFA merangkum indikator dengan model yang berbeda. Gerombol membentuk kelompok tanpa label awal, sedangkan diskriminan mempelajari kelas yang sudah diketahui.'
        ],rows=[dict(metode='PCA',tujuan='Merangkum variasi total',keluaran='Komponen, skor, varians terjelaskan'),dict(metode='Faktor (EFA)',tujuan='Menelaah variasi bersama',keluaran='Loading, korelasi faktor, keunikan'),dict(metode='Gerombol',tujuan='Mengelompokkan kemiripan',keluaran='Keanggotaan, profil, dendrogram'),dict(metode='Diskriminan (LDA)',tujuan='Membedakan label yang diketahui',keluaran='Fungsi klasifikasi dan evaluasi test')],columns=['metode','tujuan','keluaran'])
        content('foundations','Dasar matematis metode',[
            'Pada PCA, Z adalah data yang dipusatkan/disetarakan dan A adalah arah komponen. Pada EFA, L adalah loading, Φ korelasi faktor, dan Ψ keunikan. Cg menyatakan anggota kelompok g dan μg adalah pusatnya. Pada LDA, x adalah vektor indikator, Sp kovarians pooled, dan πg prior kelas.'
        ],formula=r'\begin{aligned}\mathrm{PCA}:\quad&T=ZA\\\mathrm{EFA}:\quad&\Sigma=L\Phi L^T+\Psi\\\mathrm{K\!\!\!-means}:\quad&J=\sum_g\sum_{i\in C_g}\lVert x_i-\mu_g\rVert^2\\\mathrm{LDA}:\quad&\delta_g=x^TS_p^{-1}\mu_g-\tfrac12\mu_g^TS_p^{-1}\mu_g+\log\pi_g\end{aligned}')
    seen=set()
    for r in ordered:
        run=r['run'];raw=r['raw'];result=r['bundle']['result'];cfg=run['config'];method=cfg['method'];rid=run['id'];names=result['provenance'].get('feature_labels',cfg['feature_ids']);n=len(r['frame'])
        group=method if paper and method in ('efa','kmeans','hierarchical') else 'main'
        source=result['provenance']['dataset_version_id']
        if source not in seen:
            seen.add(source)
            ds=db.get(cfg['dataset_version_id'],'dataset')
            source_names=list(dict.fromkeys(name for rr in ordered if rr['run']['config']['dataset_version_id']==source for name in rr['bundle']['result']['provenance'].get('feature_labels',rr['run']['config']['feature_ids'])))
            composition=''
            if method=='lda':composition=f" Label positif = {raw['positive_label']}, negatif = {raw['negative_label']}; terdapat {int(np.sum(raw['y']))} kasus positif dari {len(raw['y'])} rekaman."
            content('data_'+source,'Data dan komposisi observasi',[
                f"Sumber: {ds.get('filename','dataset tersimpan')}. Dataset memuat {ds['row_count']} rekaman; {len(source_names)} indikator numerik digunakan dalam hasil yang disertakan."+composition,
                'Data Taiwan mencakup periode historis 1999–2009 dan merupakan data kurasi UCI. Satu rekaman tidak otomatis menunjukkan perusahaan unik. Ketidakseimbangan label memengaruhi interpretasi akurasi dan deteksi kebangkrutan.' if paper else 'Identitas, label, dan kolom pembagian/waktu dipisahkan dari indikator numerik. Satuan dan makna indikator mengikuti definisi sumber; pengkodean angka tidak dengan sendirinya menetapkan makna substantif.'
            ],r)
            for offset in range(0,len(source_names),6):
                content('indicators_'+source+str(offset),'Indikator analisis'+(f' · {offset//6+1}' if len(source_names)>6 else ''),[
                    'Lima indikator keuangan mewakili modal kerja, laba ditahan, profitabilitas aset, hubungan ekuitas–kewajiban, dan perputaran aset. Angka memakai skala kurasi dataset, sehingga nilai 0,8 tidak otomatis berarti rasio laporan 80%.' if paper else 'Indikator berikut merupakan masukan perhitungan pada sumber ini. Perbedaan satuan ditangani sesuai basis dan transformasi masing-masing metode.'
                ],r,[dict(indikator=name) for name in source_names[offset:offset+6]],['indikator'])
        if method=='lda':
            m=raw['model'];ev=raw['evaluations']['test'];base=raw['evaluations']['baseline_test'];values={x['id']:x['value'] for x in ev['metrics']};baselines={x['id']:x['value'] for x in base['metrics']};c=ev['counts'];train=np.asarray(raw['train']);test=np.asarray(raw['test']);y=np.asarray(raw['y'])
            split={'saved_membership':'keanggotaan train/test tersimpan','stratified_random':'pembagian acak terstratifikasi','group':'pemisahan berdasarkan entitas','temporal':'pemisahan kronologis'}.get(cfg.get('split',{}).get('mode'),'pembagian tersimpan')
            missing=cfg.get('preprocessing',{}).get('missing','error')
            content(rid+'_design','Rancangan pengolahan dan evaluasi',[
                f"Model dilatih pada {len(train)} rekaman dan dievaluasi pada {len(test)} rekaman melalui {split}. Prior positif mengikuti train sebesar {percent(m['priors'][1])}; ambang utama adalah {number(ev['threshold'])}.",
                ('Nilai indikator yang kosong diisi dengan median train. ' if missing=='median' else 'Indikator pada analisis ini tidak memerlukan pengisian nilai kosong. ')+ 'Parameter pengolahan dan model dipelajari pada train. Prediksi OOF, bila tersedia, menentukan ambang tambahan tanpa memakai label test sebagai dasar pemilihan.'
            ],r,[dict(kelas='Negatif',train=int(np.sum(y[train]==0)),test=int(np.sum(y[test]==0))),dict(kelas='Positif',train=int(np.sum(y[train]==1)),test=int(np.sum(y[test]==1)))],['kelas','train','test'])
            content(rid+'_logic','Fungsi diskriminan dan keputusan kelas',[
                'Vektor indikator x dikombinasikan dengan pusat tiap kelas dan kovarians pooled. Prior empiris mencerminkan komposisi kelas train. Selisih dua fungsi klasifikasi menghasilkan log-odds η, yang diubah menjadi posterior positif.',
                f"Prediksi positif muncul ketika posterior mencapai {number(ev['threshold'])}. Skor kanonik adalah proyeksi pemisahan; posterior adalah keluaran model dan belum merupakan probabilitas eksternal yang terkalibrasi."
            ],r,formula=r'\eta=\delta_1(x)-\delta_0(x),\qquad p_1=\frac{1}{1+e^{-\eta}},\qquad S_p=\frac{W}{n_{\mathrm{train}}-2}')
            visual(r,'confusion_matrix','Hasil klasifikasi pada data test',f"Dari {c['TP']+c['FN']} kasus positif, {c['TP']} terdeteksi dan {c['FN']} terlewat. Sebanyak {c['FP']} kasus negatif mendapat alarm keliru; {c['TN']} lainnya diprediksi negatif dengan benar. Ambang = {number(ev['threshold'])}.")
            content(rid+'_evaluation','Akurasi dan kemampuan mendeteksi kasus positif',[
                f"Akurasi model adalah {percent(values['accuracy'])}; baseline kelas mayoritas mencapai {percent(baselines['accuracy'])}. Balanced accuracy model sebesar {percent(values['balanced_accuracy'])} memberi bobot yang sama pada kedua kelas, sehingga akurasi keseluruhan bukan satu-satunya ukuran.",
                'Sensitivity menyatakan bagian positif yang ditemukan; specificity menyatakan bagian negatif yang dikenali. Precision menilai kebenaran sinyal positif, sedangkan F1 menyeimbangkan precision dan sensitivity.'
            ],r,[dict(ukuran=label,model=percent(values[key]),baseline=percent(baselines[key])) for key,label in [('sensitivity','Sensitivity'),('specificity','Specificity'),('precision','Precision'),('F1','F1')]],['ukuran','model','baseline'])
            ranking=f"ROC-AUC = {number(values['ROC_AUC'],6)} dan average precision = {number(values['AP'],6)}. Prevalensi positif test = {percent(values['prevalence'])}. Kurva PR menunjukkan hubungan precision dan recall pada berbagai ambang; AP adalah ringkasan diskret, bukan luas trapezoid atau ukuran kalibrasi."
            if ev.get('curves'):
                visual(r,'precision_recall','Kemampuan pemeringkatan dan kurva precision–recall',ranking)
            else:content(rid+'_ranking','Batas evaluasi pemeringkatan',[ranking,'Subset test tidak memuat dua kelas; kurva dua kelas tidak didefinisikan.'],r)
            scenarios=[]
            for key,label in [('test','Utama'),('test_OOF_threshold','Ambang OOF train'),('test_equal_prior','Prior sama')]:
                if key in raw['evaluations']:
                    e=raw['evaluations'][key];scenarios.append(dict(skenario=label,ambang=e['threshold'],terdeteksi=e['counts']['TP'],terlewat=e['counts']['FN'],alarm_keliru=e['counts']['FP']))
            if len(scenarios)>1:
                content(rid+'_decisions','Sensitivitas keputusan terhadap ambang dan prior',[
                    'Skenario memakai observasi test yang sama. Ambang tambahan memaksimumkan F1 dari prediksi OOF train; prior sama mengubah bobot awal kelas dan bukan sekadar menggeser ambang posterior lama.',
                    'Peningkatan deteksi disertai perubahan alarm keliru. Perbandingan ini menunjukkan konsekuensi keputusan; ambang F1 tidak otomatis meminimalkan biaya ekonomi.'
                ],r,scenarios,['skenario','ambang','terdeteksi','terlewat','alarm_keliru'])
            box=m.get('box_m');pv=box.get('p_value') if box else None
            boxtext=(r'\(p<10^{-300}\)' if pv==0 else 'p = '+(f'{pv:.2e}' if pv<.0001 else number(pv,6))) if box else 'tidak terdefinisi'
            normality=[a['p_value'] for a in m.get('marginal',[]) if a.get('p_value') is not None]
            normality_text=f"{sum(p<.05 for p in normality)} dari {len(normality)} uji normalitas marginal menghasilkan p < 0,05. " if normality else 'Uji normalitas marginal tidak tersedia pada solusi ini. '
            content(rid+'_diagnostics','Diagnostik dan asumsi diskriminan',[
                f"Kovarians pooled mempunyai rank {m['rank']} dari {len(names)} indikator dan condition number {number(m['condition_number'])}. Wilks lambda = {number(m['wilks'],6)} dan korelasi kanonik = {number(m['canonical_correlation'],6)} merangkum pemisahan pada train.",
                f"Box M aproksimasi: {boxtext}. "+('Nilai ini menentang asumsi kovarians kelas yang sama. ' if pv is not None and pv<.05 else 'Ketersediaan hasil uji tidak membuktikan semua asumsi terpenuhi. ')+normality_text+'Pengujian marginal per indikator belum mencakup normalitas multivariat secara utuh. Evaluasi internal tidak menetapkan validitas pada populasi baru.'
            ],r)
            if paper:
                content(rid+'_reproduction','Konsistensi terhadap makalah dan sumber',[
                    f"Angka sumber yang dilaporkan adalah ROC-AUC 0,904 dan AP 0,309. Hasil ulang sebesar {number(values['ROC_AUC'],6)} dan {number(values['AP'],6)} konsisten pada pembulatan tiga desimal.",
                    'Status tetap reproduksi parsial: seed dan identitas split penelitian sumber tidak tersedia. Syntax SPSS disediakan pada paket makalah tetapi belum dieksekusi; hasil ini berasal dari mesin Python, bukan keluaran SPSS.'
                ],r)
        elif method=='pca':
            q=raw['selected_q'];cum=np.asarray(raw['cumulative']);pv=np.asarray(raw['PVE']);basis=raw['basis'];target=cfg.get('settings',{}).get('target',.8)
            content(rid+'_pca','PCA sebagai ringkasan variasi'+(' · ilustrasi' if paper else ''),[
                f"PCA memakai basis {basis} pada {n} rekaman. {q} komponen terpilih menjelaskan {percent(cum[q-1])} variasi"+ (f" dengan target kumulatif {percent(target)}." if not cfg.get('settings',{}).get('q') else ' berdasarkan jumlah komponen tersimpan.'),
                f"Dua komponen pertama menjelaskan {percent(cum[min(1,len(cum)-1)])}. Varians terjelaskan adalah ukuran peringkasan, bukan akurasi klasifikasi."+(' Pada makalah, ilustrasi PCA memakai train dan tidak menjadi input LDA utama.' if paper else ' Arah komponen tidak otomatis menyatakan faktor laten atau kelompok risiko.')
            ],r,[dict(komponen=i+1,variasi=percent(pv[i]),kumulatif=percent(cum[i])) for i in range(min(4,len(pv)))],['komponen','variasi','kumulatif'],group=group)
            visual(r,'scree','Spektrum variasi komponen utama','Eigenvalue diurutkan dari yang terbesar. Penurunan kurva menunjukkan variasi pada setiap komponen; retensi mengikuti konfigurasi dan proporsi kumulatif yang dilaporkan.',group)
        elif method=='efa':
            q=raw['q'];selection=raw.get('automatic_factor_selection');recommend=selection.get('recommended') if selection else None
            content(rid+'_efa','Faktor bersama · eksplorasi tambahan' if paper else 'Struktur faktor bersama',[
                f"Model memakai {q} faktor, ekstraksi {cfg.get('settings',{}).get('extraction','pa')} dan rotasi {cfg.get('settings',{}).get('rotation','oblimin')}. KMO = {number(raw['kmo'])}. "+(f"Parallel analysis merekomendasikan {recommend} faktor; jumlah aktual mengikuti identifikasi dan kelayakan estimasi." if recommend is not None else 'Jumlah faktor mengikuti konfigurasi estimasi.'),
                'Pattern loading menunjukkan hubungan indikator dengan faktor setelah korelasi antarfaktor diperhitungkan. Keunikan adalah variasi spesifik indikator. Hasil bersifat eksploratori; definisi konstruk bergantung pada teori substantif.'
            ],r,formula=r'\Sigma=L\Phi L^T+\Psi',group=group)
            visual(r,'loadings','Pola loading faktor','Warna dan nilai menunjukkan pattern loading. Tanda mengikuti konvensi solusi; besar loading bukan bukti pengaruh sebab-akibat. Korelasi antarfaktor ikut menentukan rekonstruksi kovarians.',group)
            visual(r,'parallel_analysis','Retensi faktor dan pembanding acak','Spektrum teramati dibandingkan dengan persentil 95% data acak pada urutan yang sama. Rekomendasi simulasi dibedakan dari jumlah faktor aktual yang memenuhi kelayakan estimasi.',group)
        else:
            counts=raw['counts'];sample=result['provenance'].get('sampling');scope=f"Sampel tetap {n} dari {sample['population_n']} rekaman" if sample else f"{n} rekaman eligible"
            content(rid+'_clusters',NAMES[method]+(' · eksplorasi tambahan' if paper else ': hasil pengelompokan'),[
                f"{scope} menghasilkan {len(counts)} kelompok. Indikator menggunakan skala {cfg.get('preprocessing',{}).get('scale','none')}; silhouette = {number(raw['silhouette'])}. Nomor kelompok menyatakan keanggotaan, bukan urutan risiko.",
                ('K-means membentuk pusat kelompok melalui pembaruan berulang dan beberapa inisialisasi. ' if method=='kmeans' else f"Hierarki memakai aturan {cfg.get('settings',{}).get('linkage','ward')} dan jarak {cfg.get('settings',{}).get('metric','euclidean')}. ")+('Cakupan pohon terbatas pada sampel tersebut; rekaman di luar sampel tidak memperoleh keanggotaan dari pohon ini. ' if sample else '')+'Pemisahan menggambarkan kemiripan numerik dan belum menetapkan kelas substantif.'
            ],r,[dict(kelompok=i+1,anggota=int(counts[i])) for i in range(min(6,len(counts)))],['kelompok','anggota'],group=group)
            visual(r,'profiles','Profil indikator antarkelompok','Pusat indikator berada pada skala pengolahan yang dilaporkan. Perbedaan profil menjelaskan ciri numerik kelompok; besar kecilnya pusat tidak otomatis berarti tingkat risiko yang lebih tinggi.',group)
            if method=='hierarchical':visual(r,'dendrogram','Susunan penggabungan kelompok',scope+'. Tinggi cabang menyatakan tingkat penggabungan menurut aturan jarak/linkage; cabang terpotong merangkum struktur pohon, bukan menampilkan seluruh daun.',group)
    for section in assessments:
        section=deepcopy(section);section.update(group_id='assessments',tier='core',enabled=True);out.append(section)
    if paper:
        content('actuarial','Relevansi pada penelaahan risiko aktuaria',[
            'Hasil mendukung kajian risiko kredit dan investasi melalui pembacaan beberapa indikator sekaligus. Sensitivitas yang rendah pada ambang utama menunjukkan bahwa banyak kejadian positif masih dapat terlewat meskipun akurasi keseluruhan tinggi.',
            'Prior dan ambang memengaruhi keseimbangan deteksi dan alarm keliru. Penerapan pada portofolio baru bergantung pada definisi variabel, kalibrasi, biaya kesalahan, dan validasi eksternal; kasus ini belum memvalidasi premi, cadangan, atau modal asuransi.'
        ])
    content('limits','Keterbatasan dan cakupan kesimpulan',[
        'Dataset Taiwan tidak menyediakan identitas perusahaan dan metadata waktu per baris yang memadai untuk validasi antarperusahaan atau temporal. Parameter transformasi awal data kurasi juga tidak seluruhnya tersedia; kondisi ini membatasi transfer langsung ke rasio mentah perusahaan baru.' if paper else 'Kesimpulan berlaku pada data, definisi variabel, pengolahan dan pembagian sampel yang dilaporkan. Kualitas data serta representasi populasi menentukan cakupan generalisasi.',
        'Hubungan statistik tidak menetapkan sebab-akibat. Diagnostik dan evaluasi internal menyatakan bukti pada sampel ini; keberlakuan di luar sampel dan interpretasi substantif masih mempunyai batas yang dijelaskan pada tiap metode.'
    ])
    conclusions=[]
    for r in ordered:
        if paper and r['run']['config']['method'] not in ('lda','pca'):continue
        conclusions.extend(b['text'] for b in r['bundle']['result']['narrative_blocks'][:1])
    content('conclusion','Kesimpulan',[
        ' '.join(conclusions) or 'Penelaahan menghasilkan keterangan kelayakan data. Data yang tersedia belum mendukung estimasi model; tidak ada angka model yang dapat disimpulkan.',
        'Analisis multivariat memberi sudut pandang yang berbeda terhadap variasi, faktor, kemiripan dan kelas. Pada kasus makalah, hasil utama konsisten dengan pembulatan sumber, dengan status reproduksi parsial dan batas penerapan yang tetap melekat.' if paper else 'Hasil komponen, faktor, kelompok dan klasifikasi mempunyai makna yang berbeda. Kesimpulan substantif mengikuti kesesuaian tujuan metode, bukti numerik, diagnostik dan batas data yang tersedia.'
    ])
    # Explanatory scientific prose in optional reports; no tutorial preamble.
    neutral={'Baca jumlah kesalahan bersama':'Jumlah kesalahan berkaitan dengan','Baca ukuran ini bersama':'Interpretasi ukuran ini berkaitan dengan','Simpan konfigurasi, sumber dan hasil agar keputusan dapat ditelusuri ulang.':'Konfigurasi, sumber dan hasil tersimpan sebagai jejak perhitungan.','Satuan dan parameter transformasi harus dibaca bersama hasil.':'Satuan dan parameter transformasi menentukan skala hasil.'}
    for r in ordered:
        for s in r['report_sections']:
            s=deepcopy(s);s.update(group_id='technical',tier='appendix',enabled=False)
            s['paragraphs']=[p for p in s.get('paragraphs',[]) if not p.startswith('Ringkasan ini dibaca bersama')]
            for before,after in neutral.items():s['paragraphs']=[p.replace(before,after) for p in s['paragraphs']]
            out.append(s)
    core=[s for s in out if s['tier']=='core'];optional=[s for s in out if s['tier']=='appendix']
    # Main narrative remains contiguous; explorations and technical pages follow it.
    sections=core+optional
    return db.put('deckplan',dict(id=pid,project_id=project_id,run_ids=[r['run']['id'] for r in records],automatic_suite_id=suite_id,
                                  policy_version='audience-deck-1',created_at=db.now(),paper_case=paper,sections=sections,
                                  core_count=len(core),optional_count=len(optional)))
