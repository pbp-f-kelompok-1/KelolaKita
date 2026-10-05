# KelolaKita

## Deskripsi Aplikasi

**KelolaKita** adalah platform digital pengelolaan barang dan sampah yang membantu pengguna menentukan cara penanganan yang tepat berdasarkan jenis dan kondisi barang. Setiap barang yang disetorkan akan melalui pemeriksaan awal untuk menentukan kategori penanganan, yaitu **Recycle, Reduce, atau Reuse**.

Pada kategori **Recycle**, barang yang masih dapat didaur ulang dapat disetorkan melalui kantor KelolaKita atau titik setoran yang tersedia. Pengguna dapat memilih lokasi dan jadwal berdasarkan jarak serta kemudahan pengantaran. Barang yang telah dikumpulkan kemudian disalurkan kepada bank sampah untuk diproses lebih lanjut.

Pada kategori **Reuse**, barang yang masih memiliki nilai guna akan diarahkan untuk digunakan kembali oleh pihak yang membutuhkan. Barang berukuran kecil dapat disetorkan ke titik tertentu atau diantarkan langsung ke panti asuhan yang tersedia pada peta. Sementara itu, barang berukuran besar dapat dialihkan kepada komunitas untuk membantu proses penyaluran kepada pihak yang membutuhkan.

Sementara itu, kategori **Reduce** berfokus pada upaya mengurangi timbulan sampah yang tidak dapat didaur ulang sejak dari sumbernya. KelolaKita mendukung upaya tersebut melalui edukasi, kegiatan komunitas, dan promosi penggunaan produk yang dapat digunakan kembali, seperti tote bag, stainless steel bottle, reusable straw, dan produk ramah lingkungan lainnya.

KelolaKita hadir untuk membantu masyarakat mengelola barang dan sampah dengan lebih terarah. Melalui proses pemeriksaan dan penentuan kategori penanganan, setiap barang dapat diarahkan sesuai dengan kondisi dan potensi pemanfaatannya.

---

## Anggota Kelompok

| No. | Nama | NPM |
|---|---|---|
| 1 | Glenn Josia Devano | 2506614712 |
| 2 | Ihsan Rafi Ahmad | 2506611326 |
| 3 | Maxwelly F.H. Simatupang | 2506584294 |
| 4 | Rafa Darussalam | 2506538924 |
| 5 | Rayna Kayla Rayvanka | 2506657283 |

---

## Peran Pengguna

### Pengguna

Pengguna merupakan pihak yang ingin menyetorkan barang atau sampah untuk mendapatkan penanganan yang sesuai. Pengguna dapat:

- Melakukan pengajuan penyetoran barang.
- Melihat hasil pemeriksaan dan kategori penanganan.
- Memilih metode penyetoran.
- Memilih lokasi titik setoran.
- Memilih jadwal penyetoran.
- Melihat lokasi panti atau titik penyaluran melalui peta.
- Memantau proses penjemputan dan penanganan barang.
- Mengakses informasi edukasi mengenai pengelolaan barang dan sampah.

### Pengelola KelolaKita

Pengelola merupakan pihak yang bertanggung jawab dalam menjalankan proses pemeriksaan, penyetoran, penjemputan, dan penanganan barang. Pengelola dapat:

- Melakukan pemeriksaan awal terhadap barang.
- Menentukan kategori penanganan barang.
- Mengelola titik setoran.
- Mengelola jadwal penyetoran.
- Mengelola proses penjemputan barang.
- Memverifikasi kondisi dan kategori barang.
- Mengelola proses penyaluran barang.
- Mengelola informasi dan konten edukasi.

### Pihak Mitra

KelolaKita dapat bekerja sama dengan pihak lain dalam proses penanganan barang, antara lain:

- **Bank sampah** untuk proses Recycle.
- **Panti asuhan** dan pihak yang membutuhkan untuk proses Reuse.
- **Komunitas** untuk mendukung proses penyaluran serta kegiatan Reduce dan Reuse.

---

## Daftar Modul

