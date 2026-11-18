# Paket analisis multivariat dalam aktuaria

Tanggal penyusunan dan batas pencarian: **4 November 2026**.

Makalah membahas PCA, EFA, gerombol, dan LDA serta mereproduksi secara parsial komponen LDA dalam Belikov (2026), menggunakan data keuangan Taiwan 1999–2009. Semua angka analisis aktual berasal dari **Python**, bukan SPSS.

## Mulai membaca

1. Buka `Makalah_Analisis_Multivariat.pdf` atau versi DOCX yang dapat diedit.
2. Buka workbook `Data_Analisis_Multivariat.xlsx`, mulai dari README, Evaluasi, dan Banding_Sumber.
3. Baca `Output_Analisis_Python.html` untuk ringkasan keluaran, atau `Output/Hasil_Python.json` untuk parameter lengkap.
4. Gunakan `Data_Analisis.csv`, `Analisis_Pembanding.py`, dan `Analisis_Diskriminan.sps` untuk menjalankan ulang.

Identitas penyusun, NIM, dosen, program studi, fakultas, dan institusi pada sampul perlu dilengkapi. Tidak ada identitas fiktif.

## Temuan yang diharapkan

Data: 6.819 rekaman, 6.599 label 0 dan 220 label 1. Train 4.773 (4.619/154), test 2.046 (1.980/66). Lima fitur dipakai tanpa penghapusan observasi, imputasi, atau winsorization.

LDA utama, prior empiris dan ambang 0,5:

| Metrik test | Hasil |
|---|---:|
| TN / FP / FN / TP | 1973 / 7 / 54 / 12 |
| ROC-AUC | 0.9037496174 |
| Average precision | 0.3085237263 |
| Accuracy | 0.9701857283 |
| Sensitivity | 0.1818181818 |
| Specificity | 0.9964646465 |
| Precision | 0.6315789474 |
| F1 | 0.2823529412 |

Keluaran utama cocok dengan Tabel 1–2 Belikov (2026) dalam pembulatan tiga desimal, serta eksak untuk jumlah confusion matrix. **Reproduksi tetap parsial**: seed, daftar anggota train/test, dan beberapa parameter implementasi sumber tidak tersedia. Seed 42 merupakan keputusan kajian yang ditetapkan sebelum hasil. Tidak dilakukan pencarian seed untuk memaksa kecocokan.

## Sumber dan lisensi data

UCI Machine Learning Repository. (2020). *Taiwanese bankruptcy prediction* [Data set]. DOI: https://doi.org/10.24432/C5004D.

Unduhan: https://archive.ics.uci.edu/static/public/572/taiwanese+bankruptcy+prediction.zip.

Lisensi dataset: **CC BY 4.0**, sebagaimana dinyatakan pada laman UCI. Arsip ZIP dan data.csv asli dipertahankan dalam folder Sumber. Data merupakan kurasi publik dari Taiwan Economic Journal, bukan angka yang setiap barisnya telah diaudit ulang terhadap laporan primer oleh penyusun makalah.

SHA-256 `Sumber/data_asli.csv`:

`67bf2e7c75490f7ad3f76bbce57d49cdc25967cdab607527b94f944863fa14d8`

Artikel utama: Belikov, T. A. (2026). *A system for predictive analysis of insolvency in small and medium-sized enterprises: Evidence from financial-ratio-based machine learning classifiers*. Economy and Business: Theory and Practice, (8), 28–37. https://doi.org/10.24412/2411-0450-2026-8-28-37.

Teks artikel tidak disalin ke paket. Metadata, locator, dan ringkasan dukungan klaim tersedia di workbook.

## Data dan konvensi

- `Data_Analisis.csv`: UTF-8, delimiter koma, titik desimal. Angka numerik tidak dikonversi menjadi persentase.
- ID TW00001 berarti baris data pertama setelah header. Nomor fisik CSV adalah nomor baris data + 1. ID bukan kode perusahaan.
- `bankrupt`: 0 = label negatif; 1 = label bangkrut.
- `train`: 1 = pelatihan, 0 = test. Pertahankan kolom ini untuk membandingkan perangkat lunak.
- Prediktor berurutan: WC_TA, RE_TA, ROA_A, EQ_LIAB, TURNOVER.
- Nilai berada pada skala dataset. Pembilang, penyebut, dan parameter transformasi awal tidak lengkap; jangan menganggap 0.8 pasti berarti rasio laporan 80%.
- Tidak ada ID perusahaan/tanggal perbaris. Independensi entitas dan evaluasi temporal tidak dapat diperiksa. Pemrosesan awal donor juga tidak dapat diaudit untuk kebocoran.

## Menjalankan Python

Gunakan Python 3.12. Versi yang digunakan: Python 3.12.14, NumPy 2.5.4, pandas 3.0.1, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2, dan pyreadstat 1.3.7. Daftar pemasangan ada pada `requirements.txt`.

