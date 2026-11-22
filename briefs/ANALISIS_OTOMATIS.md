# Acuan implementasi analisis otomatis

## Amendemen presentasi dan bahasa

Presentasi utama dipilah oleh backend/presentation_plan.py (audience-deck-1), bukan seluruh laporan teknis dipilih otomatis. Contoh makalah memakai 18 slide dengan konsep empat metode dan fokus empiris LDA/PCA; EFA serta kedua gerombol menjadi eksplorasi opsional. Matriks, koefisien, seluruh metrik terpisah dan rincian hitung tetap tersedia dalam dokumentasi teknis opsional. Materi utama memuat konsep/rumus, data/indikator, rancangan, hasil/visual, interpretasi, diagnostik, reproduksi, relevansi dan batas. Data umum mengikuti metode/sumber aktual tanpa klaim kasus Taiwan; jumlah slide menyesuaikan konten, bukan target paksa 18.

POST /projects/{id}/presentation-plan menerima run_ids dan automatic_suite_id opsional. Respons disimpan sebagai deckplan dengan sections, core_count, optional_count, policy_version dan ID. Section memiliki tier core/appendix, group_id, enabled awal; hanya core terpilih. Snapshot menyertakan presentation_plan_id dan memvalidasi proyek/run/suite yang sama. Teks/angka canonical disalin kembali dari rencana, sementara judul/urutan/catatan tetap dapat disunting. Visual utama memuat paragraf interpretasi dan ekspor PDF mengikuti urutan terpilih. Endpoint laporan lengkap lama tetap tersedia.

Keterangan UI bersifat deskriptif: sumber, prosedur, hasil, cakupan. Tidak memakai kalimat yang mengajari pengguna, menyatakan ketidaktahuan, atau menjanjikan pengguna “tinggal baca”. Tombol menyatakan aksi. Blok panduan umum beranda dihapus. Amendemen ini mengungguli pemilihan seluruh isi secara default pada uraian awal di bawah.

Revisi 22 November 2026. Tujuan: mahasiswa yang belum menguasai materi dapat membaca data, menjalankan prosedur yang dapat dipertanggungjawabkan, dan membacakan laporan presentasi. Penyederhanaan memindahkan keputusan teknis ke kebijakan deterministik, tanpa menyembunyikan asumsi atau membuat hasil model yang tidak layak.

## Alur dan tanggung jawab frontend

Data → Analisis otomatis → Hasil dan penjelasan → Presentasi. Konfirmasi impor langsung menuju analisis. Sheet sumber tetap dipilih bila diperlukan; aturan pemisah/angka hanya tampil dalam rincian opsional. Analisis memiliki dua halaman bacaan: mengenali sumber, kemudian membaca rencana dan alasan sistem. Tidak ada pilihan K, q, fitur, prior, missing, seed, rotasi, atau split pada jalur utama. Penelusuran tabel, hasil per metode, observasi dan diagnostik tetap tersedia secara opsional. Riwayat menonjolkan laporan otomatis; daftar run individual menjadi rincian.

Satu penelaahan membahas lima pertanyaan, dengan status ready/hasil numerik yang akan dihitung atau explained/keterangan kelayakan. Setelah berjalan, status model mengikuti worker; kegagalan proses tidak diubah menjadi explained atau angka palsu. Sukses penelaahan dapat mencakup penjelasan tanpa model. Pengguna memilih isi presentasi setelah hasil selesai, melalui kelompok pengantar/data, cara kerja/rumus, hasil/interpretasi, rincian hitung, visual, kelayakan dan kesimpulan/batas. Pilihan halaman/urutan/judul/catatan tetap tersedia sebagai rincian opsional.

Rumus memakai KaTeX lokal, termasuk notasi inline di paragraf dan pecahan, subskrip, superskrip serta matriks. Konten dipaginasi tanpa membuang indikator atau pembahasan. Snapshot membekukan isi/hasil/urutan; snapshot lama tidak ditulis ulang. Pengaturan pilihan isi tidak mengubah perhitungan.

## Kebijakan backend versi presentation-auto-1

