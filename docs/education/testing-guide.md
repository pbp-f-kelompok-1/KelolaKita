# Panduan Pengujian — Education

## 1. Command dasar

Dari root repository:

```bash
source env/bin/activate
python manage.py check
python manage.py test education
python manage.py test
python manage.py makemigrations --check --dry-run
git diff --check
```

Tes memakai database test sementara; data `db.sqlite3` tidak diubah. Hasil terakhir
pada audit implementasi: **103 tes Education** dan **197 tes total**.

## 2. Menjalankan satu kelas/metode

```bash
python manage.py test education.tests.ManagementAccessTests
python manage.py test education.tests.CrudTests.test_article_create_update_and_post_only_delete
python manage.py test education.tests.ArticleImageTests
python manage.py test education.tests.ArticleFilterTests
python manage.py test education.tests_import
```

## 3. Kelompok tes penting

### `ArticleModelTests`

- slug otomatis, unik, stabil saat judul berubah;
- default draf;
- `published()` mengecualikan draf dan artikel terjadwal.

### `ArticleImageTests`

Memakai `override_settings(MEDIA_ROOT=tempdir)`, sehingga file uji tidak masuk ke
`media/` proyek.

Menguji:

- format JPEG/PNG/WebP valid;
- file terlalu besar, terlalu kecil, bukan gambar, atau ekstensi salah;
- create menyimpan file ke storage;
- edit tanpa upload mempertahankan gambar;
- replace/clear gambar;
- upload + clear bersamaan tidak menghilangkan gambar lama;
- response media untuk artikel terbit;
- draft/terjadwal hanya untuk staff;
- file tidak terdaftar, file hilang, traversal, dan artikel terhapus → 404;
- placeholder untuk artikel tanpa gambar.

### `EventModelTests` dan `DistributionModelTests`

Menguji validasi model dan constraint database:

- end sebelum start ditolak;
- quantity minimal 1;
- tujuan penyaluran bukan bank sampah;
- `delivered` wajib tanggal;
- `PROTECT` mencegah lokasi dihapus.

### `FormTests`

Menguji validasi form dan queryset:

- form artikel valid dan label kategori publik;
- judul kosong ditolak;
- event end < start ditolak;
- distribusi ke bank sampah ditolak;
- `delivered` tanpa tanggal ditolak;
- lokasi/tujuan nonaktif tetap tersedia saat edit.

### `ArticleFilterTests`

- pencarian judul case-insensitive;
- kategori valid/tidak valid;
- kombinasi query + kategori;
- draft dan artikel terjadwal tetap tersembunyi;
- empty state;
- response AJAX hanya partial `_article_results.html`.

### `ManagementAccessTests`

- anonymous → redirect login;
- non-staff GET management → 403;
- inactive staff tidak mendapat akses;
- non-staff direct POST ke create/update/delete → 403;
- staff missing record → 404;
- staff dapat membuka dashboard/form.

### `CrudTests`

- create/update artikel;
- delete hanya lewat POST;
- create event dan distribution;
- invalid form tidak menulis;
- CSRF delete wajib;
- async delete mengembalikan JSON dan menghapus record.

### `PublicPagesTests` dan `PublicDistributionTests`

- artikel/agenda publik yang benar;
- draft/terjadwal tidak tampil;
- partner aktif saja;
- empty state;
- statistik distribusi;
- tanggal ISO;
- URL publik tidak membuka management.

### `PwsImportTests`

Tidak melakukan request jaringan. Menguji:

- dry-run tidak menulis;
- import idempotent;
- relasi agenda/lokasi dan distribusi/tujuan;
- alias record lokal diperbarui tanpa duplikat;
- manifest invalid membatalkan seluruh transaksi;
- konten hasil import tampil di route publik.

## 4. Fixture dan media

Helper ada di bagian atas `education/tests.py`:

- `make_image_upload`: membuat gambar Pillow kecil di memori.
- `make_article`, `make_event`, `make_distribution`, `make_location`: data konsisten.
- `override_settings(MEDIA_ROOT=tempdir)` untuk tes file.

Jangan memakai file di folder `media/` pengguna untuk tes.

## 5. Membaca kegagalan

Contoh:

```text
FAIL: test_non_staff_cannot_post_mutations
AssertionError: 302 != 403
```

Langkah:

1. Baca nama tes dan assertion.
2. Cek status/response saat ini.
3. Cek apakah user yang dipakai benar-benar staff aktif.
4. Cek urutan URL/redirect; login redirect bisa terjadi sebelum authorization.
5. Perbaiki kode atau fixture, bukan assertion yang valid.

Jangan menghapus assertion atau menambahkan `skip` hanya agar hijau.

## 6. Coverage

Saat audit ini, package `coverage` **tidak terpasang** di `env` dan tidak ada di
`requirements.txt`. Karena itu tidak ada angka coverage yang boleh diklaim.

Jika akan mengukur:

```bash
pip install coverage
coverage run --source=education manage.py test education
coverage report -m
```

Jangan menambahkan `coverage` ke requirements production tanpa keputusan tim. Untuk
demo, cukup jelaskan bahwa suite menguji model, form, view, authorization, media,
CRUD, dan import; angka coverage belum tersedia.

## 7. Celah yang masih ada

- Tidak ada Selenium/Playwright test otomatis di suite; browser diverifikasi manual.
- Tidak ada pengukuran coverage.
- Belum ada test untuk seluruh kombinasi status/transition distribusi.
- Belum ada test untuk semua endpoint delete event/distribution secara terpisah
  (mixin dan pola sama dengan artikel).
- Belum ada test browser/functional untuk filter async dan delete async.
- Belum ada load/concurrency test untuk upload dan slug.
- Create/update async belum diimplementasikan; belum ada test untuk alur tersebut.

Gap ini lebih baik disebutkan saat demo daripada mengklaim coverage 90% tanpa alat ukur.
