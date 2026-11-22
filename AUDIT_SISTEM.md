# Audit sistem Multivariat Lab

> **Status aktif — presentasi terkurasi, 22 November 2026:** **70 backend lulus, 0 dilewati; 10 browser lulus**. Contoh makalah memakai **18 slide utama dan PDF 18 halaman**. Dokumentasi teknis lengkap tersedia sebagai lampiran opsional. Prosedur tetap otomatis. Catatan 141 slide, pengaturan manual, dan R di bawah merupakan riwayat versi sebelumnya.

## Revisi bahasa dan pemilahan materi presentasi

Blok beranda “Baca data, pahami hasil, lalu presentasikan” dihapus. Keterangan halaman data, analisis otomatis, hasil, riwayat dan editor diubah menjadi deskripsi sumber, prosedur dan keluaran; kalimat yang menyebut kemampuan pengguna atau menjanjikan “tinggal baca/tidak perlu mengatur” dihapus dari jalur utama. Tombol tetap menyatakan aksi.

Presentasi sekarang disusun oleh backend/presentation_plan.py, terpisah dari laporan teknis lengkap. Untuk sumber makalah yang hash-nya cocok, pembahasan empiris utama adalah LDA dengan ilustrasi PCA. Materi inti tetap mencakup konsep empat metode, formulasi matematika, sumber/indikator/komposisi data, pengolahan dan split, logika LDA, confusion matrix, metrik beserta baseline, PR dan ROC-AUC/AP, OOF/prior, diagnostik, status reproduksi, PCA, relevansi aktuaria, keterbatasan dan kesimpulan. Metrik dan prosedur yang berkaitan digabung, data bersama tidak diulang per metode. Hasil EFA/K-means/hierarkis serta matriks/koefisien/perhitungan lengkap tidak tercentang secara default. Dataset mandiri tidak menerima klaim Taiwan hanya karena nama tujuan mengandung “makalah”.

Rencana presentasi beku memiliki ID, versi kebijakan, sumber run, klasifikasi core/appendix dan pilihan awal. Snapshot memvalidasi rencana terhadap proyek, suite dan run yang sama; paragraf/angka dari browser tidak mengganti konten ilmiah canonical. Penyuntingan judul, urutan, catatan dan pemilihan slide tetap tersedia. Snapshot lama tidak ditulis ulang. Mesin numerik dan hasil statistik tidak diubah oleh pemilahan.

Bukti: 70 tes backend lulus (99,09 detik); 12 tes terarah untuk rencana/otomatisasi juga lulus setelah penyesuaian terakhir. Tes baru membuktikan pemilahan makalah, retensi angka utama dan asumsi, lampiran awal nonaktif, integritas snapshot, kepemilikan, ketiadaan klaim sumber pada data umum, dan ketersediaan laporan lengkap. Tes browser mencakup alur pemilihan materi inti 24 slide pada data sintetis lima metode serta presentasi keterangan kelayakan. Contoh makalah asli menghasilkan 18 slide; seluruhnya diukur pada 1366×768 tanpa overflow atau browser error. Editor diperiksa desktop/mobile. PDF aktual 18 halaman dirender dan ditinjau, termasuk rumus, matriks klasifikasi, metrik, PR, dan kesimpulan. Detector satu kali menghasilkan []; build strict TypeScript/Vite berhasil. Bukti baru pada contracts/curated-demo.json, tmp/curated-audit/ dan frontend/test-results/.

Jumlah 18 adalah hasil pemilahan contoh ini, bukan batas paksa untuk seluruh dataset. Materi inti dapat berbeda mengikuti jumlah sumber, metode yang relevan, dan kelayakan visual. Batas validasi eksternal serta cakupan pengujian pada bagian sebelumnya tetap berlaku.

## Penyederhanaan alur analisis

Pengguna cukup membuka data, melanjutkan bacaan rencana, dan menekan Analisis otomatis. Kontrol fitur, K/q, prior, seed, rotasi, missing dan split tidak muncul pada jalur utama. Hasil utama menampilkan temuan singkat dari run, alasan keputusan tersedia dalam rincian, dan riwayat menonjolkan laporan otomatis. Rencana beku memiliki hash serta versi kebijakan; pengguna tidak perlu menyusun konfigurasi sendiri. API manual tetap ada untuk kompatibilitas/penelusuran.

Kelayakan ditelaah untuk seluruh lima pertanyaan. Metode yang layak dihitung; yang belum didukung data menghasilkan penjelasan ilmiah, tanpa model atau metrik rekaan. Dataset tanpa indikator tetap dapat menghasilkan presentasi penjelasan serta PDF/JSON/CSV/XLSX. Ini tidak berarti semua dataset dapat menghasilkan semua model.

