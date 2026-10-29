# Referensi CRUD — Education

Semua route mutasi memakai `StaffRequiredMixin` (`is_authenticated`, `is_active`,
`is_staff`) dan `csrf_token`. Tabel di bawah mengikuti kode aktual.

## Matriks CRUD

| Entitas | Operasi | Nama URL / path | Metode | View | Form / Model | Izin | Respons sukses |
|---|---|---|---|---|---|---|---|
| Artikel | Baca daftar (staff) | `education_manage` `/edukasi/kelola/` | GET | `ManageDashboard` | `Article`, `Event`, `Distribution` | Staff aktif | 200 dashboard |
| Artikel | Buat | `article_create` `/edukasi/kelola/artikel/tambah/` | GET/POST | `ArticleCreateView` | `ArticleForm` | Staff aktif | Redirect `education_manage` + pesan flash |
| Artikel | Baca daftar publik | `article_list` `/edukasi/artikel/` | GET | `ArticleListView` | `Article.objects.published()` | Publik | 200 |
| Artikel | Baca detail | `article_detail` `/edukasi/artikel/<slug>/` | GET | `ArticleDetailView` | queryset `published()` | Publik | 200 / 404 |
| Artikel | Ubah | `article_update` `/edukasi/kelola/artikel/<pk>/ubah/` | GET/POST | `ArticleUpdateView` | `ArticleForm` | Staff aktif | Redirect + pesan flash |
| Artikel | Hapus | `article_delete` `/edukasi/kelola/artikel/<pk>/hapus/` | GET/POST | `ArticleDeleteView` | `Article` | Staff aktif | GET konfirmasi; POST redirect + pesan flash |
| Agenda | Buat | `event_create` `/edukasi/kelola/agenda/tambah/` | GET/POST | `EventCreateView` | `EventForm` | Staff aktif | Redirect + pesan flash |
| Agenda | Baca daftar publik | `event_list` `/edukasi/agenda/` | GET | `EventListView` | agenda terbit + mendatang | Publik | 200 |
| Agenda | Detail publik | `event_detail` `/edukasi/agenda/<pk>/` | GET | `EventDetailView` | `published_events()` | Publik | 200 / 404 |
| Agenda | Ubah | `event_update` `/edukasi/kelola/agenda/<pk>/ubah/` | GET/POST | `EventUpdateView` | `EventForm` | Staff aktif | Redirect + pesan flash |
| Agenda | Hapus | `event_delete` `/edukasi/kelola/agenda/<pk>/hapus/` | GET/POST | `EventDeleteView` | `Event` | Staff aktif | Redirect + pesan flash |
| Penyaluran | Buat | `distribution_create` `/edukasi/kelola/penyaluran/tambah/` | GET/POST | `DistributionCreateView` | `DistributionForm` | Staff aktif | Redirect + pesan flash |
| Penyaluran | Baca daftar publik | `distribution_list` `/edukasi/penyaluran/` | GET | `DistributionListView` | `public_distributions()` | Publik | 200 |
| Penyaluran | Ubah | `distribution_update` `/edukasi/kelola/penyaluran/<pk>/ubah/` | GET/POST | `DistributionUpdateView` | `DistributionForm` | Staff aktif | Redirect + pesan flash |
| Penyaluran | Hapus | `distribution_delete` `/edukasi/kelola/penyaluran/<pk>/hapus/` | GET/POST | `DistributionDeleteView` | `Distribution` | Staff aktif | Redirect + pesan flash |
| Media artikel | Baca | `/media/education/articles/<path>` | GET | `article_image` | `Article.image` + storage | Publik untuk artikel terbit; staff untuk draft | `FileResponse` / 404 |

## Alur pembuatan artikel

1. Staff membuka `article_create` (GET).
2. `ArticleCreateView` membuat `ArticleForm` kosong.
3. Template menampilkan input teks, kategori, waktu, checkbox terbit, dan file.
4. POST mengirim `request.POST` + `request.FILES`.
5. Form memvalidasi field, kategori, dan `validate_article_image`.
6. Jika invalid: response 200, field errors tampil, tidak ada record.
7. Jika valid: `form.save()` membuat `Article`; slug dibuat `Article.save()`.
8. `messages.success`; redirect ke dashboard.
9. Dashboard membaca ulang dari database dan menampilkan artikel baru.

Gambar lama tidak perlu diunggah ulang saat edit. Checkbox `image-clear` menghapus
referensi gambar. Upload baru dan clear bersamaan ditolak oleh form; tes memastikan
gambar lama tidak hilang.

## Alur pengubahan artikel

1. `ArticleUpdateView` memuat instance berdasarkan PK; PK tidak ada → 404.
2. Form diisi dari instance.
3. POST valid menyimpan field yang dikirim; `created_at` tetap, `updated_at` berubah.
4. POST invalid menampilkan error dan tidak menyimpan perubahan.
5. Redirect ke dashboard setelah sukses.

Slug tidak berubah saat judul diedit; ini alasan URL artikel lama tetap bekerja.

## Alur penghapusan

1. GET menampilkan `manage_confirm_delete.html` dengan objek.
2. POST harus membawa CSRF token.
3. `DeleteView` menghapus record.
4. `messages.success` dikirim; redirect ke dashboard.

Delete tidak memakai `GET` untuk menghapus. Tes `test_csrf_required_for_delete`
membuktikan POST tanpa token ditolak dan record tetap ada.

## Alur agenda

- Form membatasi lokasi ke lokasi aktif, tetapi mengizinkan lokasi lama saat edit.
- `Event.clean()` + database constraint menolak `end_at < start_at`.
- Baca daftar publik hanya event terbit yang belum mulai; detail event terbit tetap ada
  meskipun sudah lewat.
- Lokasi dilindungi `PROTECT`, jadi menghapus lokasi yang dipakai agenda akan gagal.

## Alur penyaluran

- Tujuan harus panti asuhan/komunitas.
- `quantity` minimal 1.
- Status `delivered` wajib punya tanggal.
- Halaman publik hanya menampilkan catatan `delivered` dengan tanggal yang sudah lewat.
- Tujuan dilindungi `PROTECT`.

## Kasus khusus yang layak disebut saat demo

- Artikel draf/terjadwal → 404 di detail publik.
- Artikel tanpa gambar → placeholder, bukan broken `<img>`.
- File gambar hilang dari storage → placeholder publik; preview staff memberi peringatan.
- Gambar tidak valid/terlalu besar/terlalu kecil → form error, tidak menyimpan artikel.
- Non-staff POST langsung ke endpoint mutasi → 403.
- Anonymous ke management → redirect login.
- Staff inactive → tidak mendapat akses.
- Record tidak ditemukan → 404.
- Agenda selesai sebelum mulai → validation error.
- Distribusi `delivered` tanpa tanggal → validation error.
- Delete tanpa CSRF → 403.
- Lokasi yang masih dipakai → tidak dapat dihapus (`PROTECT`).
