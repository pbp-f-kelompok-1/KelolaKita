# Ringkasan Cepat Demo — Education

## A. Menjalankan

```bash
cd "Tugas Kelompok"
source env/bin/activate
python manage.py check
python manage.py test education
python manage.py runserver
```

URL:

- Publik: `http://127.0.0.1:8000/edukasi/`
- Dashboard: `http://127.0.0.1:8000/edukasi/kelola/`
- Penyaluran: `http://127.0.0.1:8000/edukasi/penyaluran/`
- Lokasi: `http://127.0.0.1:8000/locations/`

Gunakan akun staff lokal sendiri. Jangan memakai kredensial production dan jangan
menulis password di catatan/dokumen.

## B. File penting

| File | Isi |
|---|---|
| `education/models.py` | Article, Event, Distribution, validator gambar |
| `education/forms.py` | ArticleForm, EventForm, DistributionForm |
| `education/views.py` | public views, StaffRequiredMixin, CRUD, article_image |
| `education/urls.py` | route publik/staff |
| `templates/education/manage_list.html` | dashboard |
| `templates/education/manage_form.html` | form + gambar |
| `templates/education/public_home.html` | halaman publik |
| `education/tests.py` | model/form/CRUD/security/media tests |
| `education/tests_import.py` | test import PWS |
| `static/css/education.css` | styling Education |
| `static/js/education.js` | reveal progressive |
| `docs/education/` | dokumentasi demo |

## C. Alur yang harus diingat

```text
Browser
→ education/urls.py
→ view (public atau StaffRequiredMixin)
→ ModelForm / ORM
→ Model.clean() / database
→ redirect + messages
→ template
→ browser
```

Filter artikel:

```text
input q/category
→ GET /edukasi/artikel/?...
→ ArticleListView
→ Article.objects.published().filter(...)
→ partial HTML (AJAX) atau halaman penuh
→ #article-results
```

Async delete dashboard:

```text
klik Hapus
→ konfirmasi
→ POST delete + CSRF + X-Requested-With
→ StaffRequiredMixin
→ DeleteView → JSON
→ baris dihapus / reload bila list kosong
```

Contoh create artikel:

1. POST ke `article_create`.
2. `ArticleCreateView` + `ArticleForm`.
3. Form memvalidasi required fields, category, image.
4. Valid → `Article.save()` membuat slug.
5. Redirect ke `education_manage`; pesan sukses.
6. Invalid → 200, error field, tidak ada write.

## D. 20 pertanyaan dosen dan jawaban singkat

1. **Apa beda model dan form?**
   Model mendefinisikan struktur/aturan database; form menangani input user dan validasi
   request. `ModelForm` menghubungkan keduanya.

2. **Mengapa validasi server-side?**
   Client bisa dimanipulasi; server adalah batas kepercayaan. Form/model Django tetap
   memvalidasi walaupun tombol/JS dimatikan.

3. **Bagaimana URL menemukan view?**
   `education/urls.py` memetakan `path` + name ke function/class view; root URL
   meng-include app dengan prefix `/edukasi/`.

4. **Apa yang terjadi jika `form.is_valid()` false?**
   View merender ulang template dengan `form.errors`; tidak ada `save()`.

5. **Bagaimana upload gambar diproses?**
   `multipart/form-data` → `request.FILES` → `ImageField` → validator Pillow →
   storage `MEDIA_ROOT`.

6. **Mengapa GET dan POST berbeda?**
   GET membaca/menampilkan; POST mengubah state. Delete memakai POST + CSRF, bukan GET.

7. **Mengapa CSRF diperlukan?**
   Mencegah request palsu dari situs lain memakai sesi korban. Template memuat
   `{% csrf_token %}`; tes delete tanpa token → 403.

8. **Bagaimana membatasi staff?**
   `StaffRequiredMixin` memeriksa `is_authenticated`, `is_active`, `is_staff` di server.

9. **Bagaimana test membuktikan permission?**
   Test login non-staff lalu GET/POST endpoint dan assert 403/302; record tidak berubah.

10. **Bagaimana jika FK lokasi salah?**
    Form membatasi queryset; model `clean()`/`PROTECT` menjaga aturan. Input enum tidak
    valid ditolak.

11. **Kapan `select_related` dipakai?**
    Saat mengakses FK di loop; event/location dan distribution/destination sudah
    memakai `select_related` pada queryset yang relevan.

12. **Mengapa test memakai database test?**
    Django membuat database sementara dan menghapusnya; data `db.sqlite3` tidak tersentuh.

13. **Bagaimana mendiagnosis gambar 404?**
    Cek `Article.image.name`, `image_available`, file di `MEDIA_ROOT`, status publikasi,
    MIME, dan route `article_image`. Jangan menambah route media blanket.

14. **Apa yang terjadi saat lokasi dihapus?**
    FK `PROTECT` menolak jika masih dipakai event/distribution; error ditangani aplikasi
    Location.

15. **Trade-off HTMX?**
    Modul ini memakai Fetch API untuk filter dan delete, bukan HTMX. Async memberi
    pengalaman tanpa reload, tetapi menambah state/JS/error handling. Create/update
    tetap full-page agar generic view dan validasi tidak diduplikasi.

16. **Mengapa artikel draft 404?**
    `ArticleDetailView.get_queryset()` memakai `published()`; draft/terjadwal tidak
    ditemukan.

17. **Mengapa slug tidak berubah saat judul diedit?**
    Menjaga URL yang sudah dibagikan. `Article.save()` hanya membuat slug jika kosong.

18. **Apa risiko delete artikel?**
    File gambar tidak otomatis dihapus (orphan); relasi tidak ada, tetapi media perlu
    dibersihkan terpisah.

19. **Apa arti `PROTECT`?**
    Django menolak delete parent selama masih ada child; mencegah data historis kehilangan
    relasi.

20. **Apa yang belum terverifikasi?**
    Coverage tool tidak terpasang; media/PWS persistence belum diverifikasi; tidak ada
    object ownership/audit log.

## E. Checklist sebelum demo

- [ ] Working tree dipahami; tidak ada reset/clean.
- [ ] Server dan database lokal siap.
- [ ] Akun staff lokal aktif (jangan pakai production).
- [ ] Tes Education lulus.
- [ ] Tab halaman publik/dashboard/detail sudah dibuka.
- [ ] IDE membuka model/form/view/url/template.
- [ ] Data sementara untuk CRUD disiapkan dan boleh dihapus.
- [ ] Rencana cadangan jika live coding gagal: tunjukkan test dan kode, bukan mengubah
      permission.
- [ ] Setelah demo, hapus hanya record sementara; jangan hapus data seed.
