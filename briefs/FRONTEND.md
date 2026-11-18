# Brief implementasi frontend Multivariat Lab

Status: acuan implementasi, bukan hasil UI yang telah diverifikasi. Baca README dan SHARED_CONTRACT terlebih dahulu. User menyetujui produk dan menyerahkan keputusan desain; tidak perlu membuka kembali pemilihan framework atau warna. Implementasikan aplikasi yang dapat dipakai, bukan landing page pemasaran. Semua fitur inti dalam brief ini wajib, urutan pengerjaan boleh bertahap.

## Pengguna dan prinsip desain

Pengguna utama adalah mahasiswa yang belum menguasai multivariat, dengan dosen/audiens presentasi sebagai pembaca hasil. User harus selalu memahami: sedang di data/run mana, pertanyaan yang dijawab, arti hasil, tindakan berikutnya. Konteks kerja laptop di ruangan terang dan proyektor kelas menentukan tema terang dengan kontras kuat.

Identitas visual: ruang kerja analisis yang rapi, dengan angka dan grafik yang mempunyai ruang cukup. Keunikan berasal dari penelusuran bukti dan kalkulasi observasi, bukan dekorasi. Signature interaction adalah memilih hasil → melihat formula → membuka observasi → menelusuri kontribusi yang menghasilkan keputusan. Detail ini tampil di panel yang konsisten, bukan popup bertumpuk.

Hindari gradient hero, glassmorphism, neon, ilustrasi maskot, statistik promosi, bento cards dekoratif, angka besar tanpa konteks, shadow tebal, badge untuk setiap kata, animasi masuk berantai, dan chat AI yang mengambil fokus utama. Gunakan pemisah, spasi, dan hierarki sebelum membungkus setiap elemen dalam kartu.

## Token desain final

| Token | Nilai | Fungsi |
|---|---|---|
| canvas | #F4F6F8 | Latar aplikasi |
| surface | #FFFFFF | Konten utama, tabel, dialog |
| surface-subtle | #EDF1F4 | Navigasi dan bagian sekunder |
| ink | #18252F | Teks utama |
| ink-muted | #52616D | Penjelasan sekunder; jangan diturunkan opacity |
| border | #D6DEE4 | Pemisah dekoratif |
| control-border | #7A8995 | Batas input yang harus terlihat |
| accent | #126B70 | Aksi utama dan selection |
| accent-hover | #0D5559 | Hover aksi utama |
| accent-soft | #E6F2F1 | Latar pilihan aktif dengan teks accent |
| focus | #195DCB | Ring fokus |
| success | #246B45 | Status selesai dengan teks eksplisit |
| warning | #805000 | Teks peringatan pada #FFF4D6 |
| danger | #A92C32 | Teks error pada #FDEDEF |

Gunakan CSS variables semantik; tidak menyebar hex pada komponen. Semua pasangan aktual wajib dicek kontras; token bukan bukti otomatis lolos. Target WCAG 2.2 AA: teks biasa 4.5:1, teks besar 3:1, kontrol bermakna 3:1. border dekoratif tidak dipakai sebagai satu-satunya affordance kontrol.

Font UI: Source Sans 3 yang di-host lokal (sertakan lisensi), fallback Segoe UI, sans-serif. Jika unduhan font gagal, Segoe UI tetap sah; jangan menghalangi aplikasi. Satu keluarga untuk UI dan judul. Angka memakai tabular-nums; kode teknis saja menggunakan Consolas/ui-monospace. KaTeX untuk matematika dan fallback teks jika gagal render.

Ukuran rem berbasis 16px: body 16/24, label 14/20, small 13/20, heading halaman 28/36 weight 600, section 20/28, subheading 17/24. Nilai utama maksimal 32/40 dan selalu disertai satuan, denominator, subset. Tabel default 14/20, row tinggi minimum 40. Tidak ada teks penting di bawah 13px. Paragraf penjelasan maksimal 72ch.

