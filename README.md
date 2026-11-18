# Multivariat Lab

Aplikasi lokal untuk belajar, menghitung, dan mempresentasikan analisis multivariat. Backend Python dan R menyediakan hasil, frontend React menampilkan data, rumus, grafik, diagnostik, dan presentasi.

## Buka aplikasi

Frontend: http://127.0.0.1:5173

Dokumentasi API: http://127.0.0.1:8000/docs

Server keduanya sedang dijalankan pada akhir implementasi. Jika sudah berhenti, buka dua terminal dari folder proyek:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-frontend.ps1
```

Frontend membutuhkan Node.js, backend Python dan R. Untuk memasang ulang backend baca backend/README.md; frontend cukup `npm ci --prefix frontend`. Dependensi frontend berada langsung di `frontend/node_modules` pada drive C. Browser pengujian memakai lokasi standar Windows `%LOCALAPPDATA%/ms-playwright`. Sisa instalasi dan berkas sementara dari pemindahan terdahulu disimpan di `tmp/restored-runtime/`. Salinan lama `D:/MultivariatLab-runtime` masih ada sebagai cadangan karena pembersihan otomatis ditolak; aplikasi tidak bergantung padanya.

## Alur penggunaan

1. Pilih **Buka contoh Taiwan** atau buat proyek dan unggah CSV/XLSX.
2. Pilih sheet, format angka, dan peran kolom. Angka label dan teks label dibedakan.
3. Buka **Hasil analisis** untuk melanjutkan draft contoh, atau **Rancang analisis** untuk membuat konfigurasi baru.
4. Pilih tujuan, fitur, parameter, lalu tinjau dan jalankan. Hasil dan split tersimpan sebagai satu versi.
5. Pada LDA, buka tab **Observasi**, cari `TW03598` untuk contoh makalah. Laboratorium keputusan menunjukkan pertukaran antara deteksi dan alarm keliru.
6. Tambah dokumen pada **Dokumen** untuk mencari kutipan pendukung. AI opsional, statistik tetap dihitung lokal.
7. Pilih **Presentasikan**, susun bagian dan catatan, lalu simpan snapshot. Snapshot yang pernah dibuka juga disimpan di IndexedDB browser sebagai fallback jika backend snapshot tidak tersedia.

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

Hasil diuji terhadap data contoh dan skenario regresi, bukan jaminan semua dataset bebas masalah. PCA, EFA, clustering, dan LDA menjawab pertanyaan berbeda. Model Taiwan tidak langsung cocok untuk rasio mentah perusahaan baru. AI belum diuji dengan API key pengguna; pengiriman kutipan membutuhkan pilihan eksplisit. PDF mengikuti bagian dan urutan presentasi tersimpan; tampilannya bukan salinan persis slide browser. Hasil audit terakhir: 40 tes backend dan 8 tes browser lulus. Batas backend rinci ada pada backend/README.md. Tidak ada klaim validasi SPSS atau penerapan aktuaria operasional.