### 1. Authentication / Profile

Modul **Authentication / Profile** digunakan untuk mengelola identitas dan data pengguna KelolaKita.

**Cakupan fitur:**

- Registrasi dan login.
- Pengelolaan profil.
- Data pengguna.
- Informasi akun.
- Pengaturan akun.

**Operasi CRUD:**

| Operasi | Deskripsi |
|---|---|
| Create | Membuat akun dan data profil |
| Read | Melihat data profil |
| Update | Mengubah informasi profil |
| Delete | Menonaktifkan atau menghapus data akun |

**Penanggung Jawab:**  
`Rayna Kayla Rayvanka`

---

### 2. Pemeriksaan & Kategori Penanganan

Modul **Pemeriksaan & Kategori Penanganan** digunakan untuk menentukan metode penanganan berdasarkan jenis dan kondisi barang.

Setiap barang yang akan diproses wajib melalui pemeriksaan awal. Hasil pemeriksaan digunakan untuk menentukan apakah barang termasuk kategori **Recycle, Reduce, atau Reuse**.

**Cakupan fitur:**

- Pemeriksaan jenis barang.
- Pemeriksaan kondisi barang.
- Penentuan kategori penanganan.
- Informasi rekomendasi penanganan.
- Riwayat hasil pemeriksaan.

**Operasi CRUD:**

| Operasi | Deskripsi |
|---|---|
| Create | Membuat data pemeriksaan |
| Read | Melihat hasil pemeriksaan dan kategori penanganan |
| Update | Mengubah hasil pemeriksaan apabila diperlukan |
| Delete | Menghapus data pemeriksaan sesuai kewenangan |

**Penanggung Jawab:**  
`Rafa Darussalam`

---

### 3. Titik Setoran & Lokasi

Modul **Titik Setoran & Lokasi** digunakan untuk mengelola lokasi penyetoran dan membantu pengguna menemukan lokasi yang sesuai.

**Cakupan fitur:**

- Daftar titik setoran.
- Detail lokasi.
- Informasi alamat.
- Pencarian lokasi.
- Filter lokasi.
- Peta interaktif.
- Lokasi panti untuk penyaluran barang Reuse.

**Operasi CRUD:**

| Operasi | Deskripsi |
|---|---|
| Create | Menambahkan titik atau lokasi |
| Read | Melihat daftar, detail, dan lokasi pada peta |
| Update | Mengubah informasi lokasi |
| Delete | Menghapus lokasi yang tidak digunakan |

**Penanggung Jawab:**  
`Maxwelly F.H. Simatupang`

---

### 4. Penyetoran & Penjemputan

Modul **Penyetoran & Penjemputan** digunakan untuk mengatur proses penyetoran barang melalui kantor maupun titik setoran.

Pada metode **Setor ke Kantor**, pengguna membawa barang langsung ke kantor KelolaKita untuk menjalani pemeriksaan dan pengukuran. Setelah itu, barang ditentukan kategori penanganannya sebelum diproses lebih lanjut.

Pada metode **Setor ke Titik**, pengguna memilih lokasi titik setoran, menentukan kategori barang, memilih jadwal, dan melakukan konfirmasi. Setelah barang diletakkan sesuai jadwal, petugas akan melakukan penjemputan pada akhir sesi penyetoran.

Jadwal penyetoran terdiri atas dua sesi:

| Sesi | Waktu |
|---|---|
| Sesi Pagi | 08.00–11.00 |
| Sesi Siang | 13.00–16.00 |

**Operasi CRUD:**

| Operasi | Deskripsi |
|---|---|
| Create | Membuat permintaan penyetoran atau penjemputan |
| Read | Melihat detail dan status penyetoran |
| Update | Mengubah jadwal atau status sesuai kewenangan |
| Delete | Membatalkan permintaan yang masih dapat dibatalkan |

**Penanggung Jawab:**  
`Ihsan Rafi Ahmad`

---

### 5. Penyaluran, Komunitas & Edukasi