Spasi 4,8,12,16,24,32,48. Padding panel 24 desktop/16 mobile. Radius input/button 6px, panel 8px, dialog 12px; tidak semua berbentuk pill. Ikon Lucide SVG 18–20px, stroke konsisten. Button utama height 44px; kontrol padat boleh 36px pada pointer halus dengan target sentuh 44px pada touch. Fokus outline 2px offset 3px. Shadow hanya overlay. Transisi 120–180ms opacity/color; reduced-motion menghilangkan gerakan tak esensial. Tidak ada animasi yang menunda penggunaan.

Chart palette kategori berurutan: #126B70, #365EA8, #A65B1A, #7D4F96, #64723C, #986058. Dua kelas selalu negative biru dan positive oranye, disertai teks/simbol, bukan baik/buruk hijau/merah. Warna cluster bukan risk ranking. Heatmap sequential putih→teal; korelasi diverging biru→putih→oranye dengan domain -1..1. Garis >=2px, label >=13px, grid netral tipis, hindari 3D dan pie chart.

## Kerangka dan navigasi

React + TypeScript + Vite, React Router, TanStack Query untuk server state, React Hook Form + Zod untuk form, Tailwind, Radix primitives atau shadcn yang disesuaikan token, Plotly, KaTeX. Versi dipin setelah install. Tidak perlu Redux, Next.js, GSAP, atau layanan cloud. State URL untuk project/run/tab/selected observation; query cache tidak menjadi sumber kebenaran hasil.

Desktop >=1280: sidebar 224px, topbar 64px, area utama min-width:0 dengan padding 32px; lebar baca 1280px dan data dapat melebar. Layout hasil utama 1fr + panel detail 360px hanya bila ruang konten >=1000px; jika kurang, panel menjadi drawer. Pada 1024–1279 sidebar 192px, padding24; tidak memaksa tiga kolom. Pada 768–1023 navigasi drawer + topbar; dua kolom hanya jika keduanya tetap >=320px. Di bawah768 satu kolom, padding16. Pada320px seluruh halaman reflow; hanya tabel/matriks/grafik yang sungguh dua dimensi boleh scroll dalam region berlabel. Body tidak overflow horizontal.

Sidebar proyek: Data, Rancang analisis, Hasil, Presentasi, Dokumen. Riwayat run berada pada Hasil. Bantuan/glosarium tersedia dekat judul dan menu bantuan. Pengaturan layanan berada di menu aplikasi; user mengisi env server melalui petunjuk, tidak menempel secret ke localStorage.

Topbar: breadcrumb proyek, indikator data/run aktif, status simpan. Tindakan kontekstual maksimal satu primary per area. Navigasi hasil dinonaktifkan sebelum tersedia dengan alasan jelas dan tautan ke langkah berikut. Browser back/refresh tidak menghapus draft tersimpan.

## Spesifikasi layar

| Route | Isi pertama yang terlihat | Aksi utama dan perilaku |
|---|---|---|
| / | Judul Multivariat Lab, satu kalimat fungsi, daftar proyek/tanggal | Buat proyek; aksi sekunder Buka contoh makalah. Tanpa hero besar atau KPI palsu. |
| /p/:id/data | Nama dataset, sumber, jumlah baris/kolom, tombol ganti versi; tabel preview | Unggah data jika kosong; setelah impor Periksa kolom. |
| /p/:id/import/:importId | File terpilih, pilihan sheet/header/encoding/locale dan preview | Konfirmasi impor; kembali tidak menghapus berkas sumber. |
| /p/:id/data/columns | Tabel kolom: nama, tipe, peran, satuan, contoh, missing | Simpan pemetaan; ID/target/waktu tidak otomatis menjadi prediktor. |
| /p/:id/analysis/:draftId | Stepper Tujuan → Variabel → Pengaturan → Tinjau | Lanjut; pada tinjau Jalankan analisis. |
| /p/:id/runs/:runId | Selama job: tahap aktual, konfigurasi ringkas, cancel; selesai: pertanyaan + kesimpulan + bukti | Buka hasil / Presentasikan sesuai state. |
| /p/:id/results/:runId/:tab | Tab Ringkasan, Diagnostik, Perhitungan, Observasi; visual sesuai manifest | Lihat bukti; Buat skenario untuk LDA. |
| /p/:id/presentation | Urutan bagian dari run selesai, thumbnail, judul dan catatan | Simpan snapshot lalu Mulai presentasi. |
| /present/:snapshotId | Satu pesan, satu grafik/tabel, sumber/subset | Next/previous, full screen opsional, Esc keluar. |
| /p/:id/documents | Daftar sumber, status ekstraksi, judul/bagian | Tambah dokumen; lihat kutipan; usulan analisis perlu tinjau. |
| /p/:id/history | Run bertanggal, metode, status, dataset, parameter pembeda | Buka atau duplikasi konfigurasi; jangan edit run selesai. |