- Indikator: kolom numerik finite yang bervariasi; identitas, label, pembagian, waktu, konstanta dan teks dijelaskan sebagai pengecualian. Satu label dipilih hanya dari peran target eksplisit atau nama semantik yang dikenali dan mempunyai dua kelas. Beberapa kandidat label tidak ditebak. Angka dan teks label tetap berbeda.
- Missing: median bila indikator mempunyai nilai kosong. Untuk LDA, median dipelajari dari train; test tidak menentukan imputasi. Parameter aktual dan pengecualian tersimpan di laporan.
- PCA: korelasi, target kumulatif 80%. Makalah memakai train sumber jika proyek contoh dan SHA256 sumber sama dengan CSV makalah. Dataset lain dalam proyek yang sama tidak mewarisi identitas reproduksi.
- EFA: kolom independen melalui QR terpivot pada data tersetarakan; principal axis dan oblimin. Common-factor parallel analysis 500 simulasi menentukan rekomendasi. Kandidat q diuji dari rekomendasi yang masih teridentifikasi menuju jumlah lebih kecil; model harus memenuhi identifikasi, konvergensi dan keunikan positif. Rekomendasi, pilihan aktual, serta penolakan kandidat dicatat. Bila tidak ada solusi layak atau dukungan faktor, terbitkan penjelasan kelayakan. Konstruk tidak diklaim terkonfirmasi.
- K-means: standardisasi, seed 42, k-means++, 20 inisialisasi. K dipilih dari 2–6 yang layak melalui silhouette algoritme K-means pada sampel deterministik maksimal 800 rekaman; model akhir memakai seluruh rekaman eligible. Penilaian eksploratori bukan bukti jumlah kelompok alami.
- Hierarki: standardisasi, Ward Euclidean. Nilai silhouette calon K berasal dari Ward, bukan K-means. Di atas 1.000 rekaman gunakan sampel tetap 1.000 dengan ID asal dan penjelasan cakupan; pemilihan K memakai maksimal 800 dari bagian tersebut. Jangan menyatakan pohon sebagai hierarki seluruh data.
- LDA: prior empiris, ambang utama 0,5. Data makalah mempertahankan saved membership dan rekonstruksi urutan. Data lain default 70/30 terstratifikasi; entitas berulang yang dikenali dipisah antarkelompok, waktu dipisah kronologis. Entitas dan waktu sekaligus atau beberapa kandidat rancangan memerlukan penjelasan khusus, bukan asumsi random split aman. Tahun integer/float integral diparse sebagai tahun, tanggal numerik tidak dianggap nanodetik epoch.
- LDA memilih kolom independen dari variasi dalam kelas train melalui QR; tidak memakai test. OOF maksimal 5 fold, disesuaikan dengan kelas minoritas dan diperiksa dengan estimasi nyata. Jika OOF tidak layak, nonaktifkan hanya skenario OOF, catat alasan, dan periksa ulang model utama. Model utama yang tidak layak menjadi penjelasan tanpa klaim akurasi.

## Integritas API dan hasil

Rencana disimpan terpisah sebagai autoplan, dengan dataset_version_id, hash sumber, policy_version, waktu, konfigurasi dan plan_hash. Start idempotent membuat run terpisah per metode; setiap metode menjalankan validasi yang sama dengan API manual. Perhitungan tidak bersumber dari AI. Hasil, visual, tabel dan laporan mengikuti satu run yang sama.

Bagian kelayakan memiliki suite_id, hash sumber dan bukti plan, tanpa metrik atau run rekaan. Snapshot menolak campuran suite/run/proyek yang tidak sesuai. Konten ilmiah diambil kembali dari bagian canonical, bukan paragraf yang dikirim browser. Snapshot tanpa bundle tetap valid jika memiliki bagian kelayakan, beserta ekspor PDF/JSON/CSV/XLSX. Penghapusan proyek membersihkan autoplan juga.

## Bukti penerimaan dan batas

68 tes backend dan 10 tes browser lulus; tidak ada skip R. Pengujian mencakup lima metode otomatis tanpa pengaturan, missing/kolom duplikat/konstanta, label ambigu, dataset tanpa angka, idempotency, kepemilikan, sampling hierarki, tahun/tanggal, dan reproduksi LDA Taiwan. Laporan sintetis 143 bagian diperiksa seluruhnya pada 1366×768; contoh asli 141 bagian/PDF 141 halaman dengan notasi matematika dirender dan ditinjau. Bukti aktual: backend/test-output.txt, frontend/test-results/, tmp/automatic-audit/, contracts/automatic-demo.json.

Tidak ada klaim semua dataset menghasilkan semua model, semua asumsi terjamin, atau kesalahan nol universal. Menjelaskan ketidaklayakan adalah keluaran ilmiah yang diperlukan. AI, OCR, SPSS eksternal, perangkat proyektor fisik dan deployment multiuser berada di luar bukti tes ini. Pengaturan manual lama tetap tersedia di API untuk kompatibilitas, namun bukan rute frontend utama.