Modul **Penyaluran, Komunitas & Edukasi** digunakan untuk mendukung proses penanganan barang, khususnya pada kategori Reuse dan Reduce.

Pada kategori **Reuse**, barang yang masih layak digunakan dapat disalurkan melalui titik setoran, panti asuhan, komunitas, atau pihak lain yang membutuhkan. Barang berukuran besar dapat dialihkan kepada komunitas untuk membantu proses penyaluran.

Pada kategori **Reduce**, kegiatan difokuskan pada upaya mengurangi timbulan sampah melalui edukasi, kegiatan komunitas, kampanye pengurangan sampah, serta penggunaan produk yang dapat digunakan kembali.

**Contoh produk ramah lingkungan:**

- Tote bag.
- Stainless steel bottle.
- Reusable straw.
- Produk reusable lainnya.

**Operasi CRUD:**

| Operasi | Deskripsi |
|---|---|
| Create | Menambahkan data penyaluran, komunitas, atau konten edukasi |
| Read | Melihat informasi penyaluran, komunitas, dan edukasi |
| Update | Mengubah informasi yang tersedia |
| Delete | Menghapus data yang sudah tidak digunakan |

**Penanggung Jawab:**  
`Glenn Josia Devano`

---

## Alur Utama Sistem

KelolaKita menerapkan **pemeriksaan awal sebagai tahap utama sebelum barang diproses lebih lanjut**. Pengguna terlebih dahulu mengajukan barang yang ingin disetorkan. Barang tersebut kemudian diperiksa berdasarkan jenis dan kondisinya untuk menentukan kategori penanganan yang paling sesuai, yaitu Recycle, Reduce, atau Reuse.

Untuk barang yang masuk kategori **Recycle**, pengguna dapat memilih untuk menyetorkannya langsung ke kantor KelolaKita atau ke titik setoran yang tersedia. Jika memilih titik setoran, pengguna menentukan lokasi dan jadwal penyetoran. Setelah barang ditempatkan sesuai jadwal, petugas melakukan penjemputan dan membawa barang tersebut untuk diproses lebih lanjut sebelum disalurkan ke bank sampah.

Barang yang masuk kategori **Reuse** akan diarahkan untuk digunakan kembali. Barang berukuran kecil dapat disetorkan ke titik atau diantarkan langsung ke panti asuhan yang tersedia. Barang berukuran besar dapat disalurkan melalui komunitas agar dapat diteruskan kepada pihak yang membutuhkan.

Sementara itu, barang yang termasuk kategori **Reduce** tidak diarahkan ke proses daur ulang, tetapi ditangani melalui pendekatan pengurangan sampah. Pengguna akan mendapatkan informasi, edukasi, dan alternatif penggunaan produk yang dapat digunakan kembali. Komunitas juga dapat berperan dalam mendukung kegiatan dan kampanye untuk mengurangi timbulan sampah dari sumbernya.

Dengan alur tersebut, KelolaKita tidak hanya berfungsi sebagai tempat penyetoran barang, tetapi juga sebagai platform yang membantu pengguna menentukan **langkah penanganan yang sesuai untuk setiap barang berdasarkan jenis, kondisi, dan potensi pemanfaatannya**.

---

## Public API

KelolaKita menggunakan **ekosistem OpenStreetMap** untuk mendukung fitur yang membutuhkan informasi lokasi dan peta. Integrasi ini digunakan terutama pada modul **Titik Setoran & Lokasi**, serta mendukung proses penyetoran dan penyaluran barang berbasis lokasi.

### OpenStreetMap

**OpenStreetMap (OSM)** digunakan sebagai sumber peta dasar dan informasi geografis pada aplikasi KelolaKita. Peta digunakan untuk menampilkan lokasi titik setoran, kantor KelolaKita, serta lokasi penyaluran seperti panti yang berkaitan dengan proses Reuse. Informasi geografis tersebut membantu pengguna dalam melihat dan memilih lokasi yang sesuai berdasarkan kebutuhan penyetoran atau penyaluran barang.

