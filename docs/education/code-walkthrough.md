# Penjelasan Kode — Modul Education

Dokumen ini menunjuk file dan fungsi yang benar-benar ada. Buka file di IDE sambil
mengikuti urutan ini saat demo.

## 1. `education/models.py`

### `validate_article_image(image)`

**Tanggung jawab:** memvalidasi gambar sebelum disimpan.

Alurnya:

1. Menolak file lebih dari 5 MB.
2. Menolak ekstensi selain `.jpg`, `.jpeg`, `.png`, `.webp`.
3. Membuka file dengan Pillow untuk memastikan isinya benar-benar gambar, bukan file
   teks yang diberi ekstensi gambar.
4. Menolak format selain JPEG/PNG/WebP.
5. Menolak gambar di bawah 800 × 450 piksel.
6. `finally: image.seek(0)` mengembalikan pointer file agar Django dapat menyimpannya.

Validator ini dipasang pada field model **dan** pada `ArticleForm.image`, sehingga
validasi tetap berlaku baik dari form maupun pemanggilan model yang memakai validasi.

### `ArticleQuerySet.published()`

Mengembalikan hanya `is_published=True` dan `published_at <= timezone.now()`.
Ini adalah satu-satunya definisi "artikel publik" yang dipakai halaman publik.

### `Article.save()`

Jika `slug` kosong:

- slug dibuat dari `slugify(title)`;
- jika sudah dipakai, ditambahkan `-2`, `-3`, dan seterusnya;
- slug tidak diubah saat judul diedit, sehingga URL artikel yang sudah dibagikan tetap
  stabil.

Ada komentar `shortcut:` tentang loop slug yang belum concurrency-safe. Ini jujur:
dua request bersamaan dengan judul sama masih mungkin bertabrakan pada unique constraint.
Untuk skala proyek ini, loop sederhana cukup; upgrade path adalah menangani
`IntegrityError` atau memakai mekanisme sequence.

### `Article.image_available` dan `Article.cover`

- `image_available` memeriksa field image dan keberadaan file di storage.
- `cover` mengembalikan `{"src", "alt"}`.
- Jika file hilang, `cover` memakai placeholder static, bukan URL gambar rusak.
- Pemeriksaan `storage.exists()` dilakukan per akses; ini disengaja agar file yang
  dihapus tidak menghasilkan broken image. Biayanya satu stat filesystem per artikel.

### `Event.clean()`

Menolak `end_at < start_at`. Model juga memiliki `CheckConstraint` di database, jadi
aturan tetap ada meskipun ada kode yang memanggil `save()` tanpa `full_clean()`.
`Event.location` memakai `PROTECT`.

### `Distribution.clean()`

Mengumpulkan error untuk:

- tujuan selain panti asuhan/komunitas;
- status `delivered` tanpa `distributed_at`.

`quantity >= 1` dijaga validator dan constraint database.

## 2. `education/forms.py`

### `ArticleForm`

- `image` dideklarasikan ulang sebagai `forms.ImageField` agar membantu teks,
  `accept`, dan error message konsisten.
- `Meta.fields` menentukan field yang boleh diubah staff.
- `published_at` memakai input `datetime-local`.
- `__init__` mengganti label kategori menjadi label publik (`Guna ulang`,
  `Pengurangan sampah`).
- `ClearableFileInput` memberi checkbox hapus gambar.
- Form tidak memaksa semua artikel langsung terbit; `is_published` tetap dikontrol
  staff.

### `EventForm`

- Field: judul, deskripsi, mulai, selesai, lokasi, status terbit.
- `__init__` membatasi pilihan lokasi ke lokasi aktif, tetapi tetap menyertakan lokasi
  saat ini ketika mengedit record lama yang lokasinya sudah nonaktif.
- `ModelForm` memanggil `Event.clean()` sehingga validasi waktu tetap berjalan.

### `DistributionForm`

