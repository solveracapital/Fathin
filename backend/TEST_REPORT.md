# Laporan pengujian backend

## Status terbaru: rencana presentasi terkurasi

**70 passed, 0 skipped**, 99,09 detik, satu warning deprecation Starlette TestClient. Dua tes baru memverifikasi pemilahan presentasi makalah, angka utama, retensi asumsi/batas, pemisahan eksplorasi, laporan teknis tetap tersedia, penolakan run/proyek yang tidak sesuai, dan perlindungan konten canonical terhadap paragraf browser. Dataset mandiri dengan tujuan bernama makalah tidak menerima klaim Taiwan. Setelah penyesuaian keterangan/metadata akhir, **12 tes terarah** untuk presentation_plan dan automatic juga lulus (39,07 detik). Mesin statistik tidak berubah. Ekspor contoh aktual 18 halaman diuji melalui API dan dirender pada tmp/curated-audit/. Bagian berikut adalah riwayat revisi sebelumnya.

## Status terbaru: analisis otomatis, 22 November 2026

**68 passed, 0 skipped**, satu warning deprecation Starlette TestClient; durasi 104,48 detik. Tambahan pengujian: rencana otomatis lima metode tanpa konfigurasi pengguna, kecocokan sumber makalah, missing/kolom duplikat/konstanta, label tidak dikenal atau ambigu, penjelasan tanpa model beserta ekspor PDF/JSON/CSV/XLSX, idempotency/kepemilikan, cakupan sampel hierarki, pembagian entitas/waktu, tahun/tanggal numerik dan markup matematika. Nilai referensi Taiwan utama/OOF tetap lulus. Command dan keluaran aktual ada di test-output.txt. Catatan setelah bagian ini merupakan riwayat versi sebelumnya.

## Status terbaru: revisi kesiapan tampil, 22 November 2026

**58 passed, 0 skipped**, satu warning deprecation Starlette TestClient; seluruh58tes selesai dalam56,80detik pada pengujian terakhir. Tidak ada ketergantungan R. EFA Python diuji untuk enam kombinasi ekstraksi/rotasi terhadap matriks faktor yang diketahui, beserta skor/KMO/Bartlett independen, retensi/seed, model tidak layak, dan identitas satu faktor. Pengujian snapshot serta JSON/CSV/XLSX gabungan menjaga sumber, notes, urutan dan idempotency. Lihat ../AUDIT_SISTEM.md untuk bukti, temuan yang diperbaiki dan batas cakupan. Catatan di bawah adalah riwayat versi sebelumnya.

