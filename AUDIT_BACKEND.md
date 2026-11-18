# Audit backend Multivariat Lab

Audit independen lanjutan, 5 November 2026. Menelaah formula, train/test/OOF, preprocessing, impor, persistensi, job/cancel, API, ekspor, snapshot, dan integrasi frontend. Hasil audit bukan klaim bebas cacat mutlak; jaminan dibatasi pengujian dan skenario yang dicatat.

## Temuan yang diperbaiki

| Temuan | Dampak | Perbaikan dan bukti |
|---|---|---|
| transform_apply mengisi median walau missing policy error | Pengolahan test dapat berbeda dari persetujuan user | Policy disimpan dan ditegakkan pada apply; regression missing-policy |
| Baris temporal gap diberi subset test | Label tabel salah dan bisa salah dibaca sebagai evaluasi | Keanggotaan train/test/excluded eksplisit, tabel menamai excluded_gap; regression5baris |
| K/q dikonversi int diam-diam | Konfigurasi pecahan dihitung sebagai nilai lain | Tolak pecahan/bool dan batas dimensi; tes parameter |
| Target PVE1 dapat memilih p+1 akibat pembulatan | PCA valid bisa gagal | Cumulative terakhir diset1 dan pemilihan dibatasi p; reconstruction tetap diuji |
| evaluate menerima probabilitas NaN/di luar rentang | Prediksi invalid dapat menjadi kelas negatif | Validasi finite/range/dimensi/label/threshold sebelum metrik |
| Baseline selalu negatif walau train mayoritas positif | Perbandingan dataset baru menyesatkan | Baseline memilih mayoritas train; contoh Taiwan tetap sama |
| SQLite connection tidak ditutup setelah context transaction | Kebocoran resource/lock pada banyak request | Context manager menutup koneksi pada semua jalur |
| Cancel dan success dapat saling menimpa | Run dibatalkan bisa terbit sukses | Transition transaksional dengan expected status; worker claim/finish atomik |
| Idempotency start tidak dilindungi request paralel | Job duplikat pada double-click | Lock mutation di proses server; tes4request bersamaan menghasilkan1run |
| Worker berhenti tanpa output terminal | UI dapat menunggu tanpa akhir | Scheduler menandai WORKER_EXIT; startup memulihkan run dan export job terputus |
| ID folder kosong/literal '-' diterima | Folder runtime root bisa terpilih | Wajib UUID valid sebelum operasi folder |
| Temp atomic writer berbagi nama yang sama | Penulisan bersamaan dapat mengganggu | Temp unik per penulisan lalu rename |
| pandas.NA dapat berubah menjadi string | Missing dianggap teks sumber | Serialize pandas missing menjadi null |
| explicit text pada XLSX numeric tidak selalu jadi teks | Metadata dan nilai tidak sejalan | Cast text secara eksplisit; regression leading-zero CSV |
| Infinite numeric saat import dapat berubah null | Nilai invalid berubah missing tanpa keputusan | Tolak infinite sebelum persistensi |
| PCA train ditampilkan sebagai all | Subset grafik/tabel tidak tepat | Default subset metode mengikuti konfigurasi dan n aktual |
| Ringkasan model/Phi/preprocessing tidak semuanya terekspos | Sulit memeriksa logika perhitungan melalui API | Tambah tabel model_summary, factor_diagnostics, pca_scores/directions, preprocessing |
| Export format arbitrer dan archive rusak belum tervalidasi | Error server tak terstruktur | Whitelist format dan handler arsip422, fallback500 tersanitasi |
| Snapshot grafik tertentu membutuhkan API saat presentasi | Presentasi cache dapat kehilangan grafik | Bekukan figure JSON dan data; frontend menyimpan snapshot di IndexedDB |
| Kurva ROC/PR belum mempunyai judul sumbu | Interpretasi grafik tidak jelas | Label sumbu diterbitkan dari server |

Impor mempertahankan data sumber, split tidak melatih scaler pada test, median diestimasi per fold, AP diskret memakai implementasi pustaka, dan eigen canonical tetap mengikuti B a=lambda W a. Kesesuaian numerik Taiwan diperiksa ulang setelah perubahan, tanpa mengubah toleransi.

## Bukti pengujian

Suite backend mencakup pengujian statistik Taiwan, PCA rekonstruksi, invariant affine, kebocoran test, EFA R, clustering, split dan OOF group/temporal, kontrak hasil, keamanan berkas, idempotency, cancel, pemulihan dan ekspor. Hasil tepat terbaru ada backend/test-output.txt; ringkasan pada backend/TEST_REPORT.md. Suite frontend menggunakan API server nyata, bukan fixture yang menirukan keberhasilan.

## Risiko dan batas yang tetap berlaku

- Server harus satu proses pada runtime directory yang sama; lock idempotency adalah per proses. Multiuser/cloud bukan lingkup aplikasi lokal ini.
- Pengolahan100k×200 adalah batas input, bukan bukti semua kombinasi cukup memori/waktu. Parsing/profiling masih memuat data lokal, bukan streaming columnar.
- Statistik inferensial tetap bersyarat pada asumsi; metadata entitas/waktu Taiwan tidak tersedia. P-value kecil bukan jaminan model valid dan posterior belum terkalibrasi eksternal.
- Pengiriman ke provider AI aktual belum diuji karena API key belum disediakan. Layanan model hanya memilih bukti yang dikenal, bukan menghasilkan angka statistik.
- Keberhasilan ekspor file tidak membuktikan seluruh layout dokumen pada semua isi. PDF memakai ReportLab ringkasan, bukan renderer slide bebas.
- Saat driveC penuh, pemasangan dan beberapa tes gagal dengan ENOSPC. Itu dibedakan dari kegagalan logika. Dependensi/cache frontend dipasang padaD dan tes diulang setelah ruang tersedia. Tidak ada penghapusan berkas user atau sumber penelitian.