- `destination` dibatasi ke lokasi aktif dengan kategori panti/komunitas; record lama
  tetap bisa diedit meskipun lokasinya sekarang nonaktif.
- `ModelForm` memanggil `Distribution.clean()` untuk aturan status/tanggal.

## 3. `education/views.py`

### `published_events()` dan `public_distributions()`

Helper queryset untuk halaman publik.

- `published_events()`: event terbit + `select_related("location")`.
- `public_distributions()`: status `delivered`, tanggal tidak null dan tidak melewati
  tanggal Jakarta, tujuan panti/komunitas, `select_related("destination")`.

### `article_image(request, path)`

Endpoint media yang sempit.

1. Menolak path kosong, absolut, mengandung backslash/NUL, atau `..`.
2. Membentuk nama storage `education/articles/<path>`.
3. Mencari `Article` dengan nilai `image` yang sama persis.
4. Jika tidak ada record → 404.
5. Jika tidak ada artikel published dan requester bukan staff → 404.
6. Memastikan file ada dan MIME termasuk JPEG/PNG/WebP.
7. Mengembalikan `FileResponse` dengan `X-Content-Type-Options: nosniff`.
8. Cache publik 1 jam; preview staff `private, no-store`.

Yang penting saat menjelaskan: endpoint tidak membuka seluruh `MEDIA_ROOT`; file yang
tidak terhubung ke `Article.image` tidak dapat diakses melalui route ini.

### `public_home(request)`

Mengambil artikel published, memilih featured pertama, lalu mengirim:

- `featured`;
- `articles` (sisanya);
- `events` mendatang;
- `partners` aktif panti/komunitas;
- `distributions` publik terbaru (maksimal 5);
- `active_nav="edukasi"`.

### `PublicEducationContextMixin`

Menambahkan `active_nav` untuk semua public CBV.

### `ArticleListView` / `ArticleDetailView`

Keduanya memakai `Article.objects.published()`. Detail artikel draf/terjadwal akan 404,
bukan hanya disembunyikan di template.

### `EventListView` / `EventDetailView`

- List: event terbit dan start >= sekarang.
- Detail: event terbit; event yang sudah lewat tetap dapat dibuka.
- `published_events()` sudah memuat location dengan `select_related`.

### `DistributionListView`

Memakai queryset publik dan menambahkan aggregate:

- `total_records`;
- `total_quantity`;
- `total_destinations` (distinct).

### `StaffRequiredMixin`

`LoginRequiredMixin` + `UserPassesTestMixin`:

- anonymous → redirect login admin;
- authenticated non-staff → 403;
- staff inactive → tidak dapat mempertahankan akses (redirect login);
- `test_func` memeriksa `is_active and is_staff`.

Semua create/update/delete memakai mixin ini. Ini adalah kontrol server-side; tombol
yang disembunyikan di template bukan pengganti.

### `ManageDashboard`

Mengambil semua artikel, semua event + location, semua distribusi + destination.
Dashboard memang menampilkan draf dan data internal; karena itu staff-only.
`now` dikirim untuk menentukan label `Terjadwal`/`Selesai` di template.

### `ManageFormMixin`, `ManageCreateView`, `ManageUpdateView`

Menyatukan template, `success_url`, judul form, dan pesan sukses. Create/Update hanya
mengisi `model` dan `form_class`; validasi tetap milik form/model.

### `ManageDeleteView`

- GET menampilkan halaman konfirmasi.
- POST melakukan delete.
- `form_valid` mengirim pesan sukses.
- Tidak ada delete lewat GET; tombol memakai form POST + CSRF.

### `ArticleCreateView`, `ArticleUpdateView`, `ArticleDeleteView`

Mewarisi kelas generik di atas dengan model `Article` dan `ArticleForm`.

### `EventCreateView`, `EventUpdateView`, `EventDeleteView`

Sama, memakai `Event` dan `EventForm`.

### `DistributionCreateView`, `DistributionUpdateView`, `DistributionDeleteView`

