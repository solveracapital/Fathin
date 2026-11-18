# Kontrak bersama frontend dan backend

Versi kontrak `1.0.0`. Dokumen normatif; backend menghasilkan OpenAPI dan JSON Schema konkret sebelum integrasi. FE menghasilkan type TypeScript dari schema, bukan memelihara definisi tandingan. Semua path API di bawah berawalan `/api/v1`.

## Struktur dan kepemilikan

`frontend/` dimiliki agent frontend; `backend/` dimiliki agent backend. Backend juga menghasilkan `contracts/openapi.json`, `contracts/schemas/`, `contracts/fixtures/`. Kedua agent boleh memperbarui brief hanya setelah menyelaraskan perubahan. Berkas sumber dan outputs penelitian tidak ditimpa. Runtime state pada `var/` diabaikan git; rahasia tidak masuk repo. `scripts/` memuat launcher lokal dan pemeriksaan dependensi. Backend menyediakan README setup; frontend menambahkan langkah FE pada README root.

## Model informasi

- Project: id, name, description, created_at, updated_at, case_type `custom|taiwan_paper`.
- DatasetVersion: id, project_id, source_sha256, parser_version, filename, sheet_name, header_row, import_options, row_count, columns, immutable_path, created_at.
- Column: id internal stabil, source_name asli, display_name, inferred_type, assigned_type, role `feature|target|id|entity|time|ignored`, unit nullable, source_index. Nama sama tetap dibedakan ID; trimming nama tidak boleh menggabungkan dua kolom.
- AnalysisDraft: id, revision, dataset_version_id, purpose, method `lda|pca|efa|kmeans|hierarchical`, feature_ids berurutan, target_id nullable, positive_label nullable, preprocessing, split, settings.
- AnalysisRun: id, draft_revision, config_hash, dataset_version_id, status, phase, progress nullable, timestamps, seed, engine_versions, split_manifest_hash, artifacts, diagnostics, result_summary. Immutable setelah terminal; pembetulan membuat run baru.
- Scenario: id, parent_run_id, kind `threshold_simulation|equal_prior|oof_threshold`, evaluation_subset_id, settings, status, metrics. Selalu membedakan simulasi dari pemilihan tervalidasi. Prior sama menghasilkan skenario probabilitas tersendiri.
- Evidence: id, kind `table|metric|formula|document_chunk|diagnostic`, locator, dataset_version_id atau document_version_id, run_id nullable.
- PresentationSnapshot: id, project_id, run_ids, scenario_ids, selected_visual_ids, ordered_sections, speaker_notes, created_at, source_hashes. Bekukan data dan narasi; tidak mengubah run.
- Artifact: id, kind, mime_type, size_bytes, sha256, download_url; URL hanya ID terkontrol, tidak membocorkan path host.

Semua waktu API ISO8601 UTC; UI tampil Asia/Makassar. ID berupa UUID/opaque string. Angka JSON titik desimal, full precision finite; NaN/Infinity dilarang. Display Indonesia via formatter; jangan parse balik tampilan sebagai nilai analisis. Label kelas boleh string atau angka: serialisasikan sebagai pasangan nilai+tipe untuk menghindari benturan `1` dan `"1"`.

## Kontrak hasil

`GET /runs/{id}/results` mengembalikan schema_version, run_id, method, subset_definitions, metrics, table_index, formula_index, diagnostics, narrative_blocks, visual_manifest, provenance. Ringkasan tidak memuat seluruh dataset.

Metric: `{id,label,value,unit,subset_id,status,reason,evidence_ids}`. status `ok|undefined|unavailable`. Untuk bukan ok, value=null dan reason wajib. Unit `count|ratio|percent|score|none`. API menyimpan probabilitas/rasio 0..1, UI mengubah persen jika ditentukan metadata; tidak mengalikannya dua kali. Reason memiliki code dan message Indonesia. Tidak ada nilai kosong yang diam-diam diubah menjadi nol.

Table: id, title, columns berisi key/label/type/unit/precision, row_count, subset_id, evidence_ids. Data tabel paginated melalui endpoint; matriks menyertakan row_labels, column_labels, orientation. Confusion matrix wajib actual_rows_predicted_columns dan ordered_labels [negative,positive].

Formula: id, title, latex, symbol_definitions, convention, inputs berupa evidence refs, intermediate_table_ids, output_refs, explanation. Nilai substitusi harus berasal dari run yang sama. Narasi deterministik: id, title, text, evidence_ids, severity, origin `deterministic|ai`, run_id.

Diagnostic: code, severity `info|warning|blocking`, title, explanation, affected_column_ids, evidence_ids, suggested_actions. Acknowledgment warning bukan perbaikan data; blocking tidak bisa dilewati dengan klik setuju.

Visual manifest item: id, kind enum `bar|histogram|boxplot|heatmap|line|scatter|biplot|scree|dendrogram|confusion_matrix|roc|precision_recall|silhouette|contribution`, title, purpose, status `shown|available|omitted|unavailable`, reason_code, reason_text, data_ref nullable, subset_id, axes, series, encodings, evidence_ids, projection nullable, sampling nullable, default_order, table_alternative_ref nullable. projection berisi basis, dimensions, explained_variance dan scaling convention; sampling berisi population_n, displayed_n, seed, strategy. shown wajib punya data_ref dan alternatif tabel/ringkasan numerik; omitted tidak menampilkan kartu kosong. available dapat dipilih dari panel visual tambahan. unavailable menampilkan alasan hanya jika user meminta visual itu. Grafik tidak dipilih hanya oleh AI.

## Endpoint dan perilaku

