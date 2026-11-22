# Pengujian frontend

## Status terbaru: bahasa netral dan presentasi inti

**10 passed** dalam sekitar 1,8 menit pada Chrome Windows dengan API dan worker nyata. Pemeriksaan akhir seluruh 18 slide makalah juga menghasilkan 0 overflow dan 0 browser error; PDF akhir tepat 18 halaman.

Jalur utama memakai keterangan deskriptif; blok panduan beranda yang ditunjuk pengguna dihapus. Editor kini memilih materi inti secara default, dengan daftar slide yang bisa dicentang dan lampiran nonaktif. Data sintetis lima metode menghasilkan 24 slide utama; contoh makalah asli menghasilkan 18 slide utama. Tes memeriksa bahwa dokumentasi teknis tidak terpilih, jumlah snapshot mengikuti materi inti, rumus dirender, tidak ada overflow pada proyektor, serta presentasi tanpa model tetap valid. Home diuji tanpa home-guide. Build TypeScript/Vite berhasil dan detector satu kali menghasilkan []. Bukti inspeksi editor desktop/mobile, seluruh 18 slide, dan PDF 18 halaman tersimpan di ../tmp/curated-audit/. Bagian berikut mencatat versi 143 bagian yang sekarang menjadi dokumentasi opsional, bukan pilihan presentasi awal.

## Status terbaru: alur otomatis untuk presentasi, 22 November 2026

**10 passed** pada Chrome Windows/Playwright, API dan worker statistik nyata; durasi sekitar 2,1 menit. Build TypeScript/Vite berhasil. Tes utama tidak mengisi satu pun input prosedur: data → Lanjut → Analisis otomatis → pilih isi presentasi. Kelima metode berhasil pada data sintetis yang sesuai. Laporan 143 bagian diperiksa seluruhnya pada 1366×768 tanpa overflow, menunggu KaTeX/font sebelum pengukuran; tidak ada katex-error. Penjelasan saja untuk dataset tanpa indikator juga berhasil menjadi presentasi, tanpa model palsu. Axe pada halaman penelaahan/hasil otomatis dan hasil rinci tidak menemukan pelanggaran pada cakupan tes. Pemeriksaan lebar 390/768/1366 untuk alur baru melengkapi pemeriksaan responsif halaman hasil sebelumnya.

Pilihan isi disajikan per kelompok; judul/urutan/halaman/catatan berada dalam rincian opsional. Riwayat menonjolkan laporan, bukan daftar konfigurasi. Screenshot pada test-results/automatic-*.png, presentation-choices.png, dan multi-report/. Contoh makalah 141 bagian diekspor menjadi PDF 141 halaman; seluruh halaman dirender sebagai kontak dan 11 halaman dirender lebih besar di ../tmp/automatic-audit/. Rumus blok dan inline memakai KaTeX lokal pada browser dan PDF; hasil inspeksi tidak menunjukkan clipping pada sampel yang ditinjau. Detector dijalankan sekali pada frontend/src dengan exit 0 dan tanpa temuan keluaran. Batas pengujian tetap pada ../AUDIT_SISTEM.md. Bagian berikut adalah riwayat versi sebelumnya.

## Status terbaru: revisi kesiapan tampil, 22 November 2026

**9 passed** pada Chrome Windows melalui Playwright, menggunakan API dan worker nyata. Tes pilih semua kini mewajibkan **lima metode berhasil** tanpa pengecualian EFA. Laporan132bagian diperiksa pada1366×768 tanpa overflow; PDF132halaman mempertahankan jumlah/urutan dan dirender untuk QA. Build TypeScript/Vite dan detector berhasil. Launcher diuji pada cold start dan pembukaan ulang. Tidak memerlukan R. Detail serta batas pada ../AUDIT_SISTEM.md; catatan di bawah adalah riwayat versi sebelumnya.

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

## Pengujian 22 November 2026

9 passed menggunakan Chrome Windows yang sudah terpasang melalui Playwright. Browser Chromium bundel terdahulu tidak lagi ada; config memilih Chrome lokal bila tersedia. Tes baru mencakup checkbox/pilih semua, pengaturan mandiri, empat metode nyata, hasil suite, preseleksi presentasi, dan seluruh86halaman laporan pada1366×768 tanpa overflow. Sampel screenshot diperiksa langsung. EFA tidak dijalankan karena capability runtime R unavailable. PDF86halaman diperiksa urutan dan jumlahnya serta dirender untuk QA. Snapshot Taiwan terbaru90halaman. Detail ../AUDIT_SISTEM.md.