## Audit ketepatan prosedur dan hasil

Identitas/label/waktu/pembagian/konstanta/teks dipisahkan dari indikator. PCA memakai korelasi dan target 80%. EFA menguji retensi serta kelayakan numerik; rekomendasi simulasi dan q aktual dibedakan. K dipilih dari silhouette K-means atau Ward sesuai metode pada sampel tetap maksimal 800. Hierarki di atas 1.000 memakai sampel tetap 1.000, dengan cakupan/ID asal dicatat di hasil dan laporan; tidak diklaim sebagai pohon seluruh data.

LDA mengimputasi dan memilih kolom independen dari train. OOF diperiksa dengan estimasi nyata dan tidak dipaksakan jika fold tidak layak. Entitas/waktu yang dikenali memengaruhi split; tahun numerik dibaca sebagai tahun, bukan nanodetik epoch. Rancangan gabungan yang belum aman dan label ambigu dijelaskan tanpa menebak. Status reproduksi makalah kini bergantung pada hash sumber, sehingga dataset baru dalam proyek contoh tidak otomatis mewarisi split/pembanding makalah.

68 tes backend lulus dalam 104,48 detik, termasuk pengujian baru atas lima metode otomatis, missing/duplikat/konstanta, label ambigu, sumber makalah, sampling, entitas/waktu/tanggal, snapshot penjelasan saja, kepemilikan, idempotency dan ekspor. Referensi Taiwan tetap TN/FP/FN/TP = 1973/7/54/12; ROC-AUC 0,903749617385981 dan AP 0,30852372633028535. Satu warning Starlette TestClient tercatat, tanpa kegagalan tes. Keluaran aktual: backend/test-output.txt.

## Audit presentasi, rumus dan tampilan

Isi slide dipilih per kelompok penjelasan; rincian halaman, urutan, judul dan catatan bersifat opsional. KaTeX lokal merender notasi blok dan inline. PDF menggunakan notasi yang sama melalui aset KaTeX, bukan kode LaTeX yang dicetak sebagai paragraf. Snapshot tetap membekukan konten canonical dan menolak campuran run/suite/proyek yang tidak sesuai.

10 tes browser lulus dalam sekitar 2,1 menit dengan API/worker nyata. Alur utama diuji tanpa mengisi pengaturan statistik. Laporan sintetis 143 bagian diperiksa seluruhnya pada 1366×768 setelah font/notasi siap; tidak ada overflow dokumen atau katex-error. Axe pada alur otomatis dan hasil rinci tidak menemukan pelanggaran dalam cakupan tes. Build TypeScript/Vite berhasil; detector frontend dijalankan sekali, exit 0 tanpa keluaran temuan. Chunk Plotly tetap besar dan dimuat terpisah.

Contoh makalah asli baru: lima run sukses, snapshot 141 bagian dan PDF 141 halaman. Seluruh halaman dirender dalam lembar kontak; 11 halaman, termasuk rumus klasifikasi, sensitivitas, contoh observasi, retensi EFA dan cakupan hierarki, dirender lebih besar dan sampel ditinjau langsung. Bukti: contracts/automatic-demo.json, frontend/test-results/, tmp/automatic-audit/pdf-check.json dan PNG/PDF di folder tersebut. Jumlah halaman dapat berbeda pada data lain. EFA/gerombol tetap eksplorasi tambahan terhadap empiris utama makalah.

Batas: pengujian bukan jaminan kesalahan nol pada seluruh dataset. Makna kolom yang ambigu tidak ditebak, asumsi statistik tidak menjadi terjamin hanya karena pengaturan otomatis, dan semua model tidak selalu layak. Validasi eksternal, provider AI aktual, OCR, perangkat proyektor fisik, pembaca layar penuh serta deployment multiuser tidak diklaim diuji. Panduan kebijakan: briefs/ANALISIS_OTOMATIS.md. Bagian berikut mempertahankan riwayat audit terdahulu.

## Revisi kesiapan tampil: Python saja

Ketergantungan R dihapus dari kode aktif, health/capabilities, setup, dan tes. EFA tetap merupakan analisis faktor, bukan penggantian dengan PCA. Principal axis dan maximum likelihood memakai statsmodels 0.15.0 dengan rotasi none/varimax/oblimin (quartimin). backend/efa.R dihapus. Snapshot dan hasil lama tetap dibekukan.

### Temuan yang diselesaikan

