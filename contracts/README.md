# Handoff API ke frontend

Gunakan `openapi.json` sebagai kontrak aktual. `api.d.ts` dihasilkan dengan openapi-typescript7.13.0. Schema hasil/metric/visual pada schemas/. Perbarui setelah endpoint atau model berubah:

```powershell
backend/.venv/Scripts/python.exe -m backend.publish_contracts
npx --yes openapi-typescript@7.13.0 contracts/openapi.json -o contracts/api.d.ts
```

Fixtures Taiwan berasal run nyata dalam tes; fixture PCA/EFA/clustering sintetis memakai synthetic:true. Untuk frontend, payload fixture sintetis pada property result; response API langsung berisi result tanpa wrapper synthetic. Jangan merender synthetic sebagai hasil user. demo-session.json berisi ID proyek/run/snapshot yang sudah ada di server lokal (tidak portabel ke database baru).

Tambahan dari brief: GET /drafts/{id}, GET /projects/{id}/runs, PATCH /datasets/{id}/columns. Role mapping membuat versi dataset baru. Profil/impor/dokumen mengembalikan hasil langsung, tanpa profile/parsing job ID. Export dan statistik punya jobs; statistik mendukung cancel. API aktual belum menyediakan free-form filter atau AI free-form essay. PDF memakai ReportLab dan mengikuti bagian/urutan snapshot. GET /runs/{id}/presentation menyediakan bagian materi terverifikasi; POST snapshot mengesahkan kembali ID content terhadap run yang dipilih. Observasi PCA/EFA mengembalikan scores; clustering mengembalikan cluster 1..K, sama dengan tabel pada run baru. Baca backend/README.md sebelum membangun interaksi yang menganggap semua fitur brief sudah tersedia.

Endpoint health mengembalikan session_token ephemeral; simpan di memori dan kirim X-Session-Token pada mutation request browser. Ini token sesi localhost, bukan secret AI. Setelah server restart ambil ulang token. Kunci API AI hanya server environment.
