# Modul Education KelolaKita

Dokumentasi ini menjelaskan implementasi **Education / Edukasi** yang ada di repository
KelolaKita pada branch `main`. Tujuannya bukan menggambarkan aplikasi ideal, melainkan
membantu mahasiswa memahami kode yang benar-benar dipakai saat demo PTS.

## Tujuan modul

Modul Education mengelola konten edukasi dan bukti kegiatan komunitas:

- Artikel edukasi yang bisa berupa draf, terjadwal, atau terbit.
- Agenda komunitas dengan lokasi dan rentang waktu.
- Catatan barang yang sudah disalurkan ke panti asuhan/komunitas.
- Halaman publik yang hanya menampilkan konten yang layak terbit.
- Dashboard staff untuk CRUD ketiga jenis konten tersebut.
- Endpoint gambar artikel yang hanya menyajikan cover yang terdaftar di database.

## Fitur utama

| Fitur | Status implementasi |
|---|---|
| CRUD artikel staff | Ada: create, edit, delete, preview gambar, publish/draft |
| Upload/ganti/hapus gambar artikel | Ada, memakai `ImageField` + validasi Pillow |
| Artikel publik | Ada: homepage, list, detail; draft/terjadwal tidak tampil |
| Agenda komunitas | Ada: CRUD staff, list/detail publik |
| Catatan penyaluran | Ada: CRUD staff, halaman publik penyaluran |
| Relasi lokasi | Ada: `Event.location` dan `Distribution.destination` memakai `PROTECT` |
| Dashboard staff | Ada di `/edukasi/kelola/` |
| Pencarian/filter artikel | Ada: `q` dan `category` melalui GET + partial AJAX |
| AJAX/HTMX | AJAX `fetch` untuk filter artikel dan hapus dashboard; HTMX tidak dipakai; create/update masih full-page |
| Produk guna ulang | Konten static/template, bukan model database |
| Import konten PWS | Ada management command, bukan bagian request web |

## Batasan modul

- Otorisasi staff bersifat **group-level**: semua user `is_staff` dapat mengelola semua
  artikel/agenda/distribusi. Belum ada ownership per penulis.
- Tidak ada audit log, rate limiting, soft delete, atau bulk action.
- Penghapusan artikel tidak otomatis menghapus file gambar dari storage; file lama dapat
  menjadi orphan. Ini bukan bug yang memblokir CRUD, tetapi perlu diketahui saat demo.
- Media lokal bergantung pada filesystem dan tidak ikut Git. Persistensi media di PWS
  belum diverifikasi.
- Produk guna ulang di halaman publik adalah static content, bukan record database.

## Relasi dengan app lain

- `Location` menyediakan panti asuhan, komunitas, bank sampah, koordinat, dan detail
  lokasi. Education memakai `Location` untuk agenda dan tujuan penyaluran.
- `ProjectKelolaKita` menyediakan URL root, template `base.html`, static CSS, login
  admin, dan middleware.
- Modul lain (homepage, peta, jadwal) tidak diubah oleh dokumentasi ini.

## Menjalankan aplikasi

Dari root repository:

```bash
source env/bin/activate
python manage.py migrate
python manage.py runserver
```

Buka `http://127.0.0.1:8000/edukasi/`.

Untuk dashboard staff, siapkan akun staff lokal sendiri (jangan memakai kredensial
production), misalnya lewat:

```bash
python manage.py createsuperuser
```

Login melalui `/accounts/login/` lalu buka `http://127.0.0.1:8000/edukasi/kelola/`.

## URL utama

| URL name | Path | Akses |
|---|---|---|
| `education_home` | `/edukasi/` | Publik |
| `article_list` | `/edukasi/artikel/` | Publik |
| `article_detail` | `/edukasi/artikel/<slug>/` | Publik untuk artikel terbit |
| `event_list` | `/edukasi/agenda/` | Publik |
| `event_detail` | `/edukasi/agenda/<pk>/` | Publik |
| `distribution_list` | `/edukasi/penyaluran/` | Publik |
| `education_manage` | `/edukasi/kelola/` | Staff aktif |
| `article_create` | `/edukasi/kelola/artikel/tambah/` | Staff aktif |
| `article_update` | `/edukasi/kelola/artikel/<pk>/ubah/` | Staff aktif |
| `article_delete` | `/edukasi/kelola/artikel/<pk>/hapus/` | Staff aktif |
| `event_create/update/delete` | `/edukasi/kelola/agenda/...` | Staff aktif |
| `distribution_create/update/delete` | `/edukasi/kelola/penyaluran/...` | Staff aktif |

## Struktur file

```text
education/
├── models.py                 # Article, Event, Distribution, validasi gambar
├── forms.py                  # ArticleForm, EventForm, DistributionForm
├── views.py                  # halaman publik, CRUD staff, endpoint media
├── urls.py                   # route Education
├── tests.py                  # model, form, CRUD, authorization, media
├── tests_import.py           # test management command import PWS
└── management/commands/
    ├── import_pws_public_content.py
    └── pws_public_content.json

templates/education/
├── public_home.html
├── public_article_list.html
├── public_article_detail.html
├── public_event_list.html
├── public_event_detail.html
├── public_distribution_list.html
├── manage_list.html
├── manage_form.html
└── manage_confirm_delete.html

static/css/education.css     # styling publik + dashboard
static/js/education.js       # progressive reveal, bukan CRUD
```

## Menjalankan tes

```bash
python manage.py check
python manage.py test education
python manage.py test
python manage.py makemigrations --check --dry-run
git diff --check
```

Detail kelompok tes dan gap coverage ada di [testing-guide.md](testing-guide.md).

## Dokumentasi lanjutan

- [glossary.md](glossary.md) — istilah teknis dan artinya dalam konteks KelolaKita.
- [architecture.md](architecture.md) — model, relasi, dan alur request.
- [code-walkthrough.md](code-walkthrough.md) — penjelasan per file/fungsi untuk demo.
- [crud-reference.md](crud-reference.md) — matriks CRUD dan URL.
- [security-and-validation.md](security-and-validation.md) — authorization, CSRF, validasi.
- [testing-guide.md](testing-guide.md) — cara menjalankan dan membaca tes.
- [demo-script.md](demo-script.md) — skenario demo 15 menit.
- [live-coding-playbook.md](live-coding-playbook.md) — latihan live coding.
- [troubleshooting.md](troubleshooting.md) — masalah umum.
- [rubric-gap-analysis.md](rubric-gap-analysis.md) — kondisi vs rubrik PTS.
- [quick-demo-cheatsheet.md](quick-demo-cheatsheet.md) — ringkasan sebelum demo.
