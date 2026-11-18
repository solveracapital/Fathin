# Desain implementasi Multivariat Lab

Implementasi mengikuti briefs/FRONTEND.md dan PRODUCT.md; bukan arah visual baru. Diverifikasi pada aplikasi berjalan, 5 November2026.

## Sistem visual

Mode Operate, tema terang untuk laptop dan proyektor kelas. Source Sans3 lokal dengan SegoeUI fallback; data memakai tabular numerals, kode Consolas, rumus KaTeX. Canvas #F4F6F8, surface putih, teks #18252F, sekunder #52616D, aksi #126B70, focus #195DCB. Radius kontrol6px, panel8px, dialog12px. Border ringan untuk konten, border lebih kuat untuk input. Tidak ada dekorasi raster atau gradient.

## Struktur

Sidebar224px desktop/192px laptop, topbar64px, padding konten32/24/16px. Navigasi berubah menjadi dialog pada<1024px. Tabel lebar scroll lokal; matriks2×2 menyesuaikan layar kecil. Hasil memakai ringkasan naratif, empat ukuran utama, visual yang dipilih backend, lalu eksplorasi/penelusuran. Form label terhubung ID eksplisit. Detail lanjutan berada di disclosure native. Fokus dan dialog ditangani Radix/native controls.

## Interaksi khusus

Tab Observasi menghubungkan rowID, sumber, transformasi, koefisien, kontribusi eta dan posterior. Laboratorium ambang memakai request dibatalkan saat superseded, subset test tetap, dan label eksplorasi. Autosave draft menserialkan revisi; respons simpan tidak menavigasi kembali setelah pengguna meninggalkan halaman. Grafik dimuat lazy dan ResizeObserver dilepas saat pindah halaman.

## Presentasi

Snapshot immutable, satu pesan utama per bagian, kontrol next/previous dan fullscreen, catatan terpisah dari konten default. Figure JSON/data dibekukan server dan snapshot dicache IndexedDB. Label kelas negatif/positif terlihat selain warnanya. Salinan PDF adalah laporan ringkasan, bukan render piksel slide.

## Verifikasi

Build TypeScript/Vite berhasil. Automated design detector mengembalikan []. Axe pada hasil tidak menemukan pelanggaran rule-set A/AA yang diuji. Browser diuji320,390,768,1024,1366,1440,1920; tidak ada horizontal overflow halaman. Screenshot desktop, mobile, home dan presentasi diperiksa; perbaikan matrix mobile, header grafik, dan bagian penelusuran dikonfirmasi. Bukti dan batas pemeriksaan pada frontend/TEST_REPORT.md. Ini bukan klaim semua state semua dataset bebas cacat.