Tanggal 5 November 2026. Lingkungan Windows, Python3.13.5. Versi paket Python tepat tercatat di requirements.lock.txt dan R di ../contracts/r-versions.json. Command: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short`.

Hasil terbaru setelah audit mendalam dan integrasi frontend: **40 passed, 1 warning, 44.19 detik**. Rincian perbaikan pada ../AUDIT_BACKEND.md. Output aktual tersimpan test-output.txt. Warning berasal transisi FastAPI/Starlette TestClient ke httpx2; bukan kegagalan numerik atau response API. Tidak mengubah library hanya untuk menyembunyikan warning.

## Yang dibuktikan

| Pemeriksaan | Hasil |
|---|---|
| Taiwan utama TN/FP/FN/TP | 1973/7/54/12, cocok eksak |
| ROC-AUC/AP | 0.903749617385981 /0.30852372633028535, cocok dalam1e-10 |
| OOF pooled seed42 dan urutan asli | Ambang cocok0.12413099063180978 dalam1e-9; test1921/59/38/28 |
| Prior sama | Test1747/233/20/46 |
| TW03598 | Posterior0.9934229406644826 dalam1e-10 |
| Box M | Cocok322.463 dalam0.002 |
| PCA train | Lima eigenvalue cocok1e-7, rekonstruksi dan orthonormality lolos |
| Kebocoran test | Nilai test ekstrem tidak mengubah parameter fit train atau ambang OOF |
| LDA affine | Probabilitas invariant terhadap transformasi affine nonsingular dalam toleransi |
| Metrik tak terdefinisi | Precision null jika tak ada prediksi positif; kurva tak dipaksakan pada satu kelas |
| Kmeans | Keanggotaan, seed dan inertia cocok hitung ulang |
| EFA | R psych PA oblimin sintetis2faktor; struktur dan uniqueness valid |
| Kontrak hasil | LDA,PCA,EFA,kmeans,hierarchical divalidasi schema |
| Visual1fitur | Hanya profil bar; tidak ada scatter2D palsu |
| Split dan OOF | Group tidak berbagi entitas; temporal urut waktu dan coverage OOF eksplisit |
| Sumber berbahaya | Formula workbook dan arsip traversal ditolak |
| AI | ID bukti rekaan dari model ditolak dengan fallback deterministik |
| API dan job | Impor contoh, validate, run subprocess, idempotency, observation, scenario, snapshot, cancel |
| Ekspor | File JSON/CSV/XLSX/PDF/ZIP/SVG/PNG terbuat dan dapat diunduh |
| CORS/sesi | Browser mutation tanpa token ditolak, origin lokal+token diterima |

Smoke test server nyata di127.0.0.1:8000 membuat proyek contoh dan menjalankan LDA+PCA, bukan fixture statis. IDs pada contracts/demo-session.json berlaku untuk runtime lokal ini. Fixture sintetis selalu diberi synthetic:true. Data tes terisolasi di temp; data demo tersimpan di var.

Pemeriksaan tambahan setelah suite: paket ZIP dari server nyata diunduh, seluruh checksum diverifikasi, lalu dijalankan ulang melalui backend.reproduce pada proses terpisah. ROC-AUC hasil ulang cocok dalam1e-10. Ini menguji paket reproduksi aktual, bukan hanya keberhasilan membuat ZIP.

## Penjelasan reproduksi OOF

Keanggotaan train/test saja tidak menentukan assignment fold OOF. Urutan train juga memengaruhi pembagian fold walau seed sama. Kode makalah mendefinisikan kelas bernama LinearDiscriminantAnalysis sendiri dengan pooled sample covariance; nama solver pada constructor tidak menjadikannya solver SVD scikit-learn. Implementasi contoh memakai pooled dan mengembalikan urutan seed hanya setelah membership cocok persis. Tidak mengubah threshold referensi untuk meloloskan tes.

## Batas bukti

Tes ini bukan audit seluruh dataset yang mungkin, validasi eksternal model keuangan, atau bukti tampilan frontend. Pengujian AI provider aktual belum dilakukan karena tidak ada API key pengguna. Parallel analysis otomatis EFA juga diuji melalui R nyata: batas persentil 95 dan retensi dua faktor cocok. PDF LDA aktual dirender menjadi 11 halaman dan diperiksa; urutan bagian PDF serta rumus khusus PCA memiliki uji regresi. Pemeriksaan ini tidak mencakup setiap kombinasi konten PDF yang mungkin. Detail gap produk dan variasi dari brief ada di README.md dan handoff kontrak. Tidak ada klaim SPSS dijalankan.

## Audit sistem lanjutan

Lihat ../AUDIT_SISTEM.md untuk 12 pengujian baru, perbaikan impor Likuiditas, integritas koordinat PCA/AP, batas simulasi EFA, penomoran kelompok, pemecahan materi indikator, dan konsistensi PDF. Seluruh 40 tes terakhir lulus.

## Pengujian 22 November 2026

44 passed, 3 skipped karena runtime R hilang, 1 warning deprecation Starlette. Tambahan suite/konfigurasi independen, idempotency/revisi, empat metode nyata dengan satu diblokir, SVD PCA independen, linkage/pusat hierarkis, seluruh nilai pada laporan panjang, seed/K/linkage tidak sah, dan pencarian lokasi R. Hasil historis di atas tidak dianggap bukti eksekusi R saat ini. Lihat ../AUDIT_SISTEM.md bagian pembaruan.
