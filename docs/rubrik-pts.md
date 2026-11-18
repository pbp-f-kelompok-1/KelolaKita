# Audit rubrik PTS KelolaKita

Audit lokal 18 November 2026. Rubrik bersumber dari lampiran penilaian kelompok
(30%), individu (70%), dan aturan khusus per anggota. Bukti penilaian difokuskan
pada perilaku aplikasi, histori Git yang tersedia, dan modul Edukasi milik Glenn.

## Penilaian kelompok

| Komponen | Bobot | Bukti | Gap menuju nilai 4 |
|---|---:|---|---|
| Design System | 25% | Figma Web/Desktop/Tablet/Mobile, template bersama, token Forest, Tailwind, fokus keyboard, dan pengecekan empat viewport. | Audit screen reader dan lintas browser belum dilakukan. |
| External Data / Public API | 15% | Nominatim untuk geocoding, OpenStreetMap/Leaflet untuk peta, data direktori dari basis data. Tes cache server 24 jam, normalisasi query, dan respons 503 saat provider gagal lulus. Peta tetap memiliki daftar lokasi dari database saat geocoding gagal. | Uji Nominatim menggunakan respons terkontrol. SLA dan operasi produksi belum diverifikasi. |
| Collaboration & Git Flow | 30% | Ref lokal menunjukkan branch modul tiap anggota, conventional commits, dan merge PR, termasuk #18–20. | Status review wajib, AI review di PR, branch protection, dan seluruh checkpoint perlu bukti dari tim/platform. |
| Integration & Deployment | 25% | Django MTV terintegrasi, main routes dan otorisasi diuji. Konfigurasi SQLite lokal berbeda dari PostgreSQL PWS. Workflow CI memeriksa aplikasi, migrasi, dan tes. | CI remote serta CD belum berjalan pada perubahan ini. PWS mengembalikan `certificate has expired` saat pemeriksaan HTTPS. Kesiapan produksi perlu dicek setelah TLS pulih. |
| Documentation & AI Disclosure | 5% | README memuat setup, anggota, modul, sumber data sintetis, peran, tautan Figma/PWS, tangkapan layar demo, strategi prompt, keterbatasan AI, dan langkah QC. | Persetujuan akhir dokumentasi tetap mengikuti review tim. |

Pemeriksaan konfigurasi deploy juga menemukan secret bawaan dan pengaturan HTTPS
serta cookie yang perlu ditinjau sebelum rilis. Verifikasi konfigurasi reverse
proxy dan variabel produksi harus memakai environment PWS.

## Penilaian individu

| Komponen | Bobot | Bukti untuk Edukasi | Gap menuju nilai 4 |
|---|---:|---|---|
| CRUD Module Implementation | 35% | Create, read, update, delete untuk artikel, agenda, dan penyaluran. Validasi sampul, tanggal, dan tujuan penyaluran, filter pencarian/kategori yang bisa dibagikan, serta CRUD Pengelola. | Nilai atas kemampuan refactoring dan pengembangan lanjutan perlu penilaian dosen. |
| Web Interactivity & Responsiveness | 10% | AJAX untuk filter artikel, create/update dengan validasi inline, dan delete dari dashboard. Form biasa tersedia sebagai fallback. Layout Forest dipakai pada halaman publik dan kelola. | Dashboard deletion memuat ulang untuk merender empty state setelah item terakhir dihapus. HTMX dan optimistic update penuh belum diterapkan. |
| Security Awareness | 10% | Staff aktif diwajibkan untuk mutasi, POST dilindungi CSRF, draft tidak muncul di publik, media artikel memakai kontrol visibilitas, dan template 403 menjelaskan penolakan. | Rate limiting sensitif dan hardening produksi belum diaudit menyeluruh. |
| Testing & Coverage | 10% | 254 tes lulus. Line execution Edukasi 97,1% pada model, view, dan form. Termasuk regresi AJAX, unggahan, filter, validasi, serta otorisasi. | Riwayat Red–Green–Refactor wajib ditunjukkan melalui Git untuk klaim TDD. |
| Git Contribution & Code Ownership | 10% | `7229833` AJAX dan akses staf, `d557a68` import berulang, `e52bc82` unggah artikel, `22b688b` Beranda responsif, dan `5756fa5` dokumentasi Edukasi. | Bukti review pekerjaan rekan dan seluruh checkpoint perlu dikonfirmasi dari PR/pengumpulan. |
| Demo & Live Coding | 25% | Dataset dan skrip demo tersedia. Alur demo disarankan melalui filter artikel, validasi form, serta akses staf versus warga. | Penilaian bergantung pada performa demo dan live coding saat sesi berlangsung. |

