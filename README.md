# Multivariat Lab

Versi aktif menggunakan analisis otomatis dan presentasi yang dipilah dari laporan teknis. Contoh makalah berisi **18 slide utama**, dengan eksplorasi dan dokumentasi rinci sebagai lampiran yang tidak dipilih secara default. Bahasa antarmuka bersifat deskriptif. Memakai Python saja, termasuk EFA statsmodels; tidak memerlukan R. Pengujian: 70 tes backend dan 10 tes browser. Contoh serta PDF 18 halaman tercatat pada contracts/curated-demo.json. Bukti dan batas audit ada pada AUDIT_SISTEM.md.

Aplikasi lokal untuk belajar, menghitung, dan mempresentasikan analisis multivariat. Backend Python menyediakan hasil, frontend React menampilkan data, rumus, grafik, diagnostik, dan presentasi.

## Buka aplikasi

Klik **Buka Multivariat Lab.cmd** di folder proyek. Launcher menjalankan server lokal dan membuka http://127.0.0.1:5173. Python dan seluruh mesin statistik sudah terpasang di komputer ini; **tidak memerlukan R**. API di http://127.0.0.1:8000/docs.

Instalasi ulang: Python3.13, Node.js, `scripts/setup-backend.ps1`, dan `npm ci --prefix frontend`. Dependensi frontend berada di frontend/node_modules pada C. Tes browser memilih Chrome lokal bila tersedia; alternatifnya pasang Chromium Playwright. Browser Chrome/Edge juga dipakai eksportir grafik.

## Alur penggunaan

1. Pilih **Buka contoh Taiwan** atau buat proyek dan unggah CSV/XLSX.
2. Tinjau data impor; untuk workbook, pilih sheet sumber. Pengaturan format angka berada di rincian opsional jika pembacaan tabel keliru.
3. Buka **Analisis otomatis**, tekan **Lanjut**, lalu baca apa yang dikenali dan mengapa prosedurnya dipilih. Tidak perlu menentukan fitur, K, jumlah faktor, prior, seed, rotasi, atau split sendiri.
4. Tekan **Analisis otomatis**. Sistem menghitung metode yang layak dan menjelaskan pertanyaan yang belum didukung data. Penjelasan kelayakan tetap dapat dipresentasikan; bukan hasil model atau angka rekaan.
5. Dari **Hasil dan penjelasan**, pilih **Pilih isi presentasi**. Rincian hasil per metode tersedia jika ingin menelusuri lebih jauh.
6. Tekan **Susun materi presentasi**. Materi utama terpilih secara default; hasil eksplorasi tambahan dan dokumentasi teknis menjadi lampiran opsional. Judul, urutan halaman, dan catatan pembicara tersedia di rincian.
7. Simpan dan mulai presentasi. Rumus dirender dengan KaTeX pada layar dan notasi yang sama pada PDF. Snapshot yang pernah dibuka juga disimpan di IndexedDB browser sebagai fallback jika backend snapshot tidak tersedia.

Mode presentasi menyembunyikan catatan sampai pengguna membukanya. Tombol panah dan keyboard kiri/kanan berpindah bagian, Esc keluar dari fullscreen browser. Internet tidak diperlukan setelah dependensi terpasang; frontend dan backend lokal tetap harus dijalankan untuk analisis baru.

## Verifikasi dan kontrak

- `backend/` — mesin statistik, API, persistensi, tes, dokumentasi.
- `frontend/` — antarmuka, lock npm, tes browser.
- `contracts/` — OpenAPI, schema, tipe TypeScript, dan fixture.
- `briefs/` — rancangan yang disepakati.
- `AUDIT_SISTEM.md` — audit menyeluruh terbaru, perbaikan, bukti numerik/visual, dan batas yang tersisa.
- `AUDIT_BACKEND.md` — audit backend terdahulu.
- `frontend/TEST_REPORT.md` — hasil pemeriksaan antarmuka.

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
npm run build --prefix frontend
npm run test:e2e --prefix frontend
```

Tes browser memerlukan Playwright Chromium dan server lokal aktif. Browser host ini berada di lokasi standar Windows; tidak perlu mengatur PLAYWRIGHT_BROWSERS_PATH. Untuk instalasi baru gunakan `frontend/node_modules/.bin/playwright.cmd install chromium`.

## Batas produk

Hasil diuji terhadap data contoh dan skenario regresi, bukan jaminan semua dataset bebas masalah. Otomatisasi mengatur prosedur, bukan menebak makna semua kolom atau memaksa setiap metode menghasilkan model. Hierarki di atas 1.000 baris menggunakan sampel tetap yang dinyatakan di laporan; pohon itu bukan hierarki seluruh data. PCA, EFA, clustering, dan LDA menjawab pertanyaan berbeda. Model Taiwan tidak langsung cocok untuk rasio mentah perusahaan baru. AI opsional belum diuji dengan API key pengguna. PDF mengikuti bagian dan urutan presentasi tersimpan; tampilannya bukan salinan persis slide browser. Batas backend rinci ada pada backend/README.md. Tidak ada klaim validasi SPSS atau penerapan aktuaria operasional.

Laporan presentasi diperluas menjadi pembahasan lengkap yang dapat dibaca langsung. Contoh terbaru ada di contracts/multi-analysis-demo.json. EFA kini memakai statsmodels Python dan dapat dijalankan bersama empat metode lain tanpa R.