| Method/path | Request → response |
|---|---|
| GET /health | Status Python/R, database, exporter, AI configured boolean; tidak mengungkap secret |
| GET /capabilities | Metode, parameter/rentang/default, visual kinds, limits, fitur tersedia |
| GET/POST /projects | Pagination / name+description → Project |
| GET/PATCH /projects/{id} | Detail / ubah nama dan deskripsi |
| DELETE /projects/{id} | Hapus proyek dan derivatifnya setelah konfirmasi UI; sumber user eksternal tidak disentuh |
| POST /projects/{id}/imports | Multipart file → import_id, inspection (sheet names/encoding/header candidates); belum analisis |
| POST /imports/{id}/confirm | sheet/header/locale/type decisions → DatasetVersion + profile job |
| GET /datasets/{id}/profile | Profil tersimpan + status job + diagnostics |
| GET /datasets/{id}/rows | offset/limit/column_ids/sort/filter → rows,total; original row key tetap ada |
| POST /projects/{id}/drafts | Konfigurasi → draft+revision |
| PATCH /drafts/{id} | expected_revision+patch → draft baru; konflik 409 |
| POST /drafts/{id}/validate | → blocking,warnings,estimated_work,plan; tidak melatih model |
| POST /runs | draft_id,revision,idempotency_key → run_id/job_id (202) |
| GET /runs/{id} | Status, phase, progress, error nullable |
| POST /runs/{id}/cancel | Pembatalan idempotent; status aktual dikembalikan |
| GET /runs/{id}/results | Hasil immutable |
| GET /runs/{id}/tables/{table_id} | Pagination dan metadata |
| GET /runs/{id}/visuals/{visual_id} | Data grafik, provenance, metadata; tidak menghitung ulang statistik |
| GET /runs/{id}/observations/{row_id} | Nilai input, transformasi, formula, contributions, score, prediction, label nullable |
| POST /runs/{id}/scenarios | kind+parameter+subset → scenario job atau hasil cache |
| GET /scenarios/{id} | Status+hasil+manifest; subset eksplisit |
| POST /projects/{id}/documents | DOCX/PDF → document_id + parsing job |
| GET /documents/{id} | Status, metadata, bagian/chunk dan keterbatasan ekstraksi |
| POST /documents/{id}/analysis-proposal | → proposed config+evidence; tidak menjalankan analisis |
| POST /projects/{id}/assistant | run_id,question,allowed_document_ids,send_policy → answer+evidence+status |
| POST /projects/{id}/snapshots | Urutan dan refs valid → snapshot_id |
| GET /snapshots/{id} | Snapshot siap presentasi; seluruh data yang perlu sudah disertakan |
| POST /exports | run_id atau snapshot_id,format,selection → export job |
| GET /jobs/{id} | Status generik, phase, artifact_id nullable, error nullable |
| GET /artifacts/{id}/download | Stream dengan filename aman dan MIME benar |
| POST /projects/{id}/case-study | Memasang dataset/profil makalah → dataset_id,draft_ids; tetap perlu run untuk hasil baru |

List memakai `{items,total,offset,limit}`; limit default 50 maksimum 200. Data grafik maksimum sesuai capabilities; tabel bukan dikirim seluruhnya untuk pagination palsu. Import/schema error 422; file terlalu besar 413; missing dependency 503; data tidak ditemukan 404; conflict 409. Semua error `{error:{code,message,field_errors:[{path,message}],request_id,retryable}}`; stacktrace hanya log developer, jangan memuat data rahasia.

Job state `queued→running→succeeded|failed|cancelled`; cancelling hanya state transisi opsional yang FE dukung. Progress boleh null, dilarang persentase rekaan. Phase `importing|profiling|validating|preprocessing|fitting|evaluating|building_results|exporting`. Stale job setelah crash menjadi failed dengan reason INTERRUPTED dan tombol buat run baru. Poll 1s saat aktif, mundur 2–5s jika tab pasif; berhenti pada terminal. Tidak perlu websocket V1. Cancel harus menghentikan subprocess R dan tidak menerbitkan hasil sebagian sebagai succeeded.

POST run/export/scenario mempunyai idempotency key. Kunci sama + payload sama mengembalikan pekerjaan sama, payload berbeda 409. Backend cek revision/config hash sebelum eksekusi. FE membatalkan request lama atau mengabaikan response yang tidak cocok run ID; tidak pernah menimpa hasil baru dengan response lama.

## Fixture wajib

Sediakan JSON valid untuk: Taiwan LDA selesai; PCA selesai; EFA warning; clustering tanpa proyeksi 2D layak; dataset satu fitur; kelas minoritas tak cukup untuk split; import locale ambigu; job running dengan progress null; failed missing R; cancelled; precision undefined; manifest hanya satu grafik; AI unavailable; snapshot. Fixture Taiwan berasal dari kalkulasi nyata; fixture sintetis berlabel synthetic. Fixture harus lulus schema yang sama dengan response nyata.

## Keamanan lokal dan integrasi

Server bind loopback default, CORS hanya origin lokal yang dikonfigurasi; perubahan state JSON memakai pemeriksaan Origin dan token sesi lokal untuk mencegah situs lain mengendalikan server localhost. Jangan percaya filename, path upload, formula spreadsheet, atau isi dokumen. File ekspor tabel memperlakukan teks berawalan =,+,-,@ sebagai teks aman tanpa mengubah data numerik. Batasi zip bomb, expanded XLSX, jenis file, page count, timeout, dan memory. Jangan load pickle/model upload dari pengguna. AI key melalui env server; FE hanya melihat configured true/false. Logging menggunakan ID dan metadata; raw isi data/secret tidak dicatat default.
