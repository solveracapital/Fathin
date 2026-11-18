# Spesifikasi terkunci sebelum hasil
Tanggal 2026-11-04. Sumber utama Belikov (2026); dataset UCI 572, CSV urutan asli.
Fitur: Working Capital to Total Assets; Retained Earnings to Total Assets; ROA(A) before interest and % after tax; Equity to Liability; Total Asset Turnover.
Tidak menghapus kasus atau mengganti angka. Label asli 0/1. Split stratified 70/30 seed 42 sebagai keputusan analisis karena seed sumber tidak dilaporkan.
LDA solver svd prior empiris, tanpa seleksi fitur; pooling sample unbiased untuk pemeriksaan kanonik manual.
Utama holdout threshold 0.5, resubstitution terpisah. Tambahan 5-fold OOF train untuk memilih threshold F1 dan pengujian satu kali pada test; prior equal sebagai sensitivitas; 30 seed 0..29 sebagai sensitivitas split, bukan pencarian seed sumber. Jangan memilih seed berdasarkan kecocokan.
Metrik ROC-AUC, average precision (bukan trapezoidal PR area), accuracy, sensitivity, specificity, precision, F1, balanced accuracy. Nol penyebut precision dilaporkan tidak terdefinisi pada baseline.
Toleransi sumber tiga desimal ±0.0005, jumlah kasus eksak. Kesamaan split tidak dapat dijamin. Uji Box M chi-square aproksimasi, Shapiro per fitur dalam kelompok, kovarians rank dan condition, jarak Mahalanobis. Tidak menghapus pencilan.
Tidak melakukan EFA pada lima rasio tanpa model reflektif. PCA tambahan hanya ilustrasi deskriptif pada train dan bukan input model utama.
Klarifikasi implementasi 2026-11-04: perhitungan utama memakai kovarians pooled sample W/(n-G) sesuai spesifikasi matriks. Pemeriksaan awal menunjukkan scikit-learn 1.9.1 solver svd menghasilkan koefisien berbeda dengan faktor skala n/(n-G). Karena itu solver tersebut disimpan sebagai pembanding implementasi terpisah; klasifikasi dan ROC/AP sama pada data uji. Pemilihan seed 42 dilakukan sebelum hasil, tidak diubah setelah ditemukan kecocokan. Perbandingan ambang optimal memakai OOF train, bukan resubstitution sebagaimana prosedur sumber.