### Cakupan aturan per anggota

| Modul | CRUD, akses, dan filter yang terverifikasi | Interaktivitas yang tersedia |
|---|---|---|
| Akun / Profil | Registrasi, profil sendiri, edit profil, dan delete oleh petugas berizin via Django Admin. Data profil dibatasi ke pemilik. | Update profil AJAX. |
| Pengajuan | Create, lihat milik sendiri, edit/hapus sesuai status dan peran, pemeriksaan oleh pengelola. Filter kategori diproses pada queryset yang sudah dibatasi pemilik. | Pratinjau unggah sisi klien. Submit dan filter memakai navigasi normal. |
| Lokasi | Direktori publik, pencarian dari data tersimpan, dan create/update/delete khusus staf. Lokasi terpakai dilindungi dari penghapusan. | Peta, pencarian, dan geocoding AJAX. Form mutasi memakai navigasi normal. |
| Jadwal | Buat, riwayat, edit, dan batalkan sesuai kepemilikan, tanggal, kuota, dan cutoff. Riwayat dapat difilter. | Buat jadwal, filter status, dan pembatalan AJAX. Edit memakai submit normal. |
| Edukasi | Model, view, template responsif, form dan CRUD untuk tiga entitas. Visibilitas publik dan akses kelola terpisah. | AJAX filter artikel, create, update, dan delete dashboard. |

## QC lokal

| Area | Baris dieksekusi | Cakupan |
|---|---:|---:|
| Accounts | 236/242 | 97,5% |
| Pengajuan | 179/197 | 90,9% |
| Lokasi | 216/235 | 91,9% |
| Jadwal | 390/410 | 95,1% |
| Edukasi | 464/478 | 97,1% |

Cakupan dihitung dengan tracer standar Python pada executable lines dalam model,
view dan form terkait. Pengukuran ini adalah line execution dan tidak mengukur
branch coverage. `manage.py check`, `makemigrations --check --dry-run`,
`tailwind build`, dan 254 tes Django lulus.

Seed SQLite lokal dan database QA memuat 50 akun/profil, lokasi, jadwal, artikel,
agenda, dan penyaluran. Selain 50 pengajuan terjadwal, ada satu pengajuan tambahan
yang siap dipilih di form Jadwal. Seeder diuji ulang tanpa menambah duplikat pada
fixture yang sama. Data demonstrasi diberi penanda dan hanya disiapkan di SQLite
pengembangan. Smoke test 12 halaman memeriksa route, jumlah data, relasi, kuota,
foto contoh, dan penolakan terhadap akses warga ke panel staf.

Chromium memeriksa 12 halaman pada 1440, 768, 390, dan 320 px. Seluruh
48 kombinasi bebas overflow horizontal. Daftar Penyaluran memuat 51 baris
(50 seed dan satu baseline QA) pada tiap viewport. Pengiriman AJAX di
browser menampilkan error lalu state sukses tanpa navigasi. Browser menerima
respons yang dirender Django dari basis data QA melalui routing Playwright.
Akun demo juga berhasil diautentikasi di database lokal. Perbandingan dengan
salinan SQLite pra-seed memastikan record lama di semua tabel seed tetap utuh.