| Temuan | Penyelesaian |
|---|---|
| EFA tergantung program R yang hilang | Implementasi Python, lock dependensi stabil, tanpa R atau tes yang dilewati. |
| PA library tidak menyatakan konvergensi secara eksplisit | Fixed point komunalitas diperiksa kembali. ML memeriksa success optimizer. |
| Tanda/urutan loading dapat tidak konsisten dengan Phi dan skor | Perubahan dilakukan serentak, disertai uji invariansi kovarians rotasi. |
| Rekomendasi faktor dapat tidak teridentifikasi | Preflight memeriksa q, derajat bebas, korelasi, serta kelayakan indikator sebelum job. Tidak memotong q diam-diam. |
| P-value Bartlett amat kecil tampil sebagai0 | Laporan menyatakan batas <1e-300 dan menjelaskan underflow bukan peluang nol; raw baru menyimpan status. |
| JSON snapshot gabungan kehilangan bagian, notes, dan identitas metode | Mempertahankan snapshot lengkap dengan seluruh bundles dan provenance. |
| CSV/XLSX snapshot tidak menjelaskan semua sumber | CSV default memuat metrik semua run; XLSX memuat provenance semua run, table_manifest, row_index untuk array, dan part untuk metadata panjang. |
| Respons ekspor idempotent berubah bentuk | Selalu mengembalikan job_id yang sama. |
| Snapshot menerima referensi grafik yang tidak tersedia/run berulang | Referensi dan keunikan run diperiksa sebelum penyimpanan. |
| Grafik padat dipaksakan ke slide | Profil >8indikator atau >12kelompok menjadi opsional; loading padat dibaca melalui tabel terpaginasikan yang tetap lengkap. |
| Metadata nama/satuan dapat merusak render | API memeriksa tipe teks, kekosongan, dan panjang maksimal500karakter. |
| Pembukaan aplikasi membutuhkan dua terminal | Buka Multivariat Lab.cmd menjalankan launcher dengan pemeriksaan health dan proses aplikasi, tanpa bergantung pada status port Windows yang sementara. |

### Pembuktian numerik dan alur

Enam kombinasi EFA (pa/ml × none/varimax/oblimin) diuji pada sampel yang korelasinya sama dengan matriks populasi faktor yang diketahui: dua faktor berkorelasi0,3 dan enam indikator. Kovarians bersama cocok dalam3e-6. Structure, komunalitas, uniqueness, residual, skor regresi, KMO, serta Bartlett dibandingkan dengan perhitungan matriks terpisah pada toleransi1e-10 atau lebih ketat.

Parallel analysis memakai reduced correlation diagonalSMC,500nullGaussian, persentil95, dan retensi berurutan. Bartlett Wishart df=n−1 menghasilkan distribusi korelasi sampel tanpa mengurangi jumlah observasi. Boundary dibandingkan langsung dengan kuantil seluruh simulasi; seed sama cocok eksak dan seed berbeda mengubah hasil. Ini konvensi Python yang tercatat, bukan klaim identik dengan semua default psych. Solusi singular, indikator konstan, n≤p, q tidak sah/tidak teridentifikasi, Heywood dan konvergensi gagal tidak dipaksakan menjadi hasil.

Regresi Taiwan utama/OOF/prior sama, PCA/SVD, kebocoran train/test, split group/temporal, dan pusat/linkage cluster tetap lulus. JSON/CSV/XLSX snapshot lintas dua run diuji bersama notes, urutan, provenance, dan idempotency. Metode yang tidak memenuhi syarat ditolak dengan alasan; tidak menghapus hasil metode lain.

### Hasil akhir

- **58 passed, 0 skipped**, satu warning deprecation Starlette TestClient; output pada backend/test-output.txt.
- **9 browser tests passed**, Chrome Windows, API/worker nyata. Tes pilih semua menuntut kelima metode berhasil, tanpa pengecualian EFA.
- Laporan gabungan132bagian diperiksa pada1366×768 tanpa luapan; tampilan mobile serta aksesibilitas pada cakupan tes turut diperiksa.
- PDF aktual132halaman cocok jumlah/urutannya dengan snapshot. Semua halaman dirender; thumbnail keseluruhan dan halaman tertentu dibaca pada resolusi penuh. Snapshot/PDF diperbarui setelah koreksi p-value.
- Build TypeScript/Vite dan pip check berhasil; Impeccable detector mengembalikan[]. Plotly tetap dimuat terpisah dengan chunk sekitar1,13MB.
- Launcher diuji dari server berhenti dan saat server sudah hidup. Proses latar tersembunyi, log pada var/launcher/. Situs aktif di127.0.0.1:5173.

