# Demo Individu 15 Menit — Education

Dokumen ini adalah skenario latihan, bukan jaminan nilai. Sesuaikan dengan data lokal
yang sedang ada. Jangan memakai kredensial production atau mengubah data PWS.

## Persiapan 10 menit sebelum demo

- [ ] `source env/bin/activate`
- [ ] `python manage.py check`
- [ ] `python manage.py test education` (minimal kelompok yang relevan)
- [ ] `python manage.py runserver`
- [ ] Login staff lokal sudah siap (jangan menuliskan password di dokumen).
- [ ] Buka tab: `/edukasi/`, `/edukasi/kelola/`, satu detail artikel, `/locations/`.
- [ ] Buka IDE pada `education/models.py`, `forms.py`, `views.py`, `urls.py`.
- [ ] Siapkan satu artikel/agenda/distribusi sementara yang boleh dihapus setelah demo.
- [ ] Jangan memakai artikel seed PWS sebagai target delete.

Data lokal saat dokumentasi dibuat: 3 artikel, 2 lokasi, 1 agenda, 1 penyaluran.

## Alur waktu

| Waktu | Aktivitas | Bukti yang ditunjukkan |
|---|---|---|
| 00:00–01:00 | Konteks dan arsitektur | Buka README/architecture, sebut Django MVT |
| 01:00–03:00 | Halaman publik | `/edukasi/`, artikel, mitra, agenda, penyaluran |
| 03:00–06:00 | Artikel CRUD | Dashboard, form create draft, edit, delete sementara |
| 06:00–09:00 | Agenda dan penyaluran | Form create/edit, relasi lokasi, validasi tanggal |
| 09:00–11:00 | Code walkthrough | `models.py`, `forms.py`, `views.py`, `urls.py` |
| 11:00–12:30 | Security/validation | Non-staff 403, draft 404, CSRF, image validation |
| 12:30–15:00 | Live coding | Satu challenge level 1/2, jelaskan keputusan |

## 00:00–01:00 — Konteks

Ucapkan:

> Education mengelola artikel, agenda, dan catatan penyaluran. Publik hanya membaca
> konten yang sudah terbit; staff aktif memakai dashboard untuk CRUD. Saya memakai
> Django ModelForm dan generic CBV, dengan aturan bisnis di model.

Tunjukkan:

- `education/models.py`: `Article`, `Event`, `Distribution`.
- `education/views.py`: `StaffRequiredMixin`.
- `education/urls.py`: route publik dan staff.

## 01:00–03:00 — Halaman publik

Buka `/edukasi/`:

- Featured artikel.
- Kartu panduan.
- Agenda mendatang.
- Mitra penyaluran dan catatan penyaluran.
- Produk guna ulang (static, bukan database).

Buka `/edukasi/artikel/`, coba pencarian `plastik` dan kategori `Pengurangan sampah`.
Tunjukkan URL query berubah dan hasil diperbarui tanpa reload penuh. Jelaskan bahwa
form GET tetap bekerja jika JavaScript dimatikan.

Buka satu detail artikel:

- `published()` menyaring artikel;
- `cover` memilih gambar/placeholder;
- body dirender `linebreaks`.

Buka `/edukasi/penyaluran/`:

- record hanya status `delivered`;
- tanggal Jakarta;
- statistik berasal dari aggregate.

Jelaskan satu edge case: draf/terjadwal tidak bisa dibuka publik.

## 03:00–06:00 — Artikel CRUD

1. Buka `/edukasi/kelola/`.
2. Klik `Tulis artikel`.
3. Isi judul sementara, ringkasan, isi, kategori; biarkan draf; simpan.
4. Tunjukkan dashboard menampilkan draf.
5. Edit judul; simpan; tunjukkan slug artikel lama tidak berubah.
6. Buka halaman detail (jika masih draf, tunjukkan 404), lalu terbitkan dan buka.
7. Hapus artikel sementara; tunjukkan bahwa tautan Hapus memakai konfirmasi dan
   fetch async pada dashboard. Bila JavaScript gagal, fallback konfirmasi POST tetap
   tersedia.