Sediakan route riwayat sebagai tautan Hasil, bukan sidebar tambahan yang padat. Not found dan proyek terhapus memberi jalan ke beranda.

### Impor dan pemetaan

Upload memiliki tombol file native dan dropzone opsional, format/limit dari capabilities, progress aktual bila tersedia. Error file tetap dekat input dan tidak menghapus keputusan lain. Locale ambigu tampilkan contoh `1,234` dengan dua interpretasi dan minta keputusan eksplisit; tidak menganggap angka tersebut 1.234/1234 diam-diam. Sheet Data_Analisis disarankan untuk workbook contoh, sedangkan Evaluasi/Prediksi adalah keluaran yang tidak boleh terdeteksi sebagai data mentah tanpa pilihan user.

Profil menampilkan ringkasan kasus dan masalah yang perlu tindakan, bukan puluhan kartu. Preview paginated dengan row key stabil dan nomor baris sumber. Kolom panjang membungkus atau bisa dibuka; ellipsis punya detail yang bisa diakses tanpa hover. Filter preview diberi label tampilan saja dan tidak mengubah input analisis. Jika ingin subset analisis, konfigurasi eksplisit di draft.

### Wizard analisis

Tujuan ditulis dalam bahasa awam plus nama metode dan satu contoh. PCA: Merangkum variabel; EFA: Mengeksplorasi faktor bersama; clustering: Menemukan kelompok; LDA: Membedakan dua kelas. Clustering kemudian memilih k-means/hierarkis. Tampilkan alasan metode dan prasyarat. User dapat mengganti metode dengan menjaga pilihan yang kompatibel.

Variabel: checklist dengan cari, tipe, variasi; tombol pilih semua hanya untuk fitur layak. Target/ID tidak dipilih. LDA wajib target dan kelas positif eksplisit. Kolom entitas/waktu menawarkan split yang sesuai; keterbatasan random split terlihat.

Pengaturan umum ditampilkan dulu, detail lanjutan accordion. Semua default berasal capabilities dan disimpan di draft. PCA basis korelasi/kovarians; EFA jumlah faktor/parallel analysis/ekstraksi/rotasi; cluster skala/jarak/K/seed; LDA split/prior/seed/ambang dan protokol OOF. Tampilkan panduan singkat di tempat pilihan, bukan tooltip wajib. Validasi server menjadi otoritas final.

Tinjau menampilkan variabel berurutan, transformasi, baris eligible, rencana train/test, metode, asumsi, warnings, dan rencana output. Primary Jalankan dinonaktifkan saat blocking, field error mempunyai tautan fokus. Konfigurasi berubah setelah validate harus divalidasi ulang sebelum run.

### Hasil dan bukti

Ringkasan menjawab tujuan analisis dalam dua kalimat deterministik. LDA utamakan jumlah kasus positif terdeteksi dan terlewat, precision, lalu AUC/AP; akurasi berada bersama baseline dan prevalensi. PCA utamakan PVE serta dimensi; EFA kelayakan dan interpretasi loading; cluster jumlah/profil/stabilitas, tanpa klaim kelas risiko.

