# Glosarium Teknis Education

Istilah di bawah muncul dalam source code atau dokumentasi Education. Nama kelas,
field, fungsi, dan route tetap ditulis sesuai identifier aslinya.

| Istilah | Penjelasan | Contoh di KelolaKita |
|---|---|---|
| Model | Komponen Django yang mendefinisikan struktur data dan aturan pada database. | `Article`, `Event`, `Distribution`. |
| Field | Kolom atau atribut pada model. | `Article.title`, `Distribution.quantity`. |
| View | Komponen yang menerima request dan menentukan response. | `public_home`, `ArticleListView`, `ArticleCreateView`. |
| Template | Berkas HTML yang membentuk tampilan dari context yang diberikan view. | `templates/education/public_home.html`. |
| Form | Komponen yang menangani input pengguna dan validasinya. | `ArticleForm`, `EventForm`, `DistributionForm`. |
| `ModelForm` | Form Django yang terhubung langsung ke model dan dapat menyimpan data model. | `ArticleForm` adalah `ModelForm`. |
| QuerySet | Kumpulan hasil query database yang dapat disaring dan diurutkan sebelum dievaluasi. | `Article.objects.published()`. |
| `published()` | Method QuerySet khusus untuk artikel yang terbit dan sudah melewati waktu publikasi. | `ArticleQuerySet.published()`. |
| Foreign key | Field yang menghubungkan record ke record pada model lain. | `Event.location`, `Distribution.destination`. |
| `PROTECT` | Opsi `on_delete` yang mencegah record induk dihapus selama masih dipakai. | Location yang dipakai agenda/penyaluran. |
| URL routing | Pemetaan URL ke view melalui `urls.py`. | `/edukasi/kelola/artikel/tambah/`. |
| URL name | Nama unik route yang dipakai `{% url %}` dan `reverse()`. | `article_create`, `education_manage`. |
| CRUD | Create, Read, Update, Delete — empat operasi data dasar. | Artikel, agenda, dan penyaluran. |
| GET | HTTP method untuk membaca atau menampilkan halaman. | Membuka form create, halaman detail. |
| POST | HTTP method untuk mengirim data/perubahan. | Menyimpan form, menghapus record setelah konfirmasi. |
| Authentication | Proses memastikan identitas pengguna. | Login melalui halaman admin lokal. |
| Authorization | Pemeriksaan apakah pengguna berhak melakukan tindakan. | `StaffRequiredMixin` pada dashboard. |
| Staff | Status user Django (`is_staff`) yang dipakai sebagai syarat akses pengelolaan. | Pengguna staff aktif dapat CRUD konten. |
| CSRF | Perlindungan agar request perubahan tidak dipalsukan dari situs lain. | `{% csrf_token %}` pada form. |
| Session | Mekanisme Django untuk mengingat status login pengguna. | Redirect anonymous ke login. |
| Media files | File yang diunggah pengguna dan disimpan di storage. | Gambar sampul artikel di `MEDIA_ROOT`. |
| Static files | Aset aplikasi yang disajikan terpisah dari media upload. | `education.css`, gambar produk. |
| `ImageField` | Field Django untuk file gambar. | `Article.image`. |
| Placeholder | Gambar pengganti ketika artikel tidak punya cover atau file hilang. | `article-placeholder.svg`. |
| MIME type | Jenis konten file yang dikirim server. | `image/jpeg`, `image/png`, `image/webp`. |
| `FileResponse` | Response Django yang mengalirkan file. | `article_image`. |
| `select_related()` | Optimasi query untuk mengambil relasi foreign key dalam query yang sama. | Event + location pada daftar agenda. |
| `redirect` | Response yang mengarahkan browser ke URL lain. | Setelah create/update/delete sukses. |
| Messages framework | Mekanisme Django untuk menampilkan pesan sekali setelah redirect. | “Artikel berhasil diperbarui.” |
| `clean()` | Method model/form untuk validasi yang bergantung pada beberapa field. | `Event.clean()`, `Distribution.clean()`. |
| Exception | Kondisi error yang ditangani kode. | `ValidationError`, `Http404`, `IntegrityError`. |
| HTTP 403 Forbidden | Status bahwa pengguna terautentikasi tetapi tidak berwenang. | Non-staff membuka dashboard. |
| HTTP 404 Not Found | Status bahwa resource tidak ditemukan atau tidak boleh terlihat. | Draft artikel di detail publik. |
| Test | Kode yang memverifikasi perilaku aplikasi. | `education/tests.py`. |
| Test coverage | Ukuran bagian kode yang dijalankan tes; bukan jaminan semua perilaku benar. | Belum diukur pada audit ini. |
| AJAX | Pertukaran data asynchronous tanpa reload penuh. | Filter artikel dan hapus data dashboard memakai `fetch`. |
| HTMX | Library untuk interaksi HTML partial/asynchronous. | Tidak dipakai; modul memakai fetch API vanilla. |
| Progressive enhancement | Fitur tambahan yang tidak menghilangkan fungsi dasar saat JS tidak tersedia. | `static/js/education.js`. |