Bukti: backend/tests/test_python_factors.py, frontend/test-results/, dan tmp/readiness-audit/. Demo lengkap terbaru tercatat di contracts/ready-demo.json dan diberi label **data simulasi, bukan Taiwan**. Kasus makalah Taiwan tetap tersedia terpisah pada contracts/multi-analysis-demo.json.

Tidak ditemukan kegagalan tersisa pada cakupan pengujian tersebut. Ini bukan jaminan kesalahan nol untuk semua dataset/perangkat. Uji beban maksimum100k×200, seluruh browser/pembaca layar/proyektor fisik, dan provider AI pengguna yang belum dikonfigurasi belum tercakup sepenuhnya. Fungsi inti analisis/presentasi tidak membutuhkan AI. Penolakan data tidak layak bukan fitur rusak; memilih semua metode tidak membenarkan pemaksaan semua model. Kasus Taiwan tetap reproduksi parsial dan belum memvalidasi penggunaan finansial/aktuaria operasional.

Acuan pustaka: [statsmodels Factor](https://www.statsmodels.org/stable/generated/statsmodels.multivariate.factor.Factor.html), [rotasi](https://www.statsmodels.org/stable/generated/statsmodels.multivariate.factor.FactorResults.rotate.html), [skor regresi](https://www.statsmodels.org/stable/generated/statsmodels.multivariate.factor.FactorResults.factor_scoring.html). Bukti keluaran lokal berasal dari pengujian independen di atas.

## Riwayat audit sebelumnya

Tanggal: 5 November 2026. Lingkungan: Windows, Python 3.13, R 4.6.1, Chromium Playwright, React 19 / Vite 6. Audit mencakup kode, perhitungan ulang, API nyata, grafik browser, snapshot, dan berkas ekspor.

## Keputusan

Alur yang diuji dapat digunakan untuk pembelajaran dan presentasi contoh makalah setelah perbaikan di bawah. Tidak ditemukan kegagalan tersisa pada pengujian terakhir. Pernyataan ini bukan sertifikasi bebas kesalahan untuk semua dataset, semua perangkat, atau penggunaan keuangan operasional.

Audit menemukan kesalahan nyata walaupun pengujian sebelumnya sudah lulus. Karena itu pemeriksaan diperluas hingga kesamaan nilai sumber → hasil numerik → koordinat grafik → tabel alternatif → materi presentasi → PDF, bukan hanya keberhasilan membuka halaman.

## Acuan dan integritas sumber

- Workbook pada Downloads identik secara SHA256 dengan salinan pada `outputs/makalah_multivariat/`.
- Makalah DOCX Downloads dan salinan workspace berbeda satu paragraf catatan editorial setelah bagian awal. Perbandingan teks seluruh paragraf memastikan tidak ada perubahan isi statistik. Berkas asli tidak diubah.
- Isi dokumen diperlakukan sebagai bahan kajian; instruksi di dalamnya tidak menjadi instruksi untuk agent.
- Empiris utama makalah adalah LDA biner Taiwan. PCA merupakan ilustrasi tersendiri pada train. EFA dan clustering adalah dukungan tema serta eksplorasi tambahan, bukan hasil empiris yang direka sebagai bagian makalah.

## Temuan dan perbaikan

| Tingkat | Temuan | Perbaikan dan bukti |
|---|---|---|
| Tinggi | PCA memakai `scattergl`, sedangkan paket Plotly basic browser tidak menyediakan trace itu; grafik bisa tanpa titik walaupun angka benar. | Trace SVG `scatter`; kompatibilitas snapshot lama ditangani. Browser memeriksa titik benar-benar muncul dan array x/y persis sama dengan API skor PCA. |
| Tinggi | Nama seperti Likuiditas/Liquidity mengandung substring `id`, sehingga dapat dianggap identitas dan gagal menjadi fitur numerik. | Pengenalan token identitas dengan batas kata. Regresi memeriksa kedua fitur tetap angka, sedangkan ID/company_id tetap teks dan leading zero bertahan. |
| Tinggi | Garis simulasi EFA memakai mean, sedangkan keputusan retensi memakai persentil 95. Grafik dapat menyampaikan keputusan berbeda dari algoritme. | Hitung persentil 95 dari 500 simulasi common-factor yang sama; mean disimpan terpisah. R nyata membuktikan garis batas dan rekomendasi dua faktor sejalan. |
| Tinggi | Presentasi hanya ringkasan dan grafik; konteks, prosedur, rumus, contoh hitung, evaluasi, dan batas belum menjadi cerita lengkap. | Bagian berasal dari satu run tersimpan. LDA memuat data, indikator, train/test, prior, rumus, contoh TW03598, baseline, kesalahan, skenario, reproduksi parsial, dan batas. Gabungan LDA/PCA terdiri dari 17 bagian; editor menambah pengantar metode. |
| Tinggi | PDF tidak mengikuti seluruh urutan dan isi bagian yang dipilih pada snapshot. | PDF membaca bagian snapshot sesuai urutan; tes membalik dua bagian dan memeriksa teks serta halaman hasilnya. Rumus PDF mengikuti metode, termasuk uji PCA tidak mendapat rumus klasifikasi. |
| Sedang | Grafik PR digambar linear, sehingga pembaca dapat mengira AP adalah luas trapezoid. | Garis bertangga dengan koordinat asli; integral langkah cocok AP dalam 1e-12. Penjelasan menyatakan average precision. |
| Sedang | Nomor kelompok tabel/membership berawal 0, sedangkan grafik berawal 1. | Semua keluaran yang dibaca pengguna pada run baru memakai 1..K. Label internal mentah tetap 0..K−1. Tes memeriksa pemetaan seluruh anggota dan pusat. |
| Sedang | Formula hierarkis memakai formula k-means untuk semua linkage. | Ward, average, complete, single memiliki formula masing-masing. Keterangan dendrogram menjelaskan daun terpotong dan jumlah anggota cabang. |
| Sedang | Orientasi confusion matrix ekspor berpotensi membalik baris visual. | Aktual menjadi baris, prediksi menjadi kolom, negatif di atas. Nilai eksak diperiksa pada trace. Persentase per baris nol tidak ditampilkan sebagai statistik palsu. |
| Sedang | Tabel alternatif kurva dan dendrogram menyimpan array panjang di satu sel. | Baris koordinat/threshold, pasangan aktual-prediksi, pusat per indikator, langkah penggabungan, loading per faktor, dan batas parallel analysis dapat dibaca dan dipaginasi. |
| Sedang | Heatmap pattern oblique dibatasi ±1 padahal koefisien pattern dapat melampaui 1. | Rentang warna simetris mengikuti nilai maksimum aktual; angka tidak dipotong. Tes koefisien 1,2 memeriksa rentang ekspor. |
| Sedang | Materi membatasi tabel indikator/contoh ke delapan pertama tanpa kelanjutan. | Dipecah menjadi bagian maksimal delapan indikator. Tidak ada indikator hilang; tes memakai 12 indikator. Jumlah η tetap memakai seluruh kontribusi. |
| Sedang | OOF estimator eksperimen SVD tidak meneruskan prior yang dipilih. | Prior empirical/equal/custom diteruskan secara konsisten. Jalur makalah tetap pooled covariance eksplisit. |
| Sedang | Shapiro dapat memberikan angka menyesatkan untuk kelompok konstan atau terlalu kecil. | Status unavailable dengan alasan dan nilai null. Nilai p untuk n>5000 juga tetap diberi keterbatasan. |
| Sedang | Pembungkus grafik berperan sebagai gambar tetapi berisi tombol legenda interaktif; resize sempat meluapkan halaman. | Semantik group, skip navigation, label yang terkait kontrol, dan penanganan lebar grafik. Axe dan matriks ukuran browser dikonfirmasi ulang. |
| Sedang | Observasi non-LDA hanya memperlihatkan sumber walaupun halaman menjanjikan hasil per observasi. | PCA/EFA menampilkan skor tersimpan; clustering menampilkan keanggotaan yang konsisten dengan tabel. Browser memeriksa modal dan kesamaan nilainya. |
| Rendah | Metadata visual kurang menjelaskan nama indikator, skala, serta arti kelas positif. | Nama tampilan, label target/positif/negatif, skala olahan, bagian varians PCA dan batas interpretasi ditampilkan sesuai run. Inertia/iterasi/sample silhouette dan KMO rendah tersedia sebagai diagnostik. |

## Verifikasi numerik

Data Taiwan: 6.819 rekaman, lima fitur, train 4.773, test 2.046 dengan 66 positif. Pooled covariance menggunakan W/(n−2). Tidak mengganti angka keluaran dengan konstanta referensi.

| Pemeriksaan | Hasil aktual |
|---|---|
| Confusion matrix utama TN / FP / FN / TP | 1973 / 7 / 54 / 12 |
| Sensitivity utama | 12/66 = 18,1818% |
| Precision utama | 12/19 = 63,1579% |
| ROC-AUC | 0,903749617385981 |
| Average precision | 0,30852372633028535 |
| Ambang OOF train | 0,12413099063180978 |
| Test dengan ambang OOF: TN / FP / FN / TP | 1921 / 59 / 38 / 28 |
| Test dengan prior sama: TN / FP / FN / TP | 1747 / 233 / 20 / 46 |
| TW03598 posterior positif | 0,9934229406644826 |
| Eigenvalue PCA train | 1,96833010; 1,28136996; 0,99317763; 0,46554536; 0,29157695 |
| Varians dua / tiga komponen | sekitar 64,994% / 84,858% |

Perhitungan pembanding menghitung mean, kovarians dan inverse dari observasi sumber secara terpisah lalu memeriksa posterior beberapa baris. Pengujian lain memeriksa rekonstruksi PCA, ortonormalitas arah, invariansi affine LDA, dan perubahan test ekstrem yang tidak mengubah parameter train/ambang OOF. Toleransi utama 1e-10 untuk posterior/metrik, 1e-7 untuk eigenvalue referensi yang dibulatkan. Kesamaan titik grafik memakai array hasil aktual, bukan toleransi screenshot.

Urutan OOF sangat penting: membership saja tidak menentukan fold. Reproduksi urutan seed42 dilakukan hanya setelah membership asli cocok. Tidak ada klaim solver SVD atau SPSS telah mereproduksi implementasi pooled tersebut.

## Pemilihan visual sesuai kebutuhan

| Metode/kondisi | Keluaran |
|---|---|
| LDA test berisi dua kelas | Confusion matrix dan PR utama; ROC opsional. |
| LDA test satu kelas | Kurva dua kelas tidak dibuat; metrik tidak terdefinisi memiliki nilai null. |
| PCA | Scree utama; proyeksi PC1/PC2 opsional hanya bila rank minimal dua. Varians dua sumbu dan jumlah titik sampling disebutkan. |
| EFA manual | Loading/pattern; tidak mengarang grafik parallel analysis yang tidak dijalankan. |
| EFA otomatis | Loading dan perbandingan common-factor dengan batas simulasi 95%. |
| K-means | Pusat indikator per kelompok; tidak menambah scatter dua dimensi palsu untuk fitur tunggal. |
| Hierarkis | Profil pusat dan dendrogram linkage aktual; pemotongan ke 30 daun disebutkan. |

Diagram faktor, biplot, elbow, seed sensitivity dan histogram tidak otomatis disajikan sebagai hasil yang sudah dihitung. Sistem belum menyediakan semua visual dalam brief. Ini batas lingkup yang tercatat, bukan menu hasil kosong.

## Pemeriksaan antarmuka dan materi

- Browser memakai API serta proses statistik Python/R nyata, tanpa mock hasil.
- Layout hasil diuji pada lebar 320, 390, 768, 1024, 1366, 1440, 1920. Tidak ada luapan horizontal dokumen setelah layout stabil; tabel dua dimensi mempunyai scroll lokal yang disengaja.
- Tujuh belas bagian hasil gabungan LDA/PCA diperiksa satu per satu pada 1366×768; tinggi dan lebar dokumen sesuai viewport. Tabel contoh, rumus, keputusan, variabel dan scree mempunyai screenshot bukti.
- Pemeriksaan visual langsung mencakup PCA, EFA, profil kelompok, dendrogram, matriks, versi mobile, dan materi presentasi. Posisi sidebar/skip link juga diperiksa pada scroll 0 dan 500; kejanggalan tangkapan full-page saat scrolled bukan posisi di viewport pengguna.
- PDF LDA aktual dari endpoint ekspor dirender menjadi 11 halaman gambar. Urutan cerita, rumus, angka TW03598, confusion matrix, PR, dan tabel skenario diperiksa langsung; tidak terlihat teks tumpang tindih atau terpotong pada sampel ini.
- Axe: nol pelanggaran pada cakupan halaman yang diuji, tag WCAG2A/AA dan WCAG2.1AA. Rule region dikecualikan untuk struktur pustaka grafik; ini bukan sertifikasi seluruh WCAG. Grafik juga memiliki alternatif angka.
- Impeccable detector terakhir: `[]`. Build strict TypeScript dan Vite berhasil. Plotly dan KaTeX dimuat terpisah; ukuran chunk Plotly masih besar (sekitar 1,13 MB, 378 kB gzip).

## Pengujian terakhir

| Pengujian | Hasil |
|---|---|
| Seluruh backend | **40 passed**, satu warning deprecation Starlette TestClient; 44,19 detik |
| Browser end-to-end | **8 passed**, sekitar 1,3 menit |
| Build frontend | Berhasil |
| Kontrak OpenAPI dan tipe TypeScript | Diterbitkan ulang sesuai endpoint aktual |
| PDF nyata | Berhasil diunduh dan dirender, 11 halaman |

Bukti: `backend/test-output.txt`, `frontend/test-results/report.json`, `frontend/test-results/system-audit/`, dan `tmp/system-audit/`. Pengujian asli juga memeriksa unggah, mapping, wizard, job/cancel/idempotency, split group/temporal, sumber berbahaya, validasi bukti AI, tujuh format ekspor, dan fallback snapshot browser. Paket reproduksi pernah diuji ulang dengan verifikasi checksum; audit ini menambah pemeriksaan integritas visual dan materi.

## Batas dan risiko tersisa

1. Kesesuaian numerik contoh bukan validasi eksternal. Kesamaan kovarians ditentang Box M; posterior belum terbukti terkalibrasi. Identitas perusahaan unik/waktu dan split penelitian sumber belum cukup untuk klaim validasi temporal atau antarperusahaan. Reproduksi tetap parsial.
2. Bukan sistem penetapan premi, cadangan, modal asuransi, atau keputusan investasi otomatis. Tidak menjanjikan akurasi tanpa kesalahan pada semua data.
3. Dataset yang sangat lebar, label sangat panjang, atau ratusan seri memerlukan pemilihan variabel dan pemeriksaan keterbacaan tersendiri. Pemecahan tabel indikator tidak menjamin semua grafik padat akan nyaman dibaca. Batas unggah bukan benchmark kinerja; uji beban/memori menyeluruh belum dilakukan.
4. Diuji pada Chromium Windows. Belum ada uji menyeluruh dengan pembaca layar, semua jenis gangguan penglihatan, Safari/Firefox, atau proyektor fisik. Kemampuan dibaca oleh siapa pun tidak dapat disimpulkan hanya dari tes otomatis.
5. Provider AI aktual belum diuji dengan API key pengguna. Jalur lokal deterministik tetap tersedia. OCR, esai AI bebas, scoring eksternal model lama, dan editor slide canvas belum disediakan.
6. Aplikasi ditujukan untuk satu pengguna secara lokal. Belum melalui penetration test, fuzzing luas, validasi multiuser, atau hardening layanan publik. Jangan menganggap token localhost sebagai autentikasi layanan internet.
7. Snapshot dan run lama sengaja tidak ditulis ulang. Untuk menerima materi baru dan penomoran kelompok baru, jalankan analisis ulang bila perlu, kemudian buat snapshot baru. PDF mengikuti isi bagian dan urutan; bukan salinan piksel slide, dan catatan pembicara tidak dicetak sebagai materi audiens.

Tidak ada temuan tinggi/sedang dari daftar perbaikan yang sengaja dibiarkan tanpa penyelesaian. Batas di atas tetap harus dibaca sebagai batas bukti, bukan dianggap telah lolos pengujian yang belum dilakukan.


## Pembaruan 22 November 2026: pilihan jamak dan laporan lengkap

Permintaan pengguna mengubah pemilihan satu tujuan menjadi beberapa tujuan sekaligus dan mengganti presentasi ringkas dengan laporan yang bisa dibaca langsung.

### Perubahan alur

- Pilihan checkbox untuk PCA, EFA, k-means, hierarkis, dan LDA; tombol pilih semua metode yang tersedia. Identitas, target, dan kolom split tetap dilindungi dari pemilihan sebagai prediktor.
- Fitur sumber dipilih bersama. Pengolahan, parameter, dan split disimpan per metode; berpindah tab pengaturan tidak menghilangkan parameter metode lain.
- API suite membekukan konfigurasi anak, memeriksa tiap metode, dan mengantrekan pekerjaan terpisah. Metode tidak saling memakai output. Status blocked/failed/cancelled tidak berubah menjadi angka hasil; metode lain tetap dapat selesai.
- Suite memiliki idempotency, pemeriksaan revisi, riwayat proyek, pembatalan per metode, dan tautan menyusun laporan seluruh hasil yang selesai. Tidak melakukan subsampling diam-diam untuk meloloskan batas hierarkis 3.000 baris.

### Isi laporan

Laporan deterministik memuat pertanyaan, ruang lingkup, data eligible, parameter pengolahan aktual, deskripsi sebelum pengolahan, prosedur dan rumus, tabel pembentuk hasil, contoh observasi, interpretasi, diagnostik, batas, dan kesimpulan. LDA menambah mean kelas, seluruh matriks pooled, koefisien, penguraian TN/FP/FN/TP, satu pembahasan per metrik beserta baseline, dan logika OOF/prior. PCA memuat spektrum lengkap, aturan retensi, arah dan korelasi loading komponen terpilih, serta skor contoh. Gerombol memuat ukuran dan profil setiap kelompok, inertia/iterasi atau aturan hierarki, dan makna silhouette. EFA memiliki pembahasan KMO/Bartlett, pattern/structure/komunalitas/keunikan, Phi, residual, serta pemilihan faktor; perhitungan R baru tetap memerlukan runtime yang tersedia.

Tidak ada batas jumlah slide. Paragraf dan tabel dipaginasi dengan mempertahankan seluruh teks, seluruh indikator, dan presisi nilai sumber; angka tampilan dibulatkan. Snapshot menyimpan konten lengkap dan PDF mengikuti konten serta urutan yang sama. Snapshot lama tidak diubah; buat snapshot baru untuk materi yang diperluas.

### Bukti terbaru

- Backend: 44 passed, 3 skipped (R), satu warning Starlette TestClient. Rincian mesin pada backend/test-output.txt.
- Browser: 9 passed, Chrome Windows melalui Playwright, API dan pekerja statistik nyata. Rute EFA tidak dijalankan dalam tes browser karena capability menunjukkan runtime tidak tersedia.
- Pemilihan semua metode yang tersedia menghasilkan empat analisis nyata pada CSV sintetis 140 observasi. Pengaturan k-means K=2 tetap tersimpan setelah berpindah ke PCA; penskalaan default kedua metode tetap berbeda.
- Laporan gabungan uji berisi 86 halaman; semua halaman diperiksa pada1366×768 tanpa luapan dokumen. Screenshot tujuan, status, dan contoh pembahasan diperiksa langsung. Axe pada status suite tanpa pelanggaran.
- PDF aktual 86 halaman cocok jumlah dan urutannya dengan 86 bagian snapshot. Sampel 12 halaman dirender dan ditinjau, termasuk tabel, grafik, metrik, serta kesimpulan. Bukti pada tmp/multi-report-audit/ dan frontend/test-results/multi-report/.
- Contoh Taiwan diperbarui menjadi 90 halaman dari tiga run nyata: LDA, PCA train, serta k-means sebagai eksplorasi tambahan. Identitas snapshot dan tautan lokal ada pada contracts/multi-analysis-demo.json.
- Pengujian baru membandingkan PCA dengan SVD independen, linkage/pusat hierarkis dengan hasil pohon, mempertahankan seluruh eigenvalue pada laporan 13 fitur, dan membuktikan empat metode sukses walaupun metode kelima diblokir. Nilai Taiwan utama/OOF/prior sama tetap lulus tes referensi.
- Pemeriksaan tambahan menemukan seed EFA sebelumnya tetap42 meskipun pengguna mengubah seed. Konfigurasi R sekarang meneruskan seed per metode; rentang seed serta K/linkage/metric diperiksa sebelum run. Pencarian R mendukung R_SCRIPT dan lokasi pemasangan Windows selain PATH.
- Build strict TypeScript/Vite berhasil; Impeccable detector: []. Chunk Plotly tetap besar dan dimuat terpisah.

### Batas lingkungan yang belum terselesaikan

Runtime Rscript.exe tidak ditemukan pada host saat audit ini, walaupun folder library R masih ada. Tiga pengujian yang membutuhkan eksekusi R nyata dicatat sebagai skipped, bukan lulus. Percobaan pemasangan R4.6.1 dari CRAN ditolak oleh pemeriksaan persetujuan otomatis dengan alasan blocked by policy; tidak digunakan cara lain untuk mengakali penolakan tersebut. EFA tetap dinonaktifkan dan server menolak penerbitan hasil EFA tanpa runtime valid. Pengguna perlu memasang kembali R dan paket psych/GPArotation/jsonlite, lalu menjalankan ulang backend serta tiga tes tersebut. Jika lokasi khusus, atur R_SCRIPT ke Rscript.exe. Audit tidak mengklaim seluruh lima metode baru telah diuji secara langsung pada lingkungan saat ini.

Batas validasi eksternal, asumsi data, perangkat/proyektor fisik, pembaca layar penuh, dan provider AI pada laporan awal tetap berlaku. Laporan panjang memperjelas bukti dan keterbatasan; tidak mengubah analisis eksploratori menjadi validasi keuangan operasional.