Sama, memakai `Distribution` dan `DistributionForm`.

## 4. `education/urls.py`

Route publik dan staff dipetakan langsung ke view di atas. Nama route dipertahankan
karena dipakai template dan tes:

- `education_home`, `article_list`, `article_detail`;
- `event_list`, `event_detail`;
- `distribution_list`;
- `education_manage`, `article_create/update/delete`;
- `event_create/update/delete`;
- `distribution_create/update/delete`.

Route `/media/education/articles/<path>` dipasang di `ProjectKelolaKita/urls.py`
(level proyek), bukan di app, karena berada di prefix media global. View-nya tetap
`education.views.article_image`.

## 5. Template

### `public_home.html`

- Hero: artikel featured atau fallback statis.
- Panduan terbaru: `articles` (selain featured).
- Panel komunitas + agenda.
- Mitra penyaluran: data dari `Location`.
- Catatan penyaluran terbaru: data dari `Distribution` publik.
- Katalog produk: static template, bukan database.

### `public_article_list.html` dan `public_article_detail.html`

- List memakai `article.cover`; detail memakai `article.body|linebreaks`.
- `linebreaks` mengubah newline menjadi paragraf/`<br>`; teks tetap di-escape Django.

### `public_event_list.html` dan `public_event_detail.html`

- Menampilkan judul, lokasi, waktu mulai/selesai.
- Detail memakai `event.description`.
- Event yang sudah lewat tidak muncul di list, tetapi detail event terbit tetap bisa
  dibuka.

### `public_distribution_list.html`

- Statistik dari context `stats`.
- Hanya record yang sudah lolos `public_distributions()`.

### `manage_list.html`

- Dashboard artikel dengan thumbnail, status, aksi Ubah/Hapus.
- Agenda dengan date panel.
- Tabel penyaluran.
- Tidak menampilkan data palsu; semua dari queryset.

### `manage_form.html`

- `multipart/form-data` untuk gambar.
- Menampilkan error field dan error non-field.
- Preview gambar hanya jika `image_available`.
- Jika file hilang, menampilkan pesan, bukan broken image.
- JavaScript kecil memastikan checkbox clear dan upload baru tidak bertentangan.

### `manage_confirm_delete.html`

Konfirmasi delete dengan `csrf_token` dan tombol POST.

## 6. `static/js/education.js`

Hanya progressive enhancement untuk reveal section:

- jika browser tidak mendukung `IntersectionObserver`, tidak ada yang disembunyikan;
- jika `prefers-reduced-motion`, tidak ada animasi;
- fallback timeout menampilkan konten jika observer tidak berjalan.

Tidak ada fetch/CRUD asynchronous. Saat demo, jangan menyebut ini sebagai AJAX/HTMX.

## 7. Management command impor PWS

`education/management/commands/import_pws_public_content.py`

- Membaca manifest JSON.
- `--dry-run` tidak menulis database.
- `transaction.atomic()` membungkus seluruh import.
- Artikel dicocokkan lewat slug dan alias lokal (untuk migrasi data lama).
- Lokasi dicocokkan lewat nama.
- Event dicocokkan lewat judul/lokasi/start, dengan alias lokal.
- Distribusi dicocokkan lewat tujuan + tanggal.
- Gambar diverifikasi SHA-256; gambar yang hilang tidak diganti dengan file lain.
- Model yang tidak ada di source tidak dihapus; command melaporkan stale records.

## 8. Tes penting

- `education/tests.py` — model, form, CRUD, authorization, image, public pages.
- `education/tests_import.py` — dry-run, idempotensi, relasi, rollback, rendering.

Saat demo, tunjukkan satu positive path dan satu negative path. Contoh:

```bash
python manage.py test education.tests.ManagementAccessTests
python manage.py test education.tests.ArticleImageTests
```

Penjelasan hasil yang benar: tes memakai database test sementara dan `MEDIA_ROOT`
temporary untuk image; tidak menyentuh data lokal/PWS.
