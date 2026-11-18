# Audit sistem Multivariat Lab

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
