"""Presentation evidence derived from one immutable run, with no model refitting."""
import numpy as np
from .storage import clean

def sections_for_run(run,bundle,raw,frame):
    rid=run['id'];cfg=run['config'];method=cfg['method'];result=bundle['result'];out=[]
    names=result['provenance'].get('feature_labels',cfg['feature_ids'])
    def content(key,title,paragraphs,rows=None,columns=None,formula=None):
        plain={'lda':'δg(x) = xᵀ Sp⁻¹ μg − ½ μgᵀ Sp⁻¹ μg + log πg; p1 = 1 / (1 + exp(−(δ1−δ0)))','pca':'Skor T = Z A; PVE komponen k = eigenvalue k / jumlah eigenvalue.','efa':'Σ = L Φ Lᵀ + Ψ; kovarians bersama dijelaskan faktor, korelasi faktor, dan keunikan.','kmeans':'J = jumlah kuadrat jarak setiap observasi ke pusat kelompoknya.','hierarchical':{'ward':'ΔJ(A,B) = nA nB / (nA+nB) × kuadrat jarak kedua pusat.','average':'d(A,B) = rata-rata jarak semua pasangan anggota antarkelompok.','complete':'d(A,B) = jarak terbesar dari pasangan anggota antarkelompok.','single':'d(A,B) = jarak terkecil dari pasangan anggota antarkelompok.'}.get(cfg.get('settings',{}).get('linkage','ward'))}
        out.append(dict(id=rid+'_'+key,kind='content',run_id=rid,title=title,paragraphs=paragraphs,rows=rows or [],columns=columns or [],formula=formula,formula_text=plain.get(method) if formula else None,evidence_ids=[key],enabled=True))
    content('data_context','Apa yang diamati dalam data ini?',[
        f"Analisis menggunakan {len(frame):,} rekaman eligible dan {len(names)} indikator numerik. Satu baris adalah rekaman, bukan otomatis satu perusahaan unik.",
        f"Label {result['provenance'].get('target_label','kelompok')}: positif = {raw.get('positive_label')}; negatif = {raw.get('negative_label')}." if method=='lda' else 'Identitas entitas dan waktu perlu diperiksa sebelum hasil disebut validasi antarperusahaan atau temporal.'],
        [dict(subset=k,n=v['n']) for k,v in result['subset_definitions'].items()],['subset','n'])
    for start in range(0,len(names),8):
        content('variables' if start==0 else f'variables_{start//8+1}','Indikator yang masuk perhitungan'+(f' ({start+1}–{min(start+8,len(names))})' if len(names)>8 else ''),[
            'Nama dan urutan indikator berikut menentukan makna matriks, skor, dan visual.',
            'Contoh Taiwan memakai skala kurasi dataset; nilai 0,8 tidak otomatis berarti rasio laporan 80%.' if 'makalah' in cfg.get('purpose','').lower() else 'Satuan dan parameter transformasi harus dibaca bersama hasil.'],
            [dict(indikator=name,pengolahan=cfg.get('preprocessing',{}).get('scale','standard' if method in ('kmeans','hierarchical') else 'none')) for name in names[start:start+8]],['indikator','pengolahan'])
    if result['provenance'].get('automatic_decisions'):
        content('automatic_procedure','Mengapa sistem memilih prosedur ini?',result['provenance']['automatic_decisions'])
    if result['provenance'].get('sampling'):
        sample=result['provenance']['sampling']
        content('sample_scope','Cakupan contoh pada pohon kelompok',[f"Pohon memakai {sample['used_n']} dari {sample['population_n']} rekaman melalui sampel acak tetap. Pemilihan ini menjaga perhitungan dan tampilan tetap terbaca; pohon bukan hasil hierarkis seluruh populasi.",'Identitas semua rekaman yang benar-benar dipakai tersimpan. Kelompok dari contoh tidak otomatis memberikan keanggotaan untuk rekaman di luar contoh.'])
    if method=='lda':
        m=raw['model'];ev=raw['evaluations']['test'];train=np.array(raw['train']);test=np.array(raw['test']);y=np.array(raw['y'])
        content('procedure','Bagaimana model dan evaluasinya dipisahkan?',[
            f"Model dilatih pada {len(train):,} rekaman dan dievaluasi pada {len(test):,} rekaman test. Test memuat {int(y[test].sum())} kasus positif.",
            f"Prior kelas positif = {m['priors'][1]:.6f}. Kovarians bersama menggunakan W/(n−2). Pemilihan ambang tambahan memakai OOF train bila diaktifkan."],
            [dict(kelas='Negatif',train=int(sum(y[train]==0)),test=int(sum(y[test]==0))),dict(kelas='Positif',train=int(sum(y[train]==1)),test=int(sum(y[test]==1)))],['kelas','train','test'])
        content('formula','Dari beberapa indikator menjadi keputusan',[
            'Mean kelompok dan kovarians bersama membentuk dua fungsi klasifikasi. Selisih kedua skor menghasilkan η.',
            'Posterior diperoleh melalui expit(η). Kelas positif dipilih jika posterior mencapai ambang. Skor kanonik adalah proyeksi, bukan probabilitas.'],formula=r'\delta_g=x^TS_p^{-1}\mu_g-\tfrac12\mu_g^TS_p^{-1}\mu_g+\log\pi_g;\quad p_1=\frac1{1+e^{-(\delta_1-\delta_0)}}')
        rows=frame.to_dict('records');sample=next((i for i,r in enumerate(rows) if r['_row_id']=='TW03598'),int(test[0]))
        slopes=np.array(m['b'][1])-m['b'][0];x=np.array(raw['transformed'][sample]);constant=m['c'][1]-m['c'][0]
        for start in range(0,len(names),8):
            content('example' if start==0 else f'example_{start//8+1}',f"Contoh hitung observasi {rows[sample]['_row_id']}"+(f' ({start+1}–{min(start+8,len(names))})' if len(names)>8 else ''),[
                f"Konstanta η = {constant:.6f}; jumlah kontribusi seluruh {len(names)} indikator ditambah konstanta menghasilkan η = {raw['eta'][sample]:.6f}.",
                f"Posterior positif = {raw['probability'][sample]:.8f}. Ini contoh individual, bukan bukti akurasi seluruh model atau probabilitas eksternal yang terkalibrasi."],
                [dict(indikator=names[j],nilai_olah=float(x[j]),kontribusi=float(x[j]*slopes[j])) for j in range(start,min(start+8,len(names)))],['indikator','nilai_olah','kontribusi'])
        content('summary','Apa yang berhasil dideteksi?', [result['narrative_blocks'][0]['text'],
            'Baca jumlah kesalahan bersama precision, sensitivity, ROC-AUC, dan average precision. Akurasi tinggi dapat didominasi kelas mayoritas.'],
            [dict(ukuran={'accuracy':'Akurasi (%)','sensitivity':'Sensitivity (%)','precision':'Precision (%)','ROC_AUC':'ROC-AUC','AP':'Average precision'}[v['id']],model=(v['value']*100 if v['id'] in ('accuracy','sensitivity','precision') and v['value'] is not None else v['value']),baseline=next(((b['value']*100 if v['id'] in ('accuracy','sensitivity','precision') and b['value'] is not None else b['value']) for b in raw['evaluations']['baseline_test']['metrics'] if b['id']==v['id']),None)) for v in ev['metrics'] if v['id'] in ('accuracy','sensitivity','precision','ROC_AUC','AP')],['ukuran','model','baseline'])
    else:
        formula=result['formula_index'][0]['latex']
        explanations={
            'pca':['Data dipusatkan; basis korelasi juga menggunakan SD sampel agar varians indikator setara. Dekomposisi matriks menghasilkan arah dan eigenvalue.', 'Skor adalah koordinat observasi. Proporsi varians terjelaskan adalah eigenvalue dibagi jumlah eigenvalue; loading dan arah komponen mempunyai konvensi yang berbeda.'],
            'efa':['EFA memisahkan variasi bersama dari keunikan. Pattern matrix, korelasi antarfaktor Φ dan keunikan membentuk kovarians model.',f"Ekstraksi {cfg.get('settings',{}).get('extraction','pa')} dan rotasi {cfg.get('settings',{}).get('rotation','oblimin')}; KMO/Bartlett tidak membuktikan konstruk benar. Pemilihan jumlah faktor harus dibaca bersama teori dan residual."],
            'kmeans':['K-means menempatkan observasi ke pusat terdekat lalu memperbarui pusat. Algoritme memakai beberapa inisialisasi dan seed tersimpan.', 'Inertia mengukur jumlah kuadrat jarak pada skala pengolahan. Silhouette mengukur kekompakan relatif; nilai baik bukan bukti kelas risiko resmi.'],
            'hierarchical':[f"Penggerombolan hierarkis menggunakan aturan {cfg.get('settings',{}).get('linkage','ward')} dan jarak {cfg.get('settings',{}).get('metric','euclidean')}. Dendrogram merekam urutan dan tinggi penggabungan.",'Ward mempunyai tujuan kenaikan variasi dalam kelompok minimum. Average, complete, dan single memakai definisi jarak antarkelompok yang berbeda.']}
        content('formula','Bagaimana metode mengubah data menjadi hasil?',explanations[method],formula=formula)
        content('summary','Apa yang dirangkum oleh metode ini?', [result['narrative_blocks'][0]['text']],
            [dict(ukuran=m['label'],nilai=m['value']) for m in result['metrics']],['ukuran','nilai'])
    from .report_detail import detailed_sections
    detailed_sections(content,run,bundle,raw,frame)
    for visual in result['visual_manifest']:
        dense_factor=visual['kind']=='heatmap' and (len(names)>8 or raw.get('q',0)>6)
        if visual['status']=='shown' and not dense_factor:out.append(dict(id=rid+'_'+visual['id'],run_id=rid,kind='visual',visual_id=visual['id'],title=visual['title'],enabled=True))
    if method=='lda':
        compare=[]
        for key,name in [('test','Ambang utama'),('test_OOF_threshold','Ambang dari OOF train'),('test_equal_prior','Prior sama')]:
            if key in raw['evaluations']:
                e=raw['evaluations'][key];compare.append(dict(skenario=name,ambang=e['threshold'],terdeteksi=e['counts']['TP'],terlewat=e['counts']['FN'],alarm_keliru=e['counts']['FP']))
        content('decisions','Deteksi dan alarm keliru berubah bersama',[
            'Skenario di bawah dievaluasi pada observasi test yang sama. Ambang OOF dipilih dari train; prior sama mengubah probabilitas awal kelas.',
            'Ambang F1 bukan otomatis ambang terbaik secara ekonomi. Kapasitas penelaahan dan biaya kesalahan perlu informasi tambahan.'],compare,['skenario','ambang','terdeteksi','terlewat','alarm_keliru'])
        if 'makalah' in cfg.get('purpose','').lower():
            values={m['id']:m['value'] for m in ev['metrics']}
            content('reproduction','Seberapa jauh hasil mereproduksi makalah?',[
                'Pembanding berikut adalah angka tiga desimal yang dilaporkan dalam makalah. Toleransi pembulatan ±0,0005 berbeda dari toleransi pengujian internal.',
                'Status tetap reproduksi parsial: kesamaan angka tidak membuktikan identitas split penelitian sumber. SPSS belum diverifikasi melalui eksekusi.'],
                [dict(ukuran='ROC-AUC',makalah=.904,hasil=values['ROC_AUC']),dict(ukuran='Average precision',makalah=.309,hasil=values['AP'])],['ukuran','makalah','hasil'])
    content('limitations','Apa yang dapat dan belum dapat disimpulkan?',[
        *[d['explanation'] for d in result['diagnostics']][:2],
        'Pola statistik pada sampel ini bukan hubungan sebab-akibat. Validasi di populasi baru memerlukan definisi variabel dan desain yang sesuai.',
        'Kasus Taiwan membantu pembelajaran penelaahan risiko investasi; hasil ini belum memvalidasi premi, cadangan, atau modal asuransi.' if 'makalah' in cfg.get('purpose','').lower() else 'Simpan konfigurasi, sumber dan hasil agar keputusan dapat ditelusuri ulang.'])
    # Read in the order question -> data -> method -> detailed evidence -> evaluation -> limits.
    def priority(section):
        suffix=section['id'].removeprefix(rid+'_')
        if suffix=='research':return 0
        if suffix=='data_context':return 1
        if suffix.startswith('variables'):return 2
        if suffix.startswith(('processing_','descriptive')):return 3
        if suffix in ('procedure','formula','lda_split_design'):return 4
        if suffix.startswith(('lda_means','lda_covariance','lda_coefficients','pca_','efa_','cluster_')):return 5
        if suffix.startswith('example'):return 6
        if section['kind']=='visual':return 7
        if suffix=='summary' or suffix.startswith(('metric_','lda_decoding','lda_assumptions')):return 8
        if suffix in ('decisions','lda_oof_explanation','reproduction'):return 9
        if suffix=='limitations':return 10
        if suffix=='conclusion':return 11
        return 8
    out.sort(key=priority)
    # Split reports into readable sections without removing any text or table rows.
    import textwrap
    paginated=[]
    for section in out:
        if section['kind']!='content':paginated.append(section);continue
        from .mathematics import math_prose,METRICS
        paragraphs=[math_prose(p) for p in section.get('paragraphs',[])]
        metric_key=section['id'].removeprefix(rid+'_metric_')
        if metric_key in METRICS:section.update(formula=METRICS[metric_key],formula_text=metric_key+' (lihat notasi matematika)')
        if section['id'].endswith('_summary'):
            paragraphs=paragraphs+['Ringkasan ini dibaca bersama bagian prosedur, parameter, tabel lengkap, dan pembahasan setelahnya. Ukuran yang dihasilkan mengikuti tujuan metode: varians untuk PCA, kelayakan faktor untuk EFA, kemiripan untuk gerombol, serta kesalahan klasifikasi pada test untuk LDA. Nilai dari metode yang berbeda tidak mempunyai arti atau skala keberhasilan yang sama.']
        rows=section.get('rows',[]);budget=700 if rows else 1050 if section.get('formula') else 1200
        groups=[];current=[];length=0
        for paragraph in paragraphs:
            for part in textwrap.wrap(paragraph,width=budget,break_long_words=False,break_on_hyphens=False) or ['']:
                if current and length+len(part)>budget:groups.append(current);current=[];length=0
                current.append(part);length+=len(part)
        if current:groups.append(current)
        if not groups:groups=[[]]
        # Narrative before a table may take several pages. The table stays on the last narrative page.
        pieces=[dict(section,paragraphs=g,rows=[]) for g in groups[:-1]]
        chunks=[rows[i:i+4] for i in range(0,len(rows),4)] or [[]]
        pieces.extend(dict(section,paragraphs=groups[-1],rows=chunk) for chunk in chunks)
        for i,piece in enumerate(pieces):
            if i:piece.update(id=section['id']+f'__part_{i+1}',title=section['title']+f' · lanjutan {i+1}',formula=None,formula_text=None)
            paginated.append(piece)
    return clean(paginated)
