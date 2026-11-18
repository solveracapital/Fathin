# Frontend Multivariat Lab

React19 + TypeScript + Vite6, React Router7, TanStack Query5, Radix Dialog, Lucide, Plotly basic, KaTeX dan Source Sans3 lokal. Versi tepat pada package-lock.json. CSS memakai token dari brief, tanpa framework CSS tambahan karena komponen dan kebutuhan layout sudah terdefinisi.

Dev: `npm run dev --prefix frontend`; build: `npm run build --prefix frontend`. Proxy /api menuju127.0.0.1:8000; Vite di127.0.0.1:5173. Tidak memakai fixture sebagai hasil user. `contracts/api.d.ts` adalah tipe generated; bagian response yang belum memiliki field schema detail dipetakan ke record dinamis pada api.ts.

Implementasi: beranda proyek, impor CSV/XLSX, pemetaan peran/versi data, wizard empat langkah dengan autosave draft, status dan pembatalan, hasil/diagnostik/rumus/observasi, skenario, ekspor, dokumen dan sumber, assistant berbasis bukti, editor urutan presentasi, snapshot dan cache IndexedDB, navigasi mobile. Preview tabel dan hasil memakai pagination server. Query key mengikat run dan subset; response lama dari slider dibatalkan/diabaikan.

Semua statistik berasal server. Browser hanya memformat angka dan merender koordinat/persentase presentasional. Slider bukan optimizer test; skenario diberi label eksplorasi. Angka tidak tersedia tidak diubah menjadi nol. Kelas dan ID menjaga tipe sumber; API key AI tidak disimpan browser.

Fonts berasal paket @fontsource/source-sans-3 (SIL OFL), matematika KaTeX(MIT), ikon Lucide(ISC), Plotly(MIT). Lisensi paket ada pada node_modules masing-masing. Tidak ada aset raster generatif, CDN font, atau gambar dekoratif.

Plotly dan KaTeX dimuat ketika diperlukan. Bundle grafik besar masih memunculkan warning ukuran Vite, tetapi terpisah dari muatan halaman awal. Tidak menyembunyikan warning dengan menaikkan ambang konfigurasi. Grafik punya alternatif data, batas proyeksi/sampling, label sumbu dan subset. Canvas plot tidak menggantikan ringkasan angka untuk aksesibilitas.

Pengujian E2E: server nyata, contoh makalah dihitung ulang sebelum tes. Tidak ada mock backend atau angka hardcode untuk menggantikan hasil. Report otomatis pada test-results/report.json, screenshot pada test-results/screenshots. Detail pada TEST_REPORT.md.
