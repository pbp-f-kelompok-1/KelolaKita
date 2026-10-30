# Pemecahan Masalah — Education

Gunakan gejala → verifikasi → solusi aman. Jangan memakai `git reset --hard`,
`git clean -fd`, atau menghapus database/media tanpa izin.

## Server tidak mau jalan

**Gejala:** `Address already in use` atau server langsung berhenti.

**Verifikasi:**

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
python manage.py check
```

**Solusi:** jika port dipakai server Django repo yang sama, gunakan port lain:

```bash
python manage.py runserver 127.0.0.1:8001
```

Jangan membunuh proses yang tidak dikenal. Jika proses adalah repo lain, cari cwd/command
sebelum mengambil tindakan.

## Migration belum diterapkan

**Gejala:** error tabel/kolom tidak ada.

**Verifikasi:**

```bash
python manage.py showmigrations education
python manage.py makemigrations --check --dry-run
```

**Solusi:** `python manage.py migrate`. Jangan membuat migration baru jika tidak ada
perubahan model. Jangan reset database untuk masalah migration biasa.

## Template tidak ditemukan

**Gejala:** `TemplateDoesNotExist: education/...`.

**Verifikasi:** pastikan file ada di `templates/education/` dan
`TEMPLATES["DIRS"]` di `ProjectKelolaKita/settings.py` menunjuk `BASE_DIR / "templates"`.
Cek nama template di view.

## Static file 404

**Gejala:** CSS/JS tidak termuat atau warning `No directory at .../staticfiles/`.

**Verifikasi:**

```bash
python manage.py findstatic css/education.css
curl -I http://127.0.0.1:8000/static/css/education.css
```

**Solusi:** untuk development, staticfiles/WhiteNoise dengan `DEBUG=True` dan
`WHITENOISE_USE_FINDERS=True`; pastikan `STATICFILES_DIRS` benar. Warning `staticfiles/`
tidak selalu fatal jika file ditemukan lewat finders. Jangan mengubah `MEDIA_ROOT`
menjadi static directory.

## Gambar artikel 404

**Gejala:** cover tampil sebagai placeholder atau `/media/...` 404.

**Verifikasi:**

```bash
python manage.py shell -c "from education.models import Article; a=Article.objects.first(); print(a.image.name, a.image_available)"
```

Cek:

1. `Article.image` tidak kosong;
2. file ada di `MEDIA_ROOT`;
3. artikel published untuk akses publik;
4. request melewati `article_image` (bukan web server yang menyajikan `/media/` langsung);
5. MIME file termasuk JPEG/PNG/WebP.

**Solusi:** unggah ulang gambar lewat form staff. Jangan menambahkan route blanket
`/media/` ke seluruh `MEDIA_ROOT`.

## Gambar draft terlihat publik

**Gejala:** URL `/media/...` untuk artikel draf mengembalikan 200 tanpa login.

**Verifikasi:** cek `article_image` masih memakai `articles.published().exists()` dan
tidak ada route media lain yang lebih awal menangkap `/media/`. Cek urutan
`ProjectKelolaKita/urls.py` dan konfigurasi proxy PWS.

**Solusi:** perbaiki route/endpoint; jangan hanya menyembunyikan gambar di CSS.

## Form tidak lolos validasi

**Gejala:** POST mengembalikan 200 dan error field.

**Solusi:** baca `form.errors`/error di template. Untuk gambar, cek ukuran, format,
dimensi. Untuk agenda, cek end >= start. Untuk distribusi, cek tujuan panti/komunitas
dan tanggal `delivered`. Jangan menambahkan `novalidate` atau menghapus validator untuk
“memperbaiki” form.

## 403 pada dashboard

**Gejala:** user login tetapi mendapat 403.

**Verifikasi:**

```bash
python manage.py shell -c "from django.contrib.auth.models import User; print(list(User.objects.filter(username='USER').values('is_staff','is_active')))"
```

**Solusi:** gunakan akun staff aktif. Jangan mengubah `is_staff` user lain atau
melonggarkan `StaffRequiredMixin`.

## Pengguna anonymous malah redirect, bukan 403

Itu perilaku yang benar: `LoginRequiredMixin` mengarahkan anonymous ke login.
Non-staff yang sudah login baru mendapat 403.

## 404 pada edit/delete

**Penyebab:** PK tidak ada, sudah dihapus, atau URL salah.

**Verifikasi:** cek `Article.objects.filter(pk=...).exists()`; cek route name dan
argumen. Jangan membuat view yang menelan `DoesNotExist` lalu menampilkan halaman sukses.

## Tes gagal karena database test

**Gejala:** `database is locked`, migration error, atau data test tidak terlihat.

**Solusi:**

- Pastikan tidak ada `runserver` yang memakai database test;
- jalankan `python manage.py test education`;
- jangan memakai `db.sqlite3` di tes;
- jika proses sebelumnya crash, hentikan proses test yang masih hidup (setelah
  diidentifikasi), bukan menghapus database pengguna.

## Tes gambar gagal

Tes image memakai `override_settings(MEDIA_ROOT=tempdir)`. Jika file tidak ditemukan,
pastikan helper `make_image_upload` dipakai dan cleanup `shutil.rmtree` tidak berjalan
sebelum assertion. Jangan mengarahkan tes ke folder `media/` pengguna.

## Import PWS gagal/duplikat

**Verifikasi:**

```bash
python manage.py import_pws_public_content --dry-run
```

- Baca output `created/updated/unchanged/conflicts`.
- Jangan langsung menjalankan import jika ada conflict.
- Periksa alias lokal pada manifest.
- Jangan menghapus data lokal yang tidak ada di source; command hanya melaporkan stale.

## Konflik Git / perubahan lokal

**Gejala:** `git status` kotor sebelum demo.

**Solusi:** lihat `git diff`, pisahkan file Education dari perubahan lain, backup patch
ke luar repo, dan jangan memakai reset/clean. Untuk demo, gunakan working tree yang
sudah diuji; jangan commit/push tanpa instruksi.

## Browser menampilkan CSS lama

**Gejala:** source CSS berubah tetapi browser masih layout lama.

**Verifikasi:** cek URL `education.css?v=...` di HTML, hard reload, atau bandingkan
response server dengan file disk.

**Solusi:** naikkan versi query pada template jika memang mengubah CSS; jangan
menghapus cache pengguna secara global. Jangan menganggap tes Python membuktikan CSS
sudah termuat.
