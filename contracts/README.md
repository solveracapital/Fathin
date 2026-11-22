# Handoff API ke frontend

## Alur otomatis terbaru

Presentasi aktif memakai POST /projects/{id}/presentation-plan, yang menyimpan materi core/appendix dan pilihan awal. Snapshot mengirim presentation_plan_id untuk mengesahkan konten canonical. curated-demo.json adalah contoh aktif: 18 slide utama dan PDF 18 halaman. automatic-demo.json sebelumnya memuat laporan lengkap 141 bagian; itu bukan lagi pilihan presentasi awal.

Endpoint automatic-plan, automatic-plans/start dan analysis-suites/presentation tercantum dalam OpenAPI serta api.d.ts terbaru. Demo makalah otomatis ada di automatic-demo.json; mencakup plan, suite, run, snapshot, tautan editor, dan artifact PDF. ready-demo.json serta multi-analysis-demo.json adalah bukti versi terdahulu. Snapshot/hasil lama tetap disimpan dan tidak dimutasi oleh revisi UI.

Gunakan `openapi.json` sebagai kontrak aktual. `api.d.ts` dihasilkan dengan openapi-typescript7.13.0. Schema hasil/metric/visual pada schemas/. Perbarui setelah endpoint atau model berubah:

```powershell
backend/.venv/Scripts/python.exe -m backend.publish_contracts
npx --yes openapi-typescript@7.13.0 contracts/openapi.json -o contracts/api.d.ts
```

Fixtures Taiwan berasal run nyata dalam tes; fixture PCA/EFA/clustering sintetis memakai synthetic:true. Untuk frontend, payload fixture sintetis pada property result; response API langsung berisi result tanpa wrapper synthetic. Jangan merender synthetic sebagai hasil user. demo-session.json berisi ID proyek/run/snapshot yang sudah ada di server lokal (tidak portabel ke database baru).

Tambahan dari brief: GET /drafts/{id}, GET /projects/{id}/runs, PATCH /datasets/{id}/columns. Role mapping membuat versi dataset baru. Profil/impor/dokumen mengembalikan hasil langsung, tanpa profile/parsing job ID. Export dan statistik punya jobs; statistik mendukung cancel. API aktual belum menyediakan free-form filter atau AI free-form essay. PDF memakai ReportLab dan mengikuti bagian/urutan snapshot. GET /runs/{id}/presentation menyediakan bagian materi terverifikasi; POST snapshot mengesahkan kembali ID content terhadap run yang dipilih. Observasi PCA/EFA mengembalikan scores; clustering mengembalikan cluster 1..K, sama dengan tabel pada run baru. Baca backend/README.md sebelum membangun interaksi yang menganggap semua fitur brief sudah tersedia.

Endpoint health mengembalikan session_token ephemeral; simpan di memori dan kirim X-Session-Token pada mutation request browser. Ini token sesi localhost, bukan secret AI. Setelah server restart ambil ulang token. Kunci API AI hanya server environment.

Pembaruan22November2026: DraftInput.analysis_options dan endpoint validate-suite/analysis-suites tersedia. Tabel status setiap metode terpisah; successful_run_ids dipakai untuk preseleksi laporan gabungan. Snapshot tetap immutable. Contoh lokal terbaru pada multi-analysis-demo.json. EFA saat ini unavailable karena runtime host hilang; jangan menganggap fixture historis sebagai hasil baru.

Versi aktif setelah revisi kesiapan: seluruh metode termasuk EFA memakai Python. Ketergantungan R dan status unavailable akibat R sudah dihapus; catatan sebelumnya tentang R adalah riwayat audit. EFA statsmodels memakai awalSMC dan konvensi retensi yang tercatat pada raw/provenance. JSON ekspor snapshot adalah objek snapshot lengkap (bundles, ordered_sections, notes), bukan gabungan hasil berlabel metode pertama. CSV snapshot default adalah metrik seluruh run.
