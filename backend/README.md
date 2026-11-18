# Backend Multivariat Lab

Backend lokal Python/FastAPI dengan EFA melalui R. Jalankan semua command dari root proyek. Runtime data pada `var/`; sumber makalah pada `outputs/makalah_multivariat/` tidak diubah. Jangan menjalankan dua server bersamaan pada runtime directory yang sama.

## Menjalankan di Windows

Lingkungan Python dan paket R sudah dipasang di komputer ini. Mulai server:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1
```

Dokumentasi interaktif: http://127.0.0.1:8000/docs

Untuk instalasi ulang dengan Python 3.13 dan R pada PATH:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-backend.ps1
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe -m backend.publish_contracts
```

Lock Python aktual ada di requirements.lock.txt. `contracts/r-versions.json` merekam versi R yang diuji; instalasi ulang CRAN dapat memperoleh versi berbeda sehingga uji EFA harus diulang. EFA membutuhkan psych, GPArotation, jsonlite. Ekspor gambar memerlukan Chrome/Edge yang didukung Kaleido; sudah diuji pada host ini. Dependency tidak otomatis diunduh saat server start.

## Alur integrasi frontend

1. GET `/api/v1/health`, simpan session_token di memori. Request browser yang mengubah data harus mengirim `X-Session-Token`. CORS default hanya localhost/127.0.0.1:5173. Token jangan disimpan sebagai API key AI.
2. POST `/api/v1/projects` dengan `{ "name":"Presentasi", "description":"" }`.
3. POST `/api/v1/projects/{id}/case-study` untuk contoh. Response berisi dataset_id dan dua draft_ids (LDA lalu PCA). Ini memasang data, tidak mengarang hasil.
4. POST `/api/v1/drafts/{id}/validate`; selesaikan blocking.
5. POST `/api/v1/runs` dengan draft_id,revision:1,idempotency_key unik. Poll GET `/api/v1/runs/{run_id}` hingga terminal; progress null berarti tidak tersedia, bukan0%.
6. GET results, tables, visuals, observations sesuai OpenAPI. Untuk Taiwan gunakan row_id `TW03598` pada endpoint observasi.
7. POST scenarios dengan kind,threshold,subset,idempotency_key. `oof_threshold` membaca hasil pemilihan OOF run; untuk run yang belum menghitung OOF, duplikasi konfigurasi dan jalankan ulang dengan settings.oof=true.
8. GET `/api/v1/runs/{id}/presentation` untuk bagian data/prosedur/rumus/contoh/evaluasi/batas yang berasal dari hasil tersimpan. POST snapshot dengan run_ids/scenario_ids. JSON snapshot sudah berisi bundle hasil yang dibekukan, sehingga presentasi tidak memerlukan AI.
9. POST exports dengan run_id atau snapshot_id,format,idempotency_key; poll jobs; unduh artifact.download_url. Format json,csv,xlsx,pdf,zip,png,svg. PNG/SVG wajib visual_id. CSV dapat memilih table_id.

Impor baru: upload multipart field `file` ke imports, lalu confirm dengan `sheet_name` (XLSX), header_row berbasis1, decimal `.`/`,`, delimiter dan encoding (CSV). Kode kolom `c0,c1,...` stabil meskipun nama duplikat. Jika kolom ID numerik tanpa nama ID, tetapkan column_types.cN='text' saat confirm. Formula XLSX ditolak; gunakan values-only. PATCH datasets/{id}/columns menghasilkan versi baru untuk role/unit/display_name; gunakan ID versi baru pada draft berikutnya. Metadata versi lama tetap untuk run lama.

Draft: method lda/pca/efa/kmeans/hierarchical; feature_ids; target_id dan positive_label untuk LDA. positive_label boleh nilai langsung atau `{value:1,type:"number"}`. Nilai angka dan string harus sama tipe dengan dataset. preprocessing `{missing:"error|median|drop",scale:"none|standard|robust",log:false}`. Clustering default standard jika scale tidak ditentukan. PCA mempunyai standardisasi korelasi sendiri. Jangan menambahkan standardisasi kedua tanpa kebutuhan.

Split: stratified_random(default),saved_membership dengan column_id,group dengan column_id entitas,temporal dengan column_id waktu/cutoff/gap_days. Semua split menyimpan indeks aktual. Split temporal mencakup waktu<cutoff-gap ke train dan>=cutoff ke test; baris dalam gap tidak dipakai evaluasi. Group/temporal OOF menjaga kendala; early temporal train yang belum dapat diberi prediksi OOF tidak ikut pemilihan ambang dan n evaluasi OOF menunjukkan coverage aktual.