```text
python -m pip install -r requirements.txt
python Analisis_Pembanding.py
```

Jalankan dari folder paket. Kode menentukan lokasi input dari direktori berkasnya, sehingga tidak bergantung pada path pribadi penyusun. Untuk komputer dengan memori terbatas, atur `OPENBLAS_NUM_THREADS=1` dan `OMP_NUM_THREADS=1` sebelum eksekusi. Kode menulis ulang keluaran analisis, CSV, SAV, serta grafik statistik dengan nama yang sama; simpan salinan jika melakukan modifikasi penelitian.

Langkah kode:

1. Membaca CSV mentah, mengambil lima kolom yang ditetapkan, membentuk ID, dan menyimpan split terstratifikasi seed 42.
2. Mengestimasi LDA dengan mean kelompok dan pooled sample covariance **W/(n−G)**; prior berdasarkan ukuran train.
3. Memeriksa fungsi klasifikasi melalui perhitungan matriks lain dan membandingkan implementasi SVD scikit-learn.
4. Menghitung resubstitution, test, OOF lima fold train, ambang F1 dari OOF, serta sensitivitas prior dan 30 seed.
5. Menghitung kanonik, diagnostik, PCA ilustratif, statistik deskriptif, dan visual. Tidak ada EFA/gerombol empiris.

Perbedaan konvensi kovarians pada solver SVD versi aktual menghasilkan posterior sedikit berbeda; label serta AUC/AP test sama. Jangan menuntut kesamaan seluruh digit posterior tanpa memeriksa konvensi. Grafik PCA menggunakan standardisasi train dengan SD sampel; LDA utama tidak distandardisasi ulang.

Workbook dan makalah adalah snapshot hasil final. Mengubah input dalam workbook **tidak mengestimasi ulang LDA**. Formula evaluasi dan contoh hitung dapat menghitung ulang dari inputnya, tetapi model harus diperbarui melalui kode. Sesudah perubahan penelitian, sinkronkan kembali makalah dan workbook dengan keluaran baru.

## Menjalankan SPSS

`Analisis_Diskriminan.sps` ditargetkan pada dokumentasi IBM SPSS Statistics 30 dan **belum dieksekusi**. Ubah satu baris CD ke lokasi folder paket. Syntax membaca CSV, menetapkan label, mematikan Filter/Weight/Split File, memilih train = 1 untuk estimasi, menggunakan prior SIZE dan pooled covariance, serta menyimpan kelas, posterior, dan skor.

Periksa secara khusus:

- Selected cases: 4.773; unselected test: 2.046.
- Kelompok train: 4.619 negatif, 154 positif; prior 0.9677351770 dan 0.0322648230.
- Satu fungsi kanonik, dengan kemungkinan pembalikan tanda atau normalisasi berbeda.
- Matriks klasifikasi **unselected test** dibandingkan dengan 1973/7/54/12.
- CROSSVALID SPSS adalah leave-one-out pada selected cases, **bukan** OOF lima fold Python.

`Data_Analisis.sav` adalah SAV biner yang dibuat oleh pyreadstat dan dapat digunakan sebagai alternatif input. Pembuatan file itu bukan eksekusi SPSS. `Data_Hasil_SPSS.sav` dan `Output_Diskriminan.spv` pada syntax adalah nama keluaran yang baru akan dibuat jika syntax dijalankan. Keduanya tidak disertakan atau dipalsukan.

## Peta berkas

| Berkas/folder | Isi |
|---|---|
| Makalah_Analisis_Multivariat.docx / .pdf | Makalah enam BAB, daftar pustaka, lampiran A–H |
| Data_Analisis_Multivariat.xlsx | 18 sheet, raw lengkap, input, hasil, sumber dan audit |
| Data_Analisis.csv / .sav | Input final dan split yang tersimpan |
| Analisis_Pembanding.py | Kode perhitungan aktual |
| Analisis_Diskriminan.sps | Jalur SPSS yang belum dieksekusi |
| Spesifikasi_Analisis.md | Keputusan analisis serta klarifikasi implementasi |
| Output_Analisis_Python.html | Ringkasan keluaran yang dapat dibaca |
| Output | Parameter lengkap, prediksi, matriks, diagnostik, dan sensitivitas |
| Grafik | Sepuluh gambar PNG 300 dpi dan SVG |
| Data_Grafik | Angka pembentuk visual statistik; boxplot memakai Data_Analisis |
| Sumber | Arsip dataset dan CSV asli |
| Manifest_SHA256.csv | Ukuran serta checksum berkas paket |
| Pemeriksaan_Akhir.md | Catatan verifikasi aktual dan batasnya |

Tidak tersedia aplikasi dataset terbaru yang sebanding. OECD 2026 dan IAIS 2025 hanya memberi konteks industri. Tidak ada klaim bahwa model siap dipakai untuk premi, cadangan, kebutuhan modal, atau keputusan investasi langsung.