Default maksimal dua grafik utama per bagian, ditentukan backend. Visual tambahan berada pada panel Pilih visual dengan alasan rekomendasi. Omitted tidak menyisakan heading/kartu kosong. Tidak ada ikon grafik palsu saat hanya tabel yang layak. Judul setiap grafik menyatakan apa yang dibandingkan; caption berisi subset, n, unit, transformasi, sumber, sampling/proyeksi. Tombol Lihat data membuka alternatif tabel. Zoom/pan ada jika berguna; double click reset dan tombol Reset tampilan jelas. Plotly toolbar dipangkas, ekspor lewat menu terlabel.

Diagnostik membedakan validitas komputasi, asumsi model, dan keterbatasan metadata. Jangan satu badge hijau Asumsi terpenuhi untuk semua hal. Evidence drawer memperlihatkan definisi, data asal, dan konvensi. Rumus panjang scroll dalam region, tidak memotong halaman.

Tab observasi: tabel cari ID, subset, actual nullable, prediction, posterior, canonical score. Memilih row membuka lima input, transformasi, kontribusi eta, konstanta, jumlah, expit, keputusan. Urutan dan pembulatan konsisten; tombol tampilkan presisi penuh. Koefisien mentah bukan ranking sebab-akibat. Bukan semua dataset memiliki lima fitur: layout dinamis, pagination daftar kontribusi jika banyak.

### Skenario keputusan

Slider threshold disertai input numerik dan keyboard; rentang0..1, step0.001 untuk interaksi, input menerima presisi lebih tinggi. Debounce150–250ms, abort request lama, loading kecil lokal; tampilkan threshold yang benar-benar dihitung. Confusion matrix dan metrik berasal backend skenario dengan subset sama. Mark original0.5 dan OOF jika tersedia.

Tulisan tetap: Eksplorasi pada data pengujian. Perubahan ini bukan pemilihan ambang tervalidasi. Tombol Hitung ambang dari OOF train membuat job terpisah. Prior sama kontrol terpisah; jangan menukar posterior run utama. Tabel perbandingan menyertakan FP/FN dan jumlah sinyal untuk review. Tidak otomatis menyimpan nilai slider sebagai rekomendasi. Skenario dapat ditambahkan ke snapshot dengan label simulasi.

### Dokumen dan AI

AI berupa panel Bantu memahami, ditutup default. Konteks run/dokumen aktif terlihat. State belum dikonfigurasi, siap, menunggu, gagal, tidak ada bukti, dan jawaban parsial jelas. Jawaban memakai evidence links yang membuka bagian asli; jangan render HTML mentah dari model. Sebelum pengiriman pertama jelaskan apa yang dikirim sesuai send_policy; dataset mentah default tidak dikirim. Retry tidak menjalankan model statistik ulang.

Usulan konfigurasi dari dokumen ditampilkan berdampingan kutipan pendukung dan draft tujuan; user memilih Terapkan ke draft, lalu wajib validate. PDF scan kosong dijelaskan membutuhkan OCR; jangan mengarang isi. Glosarium lokal menjelaskan istilah dasar tanpa API.

### Presentasi dan ekspor

Editor berupa daftar bagian dan preview, bukan canvas bebas. Reorder dengan tombol naik/turun serta drag opsional. Bagian tidak layak tidak dipilih otomatis. Untuk Taiwan alur sembilan bagian sesuai README; EFA/cluster hanya jika ada run tambahan dan label eksplorasi. Catatan pembicara tidak ikut layar audiens atau ekspor kecuali user pilih.