Jangan menghapus artikel seed. Jika waktu sempit, cukup create + delete satu artikel
sementara; edit gambar/preview dapat dijelaskan dari artikel seed.

File yang dibuka:

- `ArticleCreateView`/`ArticleUpdateView` di `education/views.py`.
- `ArticleForm` di `education/forms.py`.
- `Article.save`/`cover` dan validator gambar di `models.py`.
- `manage_form.html`.

## 06:00–09:00 — Agenda dan penyaluran

Agenda:

- `Tambah agenda`;
- pilih lokasi;
- isi start/end;
- coba end < start → error;
- simpan yang valid;
- edit dan delete record sementara.

Penyaluran:

- `Tambah catatan`;
- pilih tujuan panti/komunitas;
- quantity;
- status `delivered` + tanggal;
- coba `delivered` tanpa tanggal → error form;
- simpan/edit/delete record sementara.

Jelaskan:

- `Event.location` dan `Distribution.destination` `PROTECT`;
- `Distribution.clean()` menolak status/tanggal tidak konsisten;
- form hanya menawarkan lokasi aktif untuk create.

## 09:00–11:00 — Penjelasan kode

Urutan yang disarankan:

1. `education/urls.py` — URL name → view.
2. `education/views.py` — `ArticleListView` filter GET/partial.
3. `education/views.py` — `StaffRequiredMixin.test_func` dan async delete JSON.
4. `ManageFormMixin.form_valid` — messages + redirect.
5. `education/forms.py` — fields dan queryset.
6. `education/models.py` — validator, `published()`, `clean()`.
7. `templates/education/manage_form.html` — `csrf_token`, `multipart/form-data`,
   error rendering.
8. `static/js/education.js` — filter fetch dan delete fetch.
9. `article_image` — media endpoint sempit.

Kalimat kunci:

> Form hanya menerima input; aturan bisnis tetap di model agar konsisten meskipun
> record dibuat dari tempat lain. Authorization diperiksa di server, bukan hanya tombol.

## 11:00–12:30 — Keamanan/validasi

Tunjukkan:

- anonymous ke `/edukasi/kelola/` → redirect login;
- user non-staff → 403;
- direct POST non-staff → 403 (test);
- delete tanpa CSRF → 403 (test);
- draft detail → 404;
- file gambar invalid → form error;
- file media tidak terdaftar → 404.

Jangan mengubah permission agar demo lebih mudah.

## 12:30–15:00 — Live coding

Pilih satu tantangan dari `live-coding-playbook.md`:

- Level 1: tambah validasi `min_length` pada summary artikel.
- Level 2: tambahkan filter status draf/terbit pada dashboard staff.
- Level 3 (hanya jika siap): tangani slug race/`IntegrityError` atau optimasi query
  setelah membuktikan N+1.

Saat live coding, ucapkan langkah:

1. Baca requirement.
2. Cari file yang tepat.
3. Ubah kode minimal.
4. Tambah/perbarui tes.
5. Jalankan tes terkait.
6. Jelaskan hasil dan edge case.

Jika challenge macet, kembali ke solusi minimal dan jelaskan trade-off. Jangan
menghapus assertion atau menonaktifkan permission.

## Jika waktu tersisa sedikit

Prioritas:

1. Halaman publik + satu artikel detail.
2. Satu CRUD create/delete sementara.
3. `StaffRequiredMixin` + validasi form.
4. Satu tes.

Lewati edit agenda/penyaluran; jelaskan lewat code walkthrough.

## Setelah demo

- Pastikan record sementara sudah dihapus.
- Jangan menghapus artikel/lokasi/agenda seed PWS.
- Refresh dashboard; pastikan data kembali seperti semula.
- Jangan commit/push hasil penyesuaian demo.