Settings LDA: prior empirical/equal/array dua angka positif sum1,threshold0..1,oof boolean,folds default5,oof_estimator pooled default. Contoh Taiwan reconstruct_order=true memverifikasi membership dengan hasil seed42 sebelum memakai urutan train aslinya. OOF contoh tetap pooled; opsi sklearn_svd tersedia sebagai eksperimen eksplisit, bukan reproduksi makalah. Koefisien tersimpan pada skala setelah preprocessing; trace memuat input asli dan transformasi.

Settings PCA: basis correlation/covariance,q opsional,target default0.8,subset train opsional memerlukan split.column_id. Settings EFA: extraction pa/ml,rotation oblimin/varimax/none,q opsional; tanpa q menjalankan common-factor parallel analysis500simulasi. Settings cluster: k,metric,linkage untuk hierarchical; batas full3000baris dan silhouette sample2000.

## AI dan dokumen

DOCX/PDF teks diurai lokal. Endpoint proposal mendeteksi kandidat metode dan bukti, tanpa otomatis memilih fitur atau menjalankan analisis. Assistant menyediakan narasi hasil dan retrieval kutipan tanpa jaringan. Jika AI_BASE_URL,AI_MODEL,AI_API_KEY disetel dan request `send_policy:"summary_and_quotes"`, model boleh memilih ID bukti relevan. Teks hasil yang dipublikasikan tetap kutipan/narasi terverifikasi. Ini pembatasan sengaja: belum menyediakan esai AI bebas atau perubahan konfigurasi otomatis. Jangan mengirim raw dataset ke model. API provider harus kompatibel endpoint chat/completions; belum ada API key pengguna untuk uji provider langsung.

## Batas yang harus diketahui agent frontend

- Frontend tersedia di http://127.0.0.1:5173. Profil/impor/dokumen lokal saat ini synchronous pada request (parsing dokumen memakai thread); run statistik asynchronous dan cancellable. Export asynchronous melalui thread, belum cancel terpisah.
- PDF memakai ReportLab dengan grafik Plotly aktual, bukan renderer HTML/KaTeX. Rumus mengikuti metode. PDF snapshot mengikuti seluruh bagian yang dipilih dan urutannya, termasuk judul yang diedit. Speaker notes disimpan di JSON snapshot dan tidak dicetak untuk audiens. PDF bukan salinan piksel slide atau editor slide bebas.
- SVG/PNG renderer tersedia untuk jenis visual yang dihasilkan sekarang. Biplot interaktif, diagram faktor, histogram profil, elbow pencarian K, dan visual seed sensitivity belum diterbitkan. Backend tidak memaksa visual yang belum dihitung. PCA menyediakan score projection opsional berlabel; cluster1fitur hanya profil.
- Output profil sudah menyajikan distribusi dasar; endpoint rows mendukung pagination/column selection/sort, belum ekspresi filter umum. Run konfigurasi tidak diubah oleh preview sort.
- Belum ada scoring model tersimpan pada data eksternal; input baru harus dilatih sebagai analisis baru. Dataset Taiwan tidak dianggap kompatibel dengan rasio mentah eksternal.
- ZIP berisi data/config/raw/split tersirat pada raw/versions/checksum. Reproduksi: `python -m backend.reproduce path.zip` menggunakan backend ini. Bukan paket instalasi aplikasi mandiri.
- Table endpoints membaca bundle JSON lokal sebelum pagination; ini benar secara respons tetapi belum database-columnar streaming untuk dataset besar. Batas operasional100k×200 bukan benchmark kelayakan semua kombinasi.
- Role/type mapping, run/result schema, dan API aktual adalah acuan integrasi. Brief tetap target produk; bagian yang berbeda di atas adalah gap implementasi nyata, bukan fitur selesai.

## Pengujian

Jalankan pytest sebelum integrasi. Numerical tests meliputi Taiwan utama/OOF/prior sama, PCA eigen/reconstruction, affine invariance LDA, test leakage, undefined metrics, clustering/inertia, EFA sintetis R, group/time split, kontrak visual, penolakan formula/arsip, allowlist bukti AI. Integration test menjalankan worker subprocess, impor contoh, skenario dan ekspor. Ini tidak membuktikan seluruh dataset mungkin atau validitas penggunaan finansial nyata. Detail hasil aktual pada TEST_REPORT.md.
