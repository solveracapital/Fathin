# Pengujian frontend

Tanggal 5 November2026. Build `npm run build --prefix frontend` berhasil dengan TypeScript strict dan Vite6.4.5. Grafik Plotly dan rumus KaTeX lazy-loaded dalam chunk terpisah; warning chunk Plotly>500kB tetap terlihat dan bukan kegagalan build.

## Browser end-to-end

Command `npm run test:e2e --prefix frontend`, Chromium headless Playwright pada Windows, API lokal nyata, worker Python/R nyata. **8 passed sekitar1,3menit**. Tidak memakai backend mock atau hardcode hasil analisis.

1. Hitung ulang contoh LDA/PCA, buka hasil, cocokkan12/66kasus terdeteksi; skenario OOF menghasilkan28TP; observasi TW03598 menampilkan posterior0.9934229407; eksporCSV tersedia; susun snapshot dan berpindah bagian tanpa browser exception.
2. UnggahCSV baru, petakan ID sebagai teks dengan leading zero, jalankan wizardPCA, terima hasil dan pastikan confusion matrix tidak dipaksakan pada PCA.
3. Jalankan Axe untuk WCAG2A/AA dan2.1AA pada halaman hasil (rule region dikecualikan karena komponen grafik); **0violations** pada cakupan tersebut. Periksa halaman pada lebar320,390,768,1024,1366,1440,1920 tanpa horizontal overflow dokumen. Dialog navigasi mobile bisa dibuka dan ditutup lewat Escape.
4. Unggah makalahDOCX, baca kutipan sumber lokal, identifikasi kandidat metode, dan gunakan assistant tanpa API key model.
5. Snapshot yang telah dibuka tetap dapat dibaca setelah endpoint snapshot diputus pada browser, menggunakan IndexedDB lokal.

Report mesin pada test-results/report.json. Screenshot home, hasil1440, hasil390 dan presentasi pada test-results/screenshots/; digunakan untuk pemeriksaan, bukan aset produk. Screenshot diperiksa dan perbaikan dikonfirmasi pada matriks mobile, nama label formulir, tombol penelusuran dan lifecycle resize grafik. Automated Impeccable detector menghasilkan [] pada frontend/src.

## Batas

Automated accessibility check tidak menggantikan uji pembaca layar penuh. Semua kemungkinan konten/ukuran dokumen belum diuji. Preview proyektor diuji melalui mode presentasi browser; belum diuji pada perangkat proyektor fisik. Font/grafik lokal tersedia setelah pemasangan; cache snapshot tidak membuat cold start tanpa server/dependensi menjadi aplikasi mandiri. Esai AI bebas dan editor slide canvas tidak disediakan.

Penghapusan/ubah nama proyek memakai API nyata dengan dialog konfirmasi; test suite utama fokus alur analisis/presentasi. Layout tabel/matriks yang benar-benar dua dimensi boleh mempunyai scroll lokal. Rasio grafik dan metadata bergantung pada hasil backend, tidak dibuat untuk mengisi ruang.

## Audit sistem lanjutan

Tiga tes tambahan memakai Taiwan LDA/PCA serta dataset sintetis enam indikator untuk k-means, hierarkis dan EFA. Tes memeriksa titik SVG PCA yang benar-benar tampil dan cocok persis dengan API, visual dan modal observasi metode lain, Axe tanpa pelanggaran pada cakupan, serta seluruh 17 bagian gabungan LDA/PCA pada1366×768. Nilai keanggotaan/skor observasi cocok dengan tabel. Bukti pada test-results/system-audit/ dan laporan menyeluruh ../AUDIT_SISTEM.md. Detector terakhir menghasilkan [].