Mode presentasi: typography judul32–40, body22–28, label chart>=18 untuk viewport1366×768. Fit konten dengan memecah bagian, jangan mengecilkan hingga tidak terbaca. Header pesan maksimal dua baris; footer sumber/n/subset/run singkat dan nomor halaman. Next/back keyboard tidak aktif saat fokus di input. Fullscreen API opsional dan kegagalannya tidak menghalangi presentasi. Chart tetap ada setelah reload snapshot offline; AI tidak diperlukan. Cold start server masih perlu lingkungan lokal terpasang; jangan menjanjikan instalasi tanpa internet.

Ekspor memilih format, bagian, precision tampilan, notes opsional. Job status dan download; jangan tampilkan sukses sebelum artifact tersedia. PDF tanpa kontrol UI. CSV/XLSX menyertakan parameter/sumber; memilih download tidak mengubah run. PNG/SVG dari grafik aktual, dengan caption dan fallback yang jelas jika eksportir belum tersedia.

## Semua state wajib

Komponen punya default/hover/focus/active/disabled/loading/error. Empty state menyebut langkah berikut. Skeleton punya dimensi stabil; jangan memakai 0 untuk metrik loading. Toast hanya konfirmasi ringan; error penting persisten dekat masalah. Status job aria-live polite dan tidak diumumkan tiap detik. Refresh memulihkan run aktif dari URL; internet putus pada AI tidak menghapus hasil lokal. Missing R menonaktifkan EFA dengan penjelasan dan petunjuk, tidak mengganti dengan PCA.

Draft disimpan debounce500ms, indikator Menyimpan/Tersimpan/Gagal simpan. Navigasi saat dirty dan belum tersimpan menanyakan buang perubahan atau tetap; file asli tidak terpengaruh. Hapus proyek pakai konfirmasi bernama proyek dan cakupan derivatif. Menu/dropdown portal agar tidak terpotong overflow; focus trap, return focus, Esc pada dialog; keyboard tab order sesuai visual. Tooltip bukan satu-satunya penjelasan. Semua input punya label, error dihubungkan aria-describedby, screen reader table headers benar.

## Penerimaan dan handoff

1. Uji end-to-end buka contoh → run LDA → hasil → observasi TW03598 → skenario → snapshot → ekspor. Uji unggah CSV baru dengan PCA/clustering dan manifest berbeda.
2. Fixture hanya satu grafik benar-benar hanya menampilkan satu; precision null tidak jadi0; warning tidak menjadi success. Uji response lama, refresh job, cancel, error impor, missing R, AI mati.
3. Periksa viewport320,390,768,1024,1366×768,1440×900,1920×1080 dan zoom200%; halaman tidak overflow, tabel mempunyai scroll lokal, footer/tombol tidak tertutup, dialog pendek bisa discroll, label panjang wrap.
4. Uji keyboard seluruh alur, focus visible/not obscured, kontras dengan tool, automated accessibility check dan pemeriksaan manual chart alternatives. Tes label Indonesia panjang dan data 100 kolom.
5. Visual review batched desktop/mobile/presentasi, perbaiki seluruh cacat teramati, lalu konfirmasi sekali. Simpan screenshot dan laporan aktual; jangan klaim nol cacat berdasarkan screenshot satu halaman.
6. Lazy-load Plotly/KaTeX dan halaman berat, pagination tabel, ResizeObserver grafik, min-width:0, cleanup listener. Tidak rerender seluruh chart ketika panel AI berubah. Target respons navigasi lokal <300ms setelah bundle siap; benchmark dan laporkan kondisi, bukan angka marketing.
7. Sertakan README FE, perintah dev/build/test, mock switch eksplisit, build berhasil, laporan E2E/a11y, daftar gap nyata. Dokumentasikan desain implementasi final pada DESIGN.md setelah verifikasi, jangan menganggap brief sebagai bukti render sudah benar.

Jangan menambahkan fitur/animasi/halaman demi mengisi ruang. Jika kontrak belum mendukung kebutuhan, catat perubahan dan selaraskan backend; jangan membuat perhitungan tandingan di browser.