Data titik setoran dan lokasi lain yang dikelola oleh KelolaKita tetap disimpan dalam database aplikasi. OpenStreetMap digunakan sebagai pendukung untuk menyediakan informasi geografis dan menampilkan peta pada antarmuka aplikasi.

Dokumentasi resmi:  
[OpenStreetMap API](https://wiki.openstreetmap.org/wiki/API)

### Nominatim

**Nominatim** digunakan oleh KelolaKita sebagai layanan **geocoding** untuk mengubah alamat atau nama lokasi menjadi koordinat geografis berupa latitude dan longitude. Layanan ini terutama digunakan ketika pengelola menambahkan atau memperbarui data titik setoran. Alamat yang dimasukkan akan diproses menggunakan Nominatim untuk memperoleh koordinat yang kemudian disimpan bersama data lokasi dan digunakan untuk menempatkan titik tersebut pada peta.

Penggunaan Nominatim membantu KelolaKita dalam menghubungkan informasi alamat dengan posisi geografis sehingga lokasi titik setoran dapat ditampilkan secara akurat pada peta dan digunakan dalam fitur pencarian lokasi.

Dokumentasi resmi:  
[Nominatim](https://nominatim.org/)

### Leaflet.js

**Leaflet.js** digunakan sebagai library JavaScript untuk menampilkan dan mengelola **peta interaktif** pada website KelolaKita. Leaflet memungkinkan aplikasi menampilkan marker lokasi, popup informasi, perpindahan dan pembesaran peta, serta interaksi lain yang dibutuhkan untuk membantu pengguna menemukan titik setoran dan lokasi penyaluran.

Dalam implementasinya, Leaflet digunakan bersama OpenStreetMap sebagai peta dasar. Koordinat yang diperoleh dari data lokasi KelolaKita maupun hasil geocoding Nominatim kemudian digunakan untuk menampilkan posisi masing-masing lokasi pada peta.

Dokumentasi resmi:  
[Leaflet.js](https://leafletjs.com/)

### Integrasi Public API

Ketiga teknologi tersebut digunakan secara saling melengkapi dalam fitur berbasis lokasi KelolaKita. **Nominatim** membantu memperoleh koordinat dari alamat, **OpenStreetMap** menyediakan peta dasar dan informasi geografis, sedangkan **Leaflet.js** digunakan untuk menampilkan peta tersebut secara interaktif pada website.

Integrasi ini terutama mendukung fitur pencarian dan pemilihan titik setoran, penampilan lokasi pada peta, serta proses penyaluran barang Reuse berdasarkan lokasi. KelolaKita tetap menyimpan data domain seperti titik setoran, jadwal, status penyetoran, dan informasi penyaluran pada database internal aplikasi.

---

## Ringkasan Fitur Utama

- Pemeriksaan awal barang sebelum diproses.
- Klasifikasi barang menjadi Recycle, Reduce, atau Reuse.
- Pilihan setor ke kantor atau titik setoran.
- Pemilihan lokasi dan jadwal penyetoran.
- Sistem penjemputan dari titik setoran.
- Peta untuk membantu pengguna menemukan lokasi.
- Penyaluran barang Reuse kepada pihak yang membutuhkan.
- Dukungan komunitas untuk proses Reduce dan Reuse.
- Edukasi mengenai pengelolaan dan pengurangan sampah.
- Informasi produk yang dapat digunakan kembali.
- Pengelolaan proses penanganan oleh pengelola KelolaKita.

---

## Tujuan Proyek

KelolaKita bertujuan membangun platform digital yang membantu masyarakat mengelola barang dan sampah dengan lebih terarah. Melalui proses pemeriksaan awal dan klasifikasi **Recycle, Reduce, dan Reuse**, setiap barang dapat diarahkan menuju metode penanganan yang sesuai dengan jenis dan kondisinya.

Platform ini diharapkan dapat membantu masyarakat membangun kebiasaan pengelolaan barang yang lebih bertanggung jawab sekaligus mempermudah proses penyetoran, penyaluran, dan edukasi mengenai pengelolaan sampah.
