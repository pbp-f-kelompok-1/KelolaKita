# Analisis Kesenjangan Rubrik — Education

Analisis ini memakai sumber aktual dan tes lokal. Tidak ada skor atau coverage yang
dikarang. Rubrik penuh ada di brief PTS; tabel ini hanya memetakan kondisi.

## Ringkasan 7 Aturan Khusus setelah implementasi

| Aturan | Status | Catatan |
|---|---|---|
| 1. Models | TERPENUHI | Article, Event, Distribution, relasi Location. |
| 2. Views & CRUD | TERPENUHI | CRUD melalui aplikasi, bukan Django Admin. |
| 3. HTML & Responsive CSS Framework | TERPENUHI | Tailwind dimuat; Education memakai CSS custom responsif. |
| 4. Forms | TERPENUHI | ModelForm, validasi, upload gambar, CSRF. |
| 5. AJAX/HTMX | TERPENUHI (parsial kualitas) | Fetch untuk filter dan async delete; create/update belum async, HTMX tidak dipakai. |
| 6. Authentication-based Filtering | TERPENUHI | Publik Read; staff aktif Create/Update/Delete. |
| 7. Database Filtering | TERPENUHI | QuerySet internal + filter user `q`/`category`; dashboard filter opsional belum ada. |

## Ringkasan kondisi

| Komponen | Bobot | Kondisi awal | Bukti | Gap / perbaikan | Kondisi akhir |
|---|---:|---|---|---|---|
| CRUD Module Implementation | 35% | Create/read/update/delete artikel, agenda, distribusi berjalan; validasi model/form; upload gambar | `education/views.py`, `forms.py`, `models.py`, `tests.py`; 199 tes total (lihat laporan) | Tidak ada bulk/soft-delete; delete gambar tidak menghapus file orphan; tetap dianggap gap, bukan fitur wajib | CRUD lengkap dengan validasi, error form, authorization, image handling |
| Web Interactivity & Responsiveness | 10% | Form create/update full-page; filter artikel memakai AJAX partial; delete dashboard memakai fetch; CSS responsif | `static/js/education.js`, `_article_results.html`, tests | Tidak semua CRUD asynchronous; tidak ada HTMX/optimistic UI; create/update tetap full-page | Level 3: ada AJAX bermakna pada filter dan delete, belum konsisten di seluruh CRUD |
| Security Awareness | 10% | Staff-only mixin, active staff check, CSRF, form/model validation, media endpoint sempit | `StaffRequiredMixin`, `article_image`, tests | Tidak ada object ownership, rate limit, audit log; semua staff setara | Kontrol server-side lebih ketat; batasan didokumentasikan |
| Testing & Coverage | 10% | Banyak unit/regression tests; image edge cases; import tests; filter/async tests | `education/tests.py`, `tests_import.py`; 199 total | `coverage` tidak terpasang; tidak ada Selenium; tidak ada angka coverage | Tes ditambah untuk filter, async delete, inactive staff, direct POST non-staff, missing record, delivered date form; coverage tetap belum diukur |
| Git Contribution & Code Ownership | 10% | Branch `main`; repository memiliki commit fitur Education; agen tidak commit | `git log`, status working tree | Penilaian history/checkpoint tidak dapat dilakukan dari kode saja | Tidak ada commit/push dari agen; pemilik harus menyiapkan riwayat sendiri |
| Demo & Live Coding | 25% | Modul dapat didemokan; alur kode dan tantangan belum terdokumentasi | README, architecture, walkthrough, demo script, playbook | Keberhasilan bergantung latihan mahasiswa; belum diuji sebagai presentasi nyata | Dokumentasi dan latihan tersedia; belum ada jaminan performa demo |

## Bukti per komponen

### CRUD

Implementasi:

- `ManageCreateView`, `ManageUpdateView`, `ManageDeleteView`.
- `ArticleForm`, `EventForm`, `DistributionForm`.
- `Article`, `Event`, `Distribution` dengan validator/`clean()`.
- `messages.success` setelah sukses.

Gap yang tidak disembunyikan:

- Tidak ada soft delete/bulk operations.
- Delete artikel tidak menghapus file cover otomatis.
- Tidak ada versioning/audit.

### Interaktivitas

Yang ada:

- `static/js/education.js` untuk progressive reveal.
- Filter artikel asynchronous dengan Fetch API dan partial HTML.
- Async delete dashboard dengan fetch, CSRF, dan fallback konfirmasi.
- `manage_form.html` untuk sinkronisasi upload vs clear image.
- Form create/update tetap HTML biasa; POST/redirect/GET.

Yang belum:

- HTMX.
- Async create/update untuk seluruh entitas.
- Optimistic UI.
- Automated browser suite untuk seluruh alur.

Saat demo, sebut ini sebagai AJAX/fetch parsial, bukan “full AJAX/HTMX”.

### Keamanan

Kontrol:

- `StaffRequiredMixin` memeriksa login, `is_active`, `is_staff`.
- Non-staff direct POST ditolak; tes baru mencakup ini.
- CSRF pada semua form.
- Public queryset menyaring draft/terjadwal.
- Gambar hanya dari `Article.image` yang terdaftar; path traversal ditolak.
- Image validator memeriksa ukuran, format, dimensi.

Batasan:

- Staff adalah role kelompok, bukan pemilik objek.
- Tidak ada rate limit.
- Tidak ada audit log.
- File media tidak dipindai malware.
- Media endpoint masih Django streaming; persistensi PWS belum terverifikasi.

### Pengujian

Angka aktual harus diambil dari output final, bukan diasumsikan. Setelah implementasi
filter dan async delete, suite aktual adalah **103 tes Education** dan **199 tes total**.
Verifikasi dengan command di `testing-guide.md`.

Gap:

- `coverage` belum terpasang; tidak ada persentase.
- Belum ada Selenium/Playwright test.
- Beberapa transisi status distribusi belum diuji terpisah.

### Git

Agen tidak melakukan commit/push/merge. Working tree berisi perubahan dokumentasi dan
kode yang harus ditinjau pemilik. Riwayat kontribusi/checkpoint tidak dapat dinilai
hanya dari working tree.

### Demo

Dokumentasi menyediakan:

- `demo-script.md` (15 menit).
- `live-coding-playbook.md` (level 1–3).
- `quick-demo-cheatsheet.md` (20 pertanyaan + checklist).

Yang belum:

- Latihan lisan nyata.
- Pengukuran waktu presentasi.
- Rekaman demo.

## Perubahan yang dibuat dalam audit ini

1. `StaffRequiredMixin.test_func` juga memeriksa `is_active` agar staff inactive tidak
   dianggap authorized.
2. Redirect staff memakai `accounts:login`, bukan `admin:login`.
3. Filter artikel berbasis ORM (`q`, `category`) dengan fallback GET dan partial AJAX.
4. Async delete dashboard dengan Fetch API, CSRF, JSON response, dan fallback
   konfirmasi biasa.
5. Tes filter, async delete, inactive staff, direct POST non-staff, missing record,
   dan `delivered` tanpa tanggal.
6. Dokumentasi dan playbook live coding diperbarui.

Perubahan tidak menambah dependency eksternal, tidak mengubah schema, dan tidak
mengubah kebijakan permission publik.
