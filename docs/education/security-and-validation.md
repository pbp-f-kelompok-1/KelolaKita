# Keamanan dan Validasi — Education

Dokumen ini membedakan kontrol yang benar-benar ada dari batasan yang masih terbuka.
Jangan mengklaim aplikasi “100% aman” saat demo.

## 1. Authentication vs authorization

- **Authentication** membuktikan siapa user. Project memakai Django auth/session dan
  login admin lokal.
- **Authorization** menentukan boleh atau tidak. Education memakai
  `StaffRequiredMixin`.

`StaffRequiredMixin`:

```python
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("admin:login")

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()
```

Konsekuensi:

| Kondisi | Hasil |
|---|---|
| Anonymous membuka management | redirect ke login admin |
| User login non-staff | 403 Forbidden |
| Staff aktif | boleh |
| Staff inactive | tidak mempertahankan sesi; redirect login |

Pemeriksaan dilakukan server-side pada setiap view management, termasuk endpoint
create/update/delete. Menyembunyikan tombol di template bukan mekanisme otorisasi.

## 2. Objek dan permission

Education memakai model konten milik kelompok, bukan data per user. Semua staff aktif
boleh mengelola semua artikel/agenda/penyaluran. Tidak ada object-level ownership
(seperti “hanya penulis yang boleh edit”). Ini keputusan produk, bukan bug yang
disembunyikan.

Karena itu, jangan mengklaim bahwa user hanya dapat mengubah datanya sendiri. Yang
benar: **semua user non-staff tidak dapat mengubah apa pun; staff aktif dapat mengelola
konten kelompok.**

## 3. Validasi form dan model

### Artikel

- Field wajib: judul, ringkasan, isi, kategori, tanggal.
- `ImageField` + `validate_article_image`:
  - maksimal 5 MB;
  - ekstensi JPG/JPEG/PNG/WebP;
  - isi file harus dapat dibuka Pillow dan formatnya termasuk JPEG/PNG/WebP;
  - minimal 800 × 450 piksel.
- `Article.save()` membuat slug unik dan stabil.
- Kategori dibatasi choices model.

### Agenda

- Judul, waktu mulai, dan lokasi wajib.
- `Event.clean()` menolak selesai lebih awal dari mulai.
- Database juga memiliki `CheckConstraint` untuk aturan yang sama.
- Form hanya menawarkan lokasi aktif untuk create; record lama dapat mempertahankan
  lokasi nonaktif saat edit.

### Penyaluran

- Nama barang dan jumlah wajib; jumlah minimal 1.
- Tujuan harus panti asuhan/komunitas.
- Status harus salah satu choices.
- Status `delivered` wajib tanggal.
- `destination` memakai `PROTECT` agar tujuan historis tidak hilang.

## 4. CSRF dan method

Semua form POST memakai `{% csrf_token %}`. Delete menggunakan form POST, bukan tautan
GET. Tes `test_csrf_required_for_delete` mengirim POST tanpa token dan memastikan 403
serta record tetap ada.

GET hanya untuk membaca/konfirmasi; bukan untuk mutasi.

## 5. Konten tidak terbit

`Article.objects.published()` menjadi satu-satunya queryset publik:

- `is_published=True`;
- `published_at <= now`.

`ArticleDetailView` dan `ArticleListView` memakai queryset itu, sehingga draf dan
artikel terjadwal menghasilkan 404 di publik. Dashboard staff memakai
`Article.objects.all()` sehingga draf tetap bisa dikelola.

## 6. Media dan gambar

`article_image` di `/media/education/articles/<path>`:

- menolak path kosong/absolut/backslash/NUL/`..`;
- membentuk nama file hanya di prefix `education/articles/`;
- mencari `Article` yang benar-benar memiliki `image` tersebut;
- untuk anonim, hanya artikel published;
- membuka file hanya jika `image_available`;
- MIME hanya JPEG/PNG/WebP;
- mengembalikan `FileResponse` dengan `nosniff`;
- cache publik 1 jam; akses staff ke draft memakai `private, no-store`.

Yang **tidak** dilakukan endpoint ini: membuka seluruh `MEDIA_ROOT` atau path bebas.
File yang ada di folder media tetapi tidak terdaftar di `Article.image` akan 404.

## 7. Error handling

- Form invalid → HTTP 200 dengan error field; tidak ada write.
- Record tidak ada → 404 dari generic view.
- Non-staff → 403.
- Anonymous → redirect login.
- File hilang → placeholder publik / peringatan di form staff.
- Constraint database (mis. end < start) → error validasi, bukan traceback ke publik.

## 8. Batasan keamanan yang masih ada

- Tidak ada rate limiting untuk login/upload/endpoint media.
- Tidak ada audit log perubahan konten.
- Tidak ada object ownership; semua staff setara.
- File gambar tidak dihapus otomatis saat artikel dihapus; orphan file dapat tersisa.
- Tidak ada pemindaian malware atau pembersihan EXIF.
- `article_image` masih memakai Django/gunicorn untuk streaming, bukan CDN/media server
  produksi.
- Persistensi media PWS belum diverifikasi.
- Konfigurasi production (secret key, debug, host) adalah tanggung jawab deployment;
  modul ini tidak mengubahnya.

Saat demo, sebutkan kontrol yang ada dan satu batasan yang jujur. Itu lebih kuat
daripada klaim keamanan tanpa bukti.
