# Backend Multivariat Lab

Versi aktif memakai Python saja. PCA, LDA, k-means, dan hierarkis menggunakan NumPy/SciPy/scikit-learn; EFA menggunakan statsmodels0.15.0. Tidak memerlukan R, Rscript, psych, atau GPArotation.

## Mulai

Dari root proyek, jalankan `scripts/start-app.ps1` atau klik `Buka Multivariat Lab.cmd`. Launcher memeriksa server, menjalankan layanan lokal, dan membuka browser. Mode pemeriksaan tanpa membuka browser: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-app.ps1 -NoBrowser`. Server backend saja: `scripts/start-backend.ps1`.

Untuk instalasi ulang: Python3.13 dan Node.js diperlukan. Jalankan `scripts/setup-backend.ps1`, lalu `npm ci --prefix frontend`. Lock dependensi Python ada di requirements.lock.txt, frontend di package-lock.json. Aplikasi tidak memasang dependensi saat analisis berjalan. Grafik ekspor memerlukan Chrome/Edge lokal; launcher tidak mengunduh browser.

Data kerja berada di var/; sumber makalah outputs/makalah_multivariat/ tidak diubah. Hanya satu backend boleh memakai direktori runtime yang sama. Layanan di127.0.0.1:8000, frontend di127.0.0.1:5173. Ini aplikasi lokal satu pengguna, bukan layanan publik multiuser.

## Alur API

Alur utama frontend: `POST /projects/{id}/automatic-plan` dengan dataset_version_id, baca rencana beku, kemudian `POST /automatic-plans/{id}/start` dengan idempotency_key. Poll `/analysis-suites/{id}` dan ambil `/analysis-suites/{id}/presentation`. Snapshot menerima automatic_suite_id, run_ids, dan ordered_sections. Metode yang belum layak memiliki status explained dan bagian laporan tersendiri, tanpa run/model rekaan. Snapshot berisi penjelasan saja juga dapat diekspor ke PDF/JSON/CSV/XLSX. Kebijakan lengkap ada pada ../briefs/ANALISIS_OTOMATIS.md. Endpoint draft/prosedur di bawah dipertahankan untuk kompatibilitas dan penelusuran teknis; bukan alur yang perlu diatur pengguna.

OpenAPI aktual: contracts/openapi.json dan /docs. GET /api/v1/health mengembalikan session_token; browser mengirim X-Session-Token pada mutation. Token lokal bukan API key AI.

1. POST /projects, unggah CSV/XLSX ke /projects/{id}/imports, lalu /imports/{id}/confirm. Contoh makalah melalui /projects/{id}/case-study.
2. Mapping tipe dan role membuat versi dataset baru. Angka dan teks label dibedakan; identitas dengan leading zero dipertahankan sebagai teks. Workbook berformula ditolak: gunakan values-only.
3. POST /projects/{id}/drafts. Draft berisi dataset_version_id, method, feature_ids, purpose, preprocessing, settings, split, target_id/positive_label untuk LDA.
4. POST /drafts/{id}/validate atau validate-suite. Pemeriksaan data/model dapat menghasilkan blocking. Kelulusan awal bukan bukti semua asumsi terpenuhi; fitting memeriksa solusi numerik kembali.
5. POST /runs memakai draft_id, revision, idempotency_key; poll /runs/{id}. Worker terpisah mendukung cancel dan timeout300detik. Tidak menampilkan progress persen rekaan.
6. GET /runs/{id}/results, tables/{id}, visuals/{id}, observations/{row_id}, presentation. Semua memakai hasil versi run yang sama.
7. Snapshot membekukan bundles, ordered_sections, catatan dan grafik. Rujukan run/grafik divalidasi sebelum disimpan. Snapshot lama tidak berubah setelah pembaruan mesin atau laporan.
8. POST /exports, poll /jobs/{id}, unduh artifact.download_url. PDF mengikuti bagian dan urutan snapshot; JSON snapshot mempertahankan seluruh bundles, bagian dan notes. CSV snapshot default berisi metrik semua run dengan ID/metode; XLSX memuat seluruh tabel dan provenance setiap run. ZIP/PNG/SVG memerlukan satu run. Respons idempotency selalu memiliki job_id yang sama.

## Beberapa pertanyaan sekaligus

analysis_options berisi key metode dengan value preprocessing/settings/split. Dataset, fitur, dan target dipakai bersama; parameter tiap metode dibekukan sendiri. Contoh:

```json
{"analysis_options":{"pca":{"settings":{"basis":"correlation","target":0.8}},"efa":{"settings":{"extraction":"pa","rotation":"oblimin"}},"kmeans":{"preprocessing":{"scale":"standard"},"settings":{"k":3},"split":{"seed":42}}}}
```

POST /drafts/{id}/validate-suite mengembalikan hasil validasi per metode. POST /analysis-suites memakai RunInput; GET /analysis-suites/{id} mengembalikan status dinamis dan successful_run_ids. Riwayat melalui GET /projects/{id}/analysis-suites. Metode blocked tidak dijalankan; metode gagal tidak menerbitkan angka palsu atau membatalkan hasil lain. Pekerjaan dijalankan bergiliran untuk mengendalikan memori.

## Konvensi numerik

- LDA biner memakai pooled covariance W/(n−2), prior empirical/equal/custom, ambang0..1. Pengolahan dan pemilihan ambang OOF memakai train/foldtrain saja. Group/temporal split menjaga kendala masing-masing; gap temporal bukan test. Keanggotaan dan urutan split disimpan. Reproduksi OOF Taiwan mengembalikan urutan seed42 hanya sesudah membership cocok persis.
- PCA basis correlation/covariance dengan pemusatan, arah deterministik, PVE dan skor. PCA train memerlukan split.column_id dan settings.subset=train. Loading adalah korelasi indikator-komponen, berbeda dari arah.
- EFA principal axis (awalSMC) atau maximum likelihood, rotasi none/varimax/oblimin(quartimin). Pemeriksaan konvergensi, jumlah faktor, positive definiteness, keunikan positif dan invariansi kovarians rotasi dilakukan sebelum penerbitan hasil. Skor regresi = Z solve(R,L Phi). KMO dan Bartlett dihitung dari korelasi aktual. Tidak melakukan smoothing, clipping Heywood, atau imputasi tersembunyi.
- EFA otomatis: common-factor parallel analysis500simulasi, spektrum reduced correlation diagonalSMC, batas persentil95, retensi berurutan dari faktor pertama. NullGaussian memakai Wishart Bartlett dengan df=n−1, setara distribusi korelasi sampel dari n observasi independen tanpa mengurangi n. Ini kebijakan Python yang dicatat, bukan klaim identik dengan seluruh default psych. Jika tidak ada faktor yang didukung, hasil tidak dipaksakan. Jumlah manual tidak membuat grafik simulasi rekaan.
- K-means: k-means++,20inisialisasi, max300iterasi, seed tersimpan, Euclidean. Hierarkis: Ward/average/complete/single; Ward wajibEuclidean. Hierarkis full maksimal3000baris; tidak melakukan sampling diam-diam. Silhouette sampel deterministik maksimal2000dengan jumlah sampel dicatat. Nomor kelompok pengguna mulai1 dan bukan peringkat risiko.

## Visual dan laporan

Presentasi utama kini terpisah dari laporan teknis lengkap. POST /projects/{id}/presentation-plan menerima run_ids serta automatic_suite_id opsional, menyimpan deckplan dengan section core/appendix, lalu snapshot menyertakan presentation_plan_id. Server memeriksa kesesuaian proyek/run/suite serta mengambil konten ilmiah canonical dari rencana; paragraf browser tidak menjadi sumber angka. Hanya core dipilih awal. Contoh makalah: 18 slide utama dengan LDA/PCA; hasil EFA/gerombol dan dokumentasi rinci opsional. Endpoint /runs/{id}/presentation tetap menyediakan laporan lengkap. Demo aktif: ../contracts/curated-demo.json.

Manifest menentukan visual yang layak; frontend tidak memaksa kurva dua kelas pada subset satu kelas atau scatter2D pada fitur tunggal. Proyeksi PCA opsional mencantumkan varians dua sumbu serta jumlah titik tampilan. Profil kelompok dengan >8indikator atau >12kelompok menjadi opsional; laporan lengkap memakai tabel lanjutan. Loading faktor padat tidak dipaksakan menjadi satu slide. Seluruh indikator, matriks, dan koefisien tetap tersedia. Tidak ada batas jumlah halaman laporan.

Mode otomatis menentukan K dengan silhouette pada calon 2–6 yang memenuhi syarat dan sampel tetap maksimal 800 observasi; K-means dan Ward dinilai dengan algoritmenya sendiri. Hierarki otomatis di atas 1.000 baris memakai sampel tetap 1.000 observasi dengan ID/baris asal dan cakupan dicatat eksplisit. Jalur API manual tetap memiliki batas 3.000 untuk hierarki penuh. LDA melindungi test dari imputasi/pemilihan kolom train, mempertahankan split sumber makalah hanya jika hash sumber cocok, dan mempertimbangkan entitas/waktu yang dikenali. Data longitudinal gabungan atau makna label ambigu dijelaskan tanpa mengklaim evaluasi acak yang aman.

KaTeX dan font lokal digunakan pada layar. PDF merender notasi yang sama melalui Node.js dan Chrome/Edge/Chromium lokal; notasi blok serta notasi inline tidak dicetak sebagai kode LaTeX. Aset rumus disimpan dalam cache lokal. Instalasi ulang untuk PDF memerlukan dependensi frontend termasuk playwright-core, selain dependensi Python.

## Dokumen dan AI

DOCX/PDF teks diurai lokal, isinya sumber data dan bukan instruksi sistem. OCR tidak disediakan. Pencarian kutipan dan narasi deterministik tidak memerlukan AI. Provider opsional memakai AI_BASE_URL, AI_MODEL, AI_API_KEY dan persetujuan send_policy=summary_and_quotes; hanya memilih ID bukti terverifikasi. Dataset mentah tidak dikirim. Provider aktual memerlukan key pengguna dan belum divalidasi pada semua penyedia.

## Pengujian dan batas

Jalankan `backend/.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short`, build frontend, dan tes browser dengan server aktif. Tidak ada tes EFA yang dilewati karena R. Pengujian EFA memakai matriks faktor populasi yang diketahui, seluruh enam kombinasi ekstraksi/rotasi, skor/KMO/Bartlett independen, retensi dan seed, serta penolakan solusi tidak layak.

Laporan terbaru pada TEST_REPORT.md dan ../AUDIT_SISTEM.md. Tidak ada jaminan kesalahan nol untuk seluruh dataset. Asumsi model, kualitas/independensi data, validasi eksternal, dan perangkat fisik tetap memerlukan penilaian sesuai penggunaan. Kasus Taiwan adalah reproduksi parsial; tidak ada klaim eksekusi SPSS atau model premi/cadangan aktuaria operasional. Fitur di luar lingkup yang tidak disediakan: OCR, scoring eksternal model lama, esai AI bebas, editor slide canvas, dan deployment multiuser.
