# Pemeriksaan akhir

Pemeriksaan dilakukan 4 November 2026. Catatan ini menjelaskan pemeriksaan aktual, bukan sertifikasi validitas ilmiah menyeluruh.

## Dokumen

- DOCX dibuka dengan Microsoft Word, field/daftar isi diperbarui, dan diekspor menjadi PDF 70 halaman. Bagian utama BAB I–VI berjumlah sekitar 12.734 kata menurut ekstraksi PDF, termasuk tabel, caption, dan nomor halaman.
- Seluruh 70 halaman PDF dirender dan diperiksa secara visual per halaman. Pemeriksaan mencakup persamaan, tabel, caption, gambar, daftar pustaka, daftar isi, dan nomor halaman. Tabel panjang memakai header berulang; tabel pendek dipertahankan utuh. Ruang kosong pada akhir bab/bagian mengikuti aturan pergantian bab.
- Tidak ditemukan token template yang belum diganti pada PDF. Placeholder hanya untuk identitas administratif pada sampul.
- Jalur render_docx.py tidak dapat digunakan karena LibreOffice tidak tersedia. Pemeriksaan memakai ekspor Microsoft Word dan render PyMuPDF sebagai alternatif aktual.
- 18 referensi unik tercantum dan digunakan; register mencatat bagian yang dibaca serta batas akses. Sumber yang hanya tersedia sebagai abstrak tidak dipakai untuk mengklaim rincian hasil yang tidak dibaca.

## Data dan angka

- Data CSV dan SAV dibaca kembali: 6.819 baris dan 8 kolom, ID identik, selisih numerik maksimum 0.
- Raw_Asli pada XLSX diperiksa seluruhnya terhadap CSV asli: 6.819 × 96 nilai sesuai dalam toleransi numerik ekspor Excel (rtol 1e-13, atol 1e-15).
- Prior, pembagian train/test, koefisien, matriks klasifikasi, dan metrik berasal dari keluaran Python. Pemeriksaan fungsi klasifikasi melalui dua formulasi matriks memberi perbedaan posterior maksimum sekitar 7,43e-14.
- Data uji utama: TN 1973, FP 7, FN 54, TP 12; akurasi 0,9701857283; sensitivitas 0,1818181818; AUC 0,9037496174.
- Output model utama cocok dengan sumber dalam pembulatan metrik tiga desimal dan tepat untuk empat jumlah klasifikasi. Status tetap reproduksi parsial karena identitas split dan seed sumber tidak tersedia.

## Workbook

- XLSX dibuat dengan artifact-tool dan berhasil dibuka, dihitung ulang, serta disimpan oleh Microsoft Excel. Terdapat 18 sheet. Data mentah lengkap, data analisis, prediksi, sumber, audit klaim, dan angka pembentuk grafik tersedia.
- Sel formula diperiksa tanpa error Excel tersimpan. Formula evaluasi menghitung confusion matrix/rasio dari Prediksi. Parameter LDA adalah snapshot hasil Python, bukan model yang dilatih ulang otomatis oleh Excel.
- Uji perubahan input contoh: posterior berubah dari 0,9934229407 menjadi 0,9927409509 setelah WC_TA ditambah 0,01; nilai asli dipulihkan. Excel menghitung ulang posterior 0,9934229407 dan akurasi test 0,9701857283.
- Pratinjau masing-masing sheet diperiksa. Format hitungan bulat, p-value ilmiah, label lokasi bab, serta catatan contoh diperbaiki dan bagian yang berubah diperiksa kembali dari ekspor Excel.
- Pemeriksaan visual workbook memakai area contoh, bukan inspeksi visual setiap sel. Pemeriksaan numerik raw meliputi seluruh nilai.

## Batas yang masih ada

- SPSS tidak tersedia untuk eksekusi. Syntax .sps belum diuji; tidak ada file .spv atau screenshot hasil SPSS. SAV ditulis dan dibaca dengan pyreadstat.
- Tidak tersedia dataset terbaru dengan kelima fitur pada skala dan label yang sebanding. OECD 2026 dan IAIS 2025 digunakan hanya sebagai konteks.
- Identitas perusahaan, waktu tiap baris, komponen pembentuk rasio, serta parameter transformasi donor tidak tersedia. Independensi dan kebocoran pada proses sebelum publikasi dataset tidak dapat dipastikan.
- Asumsi kovarians bersama mendapat penolakan diagnostik. Model belum dikalibrasi atau divalidasi eksternal dan tidak menjadi dasar langsung untuk premi, cadangan, modal, atau keputusan investasi.

Manifest_SHA256.csv mencatat checksum berkas final; manifest itu sendiri tidak memasukkan checksum dirinya. ZIP berisi salinan paket yang sama.
