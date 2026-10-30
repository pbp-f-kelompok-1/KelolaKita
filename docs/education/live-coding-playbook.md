# Panduan Live Coding — Education

Gunakan database lokal dan data sementara. Jangan menguji mutasi ke PWS. Tantangan di
bawah sengaja kecil dan bisa dijelaskan, bukan rewrite arsitektur.

> Solusi referensi dipisahkan di akhir. Saat latihan, coba dulu tanpa melihatnya.

---

## Level 1 — Mudah

### Tantangan 1.1 — Validasi ringkasan artikel

**Kebutuhan:** ringkasan artikel minimal 20 karakter. Form invalid harus menampilkan
error dan tidak membuat artikel.

**File:** `education/forms.py`, `education/tests.py`.

**Petunjuk:** tambahkan `clean_summary()` pada `ArticleForm`; gunakan
`forms.ValidationError`.

**Batasan:** jangan ubah model/migration; jangan melemahkan tes lama.

**Tes yang dijalankan:**

```bash
python manage.py test education.tests.FormTests
python manage.py test education.tests.CrudTests
```

**Kriteria berhasil:** form dengan summary pendek tidak valid; pesan error muncul;
POST invalid tidak menambah `Article`.

### Tantangan 1.2 — Tampilkan waktu selesai agenda

**Kebutuhan:** pada kartu agenda publik, tampilkan `–HH.MM` hanya jika `end_at` ada.

**File:** `templates/education/public_home.html` atau
`templates/education/public_event_list.html`.

**Petunjuk:** gunakan `{% if event.end_at %}` dan filter `date:"H.i"`; jangan
menampilkan tanda hubung jika kosong.

**Tes:** buat event dengan/tanpa `end_at`; cek HTML mengandung waktu selesai hanya pada
event yang memilikinya.

---

## Level 2 — Menengah

### Tantangan 2.1 — Filter status di dashboard staff

**Kebutuhan:** dashboard `/edukasi/kelola/?status=draft` hanya menampilkan artikel
draf; `?status=published` menampilkan artikel terbit; nilai tidak valid diabaikan.

**File:** `education/views.py` (`ManageDashboard`), `templates/education/manage_list.html`,
`education/tests.py`.

**Petunjuk:** baca `self.request.GET.get("status")`, validasi ke nilai yang
diizinkan, lalu filter `Article.objects.all()`. Filter hanya untuk daftar artikel;
jangan mengubah daftar agenda/penyaluran pada halaman yang sama.

**Batasan:** jangan mengubah route/model; tetap tampilkan semua artikel jika
parameter kosong/invalid.

**Tes:**

```bash
python manage.py test education.tests.ManageDashboardTests
```

**Kriteria berhasil:** filter status bekerja; state tabel lain tidak berubah;
test parameter valid/invalid; staff-only tetap berlaku.

### Tantangan 2.2 — Tes direct POST non-staff

**Kebutuhan:** buktikan user login non-staff tidak dapat POST ke create/update/delete
artikel dan record tidak berubah.

**File:** `education/tests.py` (`ManagementAccessTests`).

**Petunjuk:** login user non-staff, POST ke endpoint dengan payload kosong/valid,
assert 403, lalu assert record tetap ada.

**Kriteria:** tes gagal jika `StaffRequiredMixin` dilepas; jangan mengubah permission
aplikasi.

### Tantangan 2.3 — Cegah status `delivered` tanpa tanggal melalui form

**Kebutuhan:** form penyaluran menampilkan error `distributed_at` jika status
`delivered` tanpa tanggal.

**File:** `education/forms.py`, `education/tests.py`.

**Petunjuk:** `Distribution.clean()` sudah melakukan ini; pastikan `ModelForm`
memanggilnya dan tambahkan tes form. Jangan menduplikasi aturan di view.

---

## Level 3 — Menantang

### Tantangan 3.1 — Tangani slug race dengan aman

**Kebutuhan:** jika dua request membuat artikel berjudul sama hampir bersamaan,
jangan biarkan `IntegrityError` menjadi 500; ulangi pembuatan slug atau tangani error
dengan respons form yang jelas.

**File:** `education/models.py`, `education/forms.py`, tests.

**Petunjuk:** unique constraint pada `slug`; loop saat ini belum concurrency-safe.
Tangkap `IntegrityError` di titik simpan, lalu coba slug berikutnya dengan batas
percobaan. Jangan menelan error tanpa pesan.

**Tes:** simulasikan slug sudah ada; pastikan artikel baru mendapat suffix. Untuk race
nyata, gunakan transaksi/thread test jika lingkungan mendukung; jika tidak, dokumentasikan
batas pengujian.

### Tantangan 3.2 — Optimasi query setelah membuktikan N+1

**Kebutuhan:** ukur query pada dashboard/daftar publik, temukan query berulang nyata,
lalu tambahkan `select_related`/`prefetch_related` hanya pada relasi yang terbukti.

**File:** `education/views.py`.

**Catatan:** `published_events`, `public_home`, dan dashboard sudah memakai
`select_related` untuk event/distribusi. Jangan menambah optimasi tanpa bukti query.
Gunakan `django.test.utils.CaptureQueriesContext` atau `connection.queries` pada
`DEBUG=True`.

**Kriteria:** jumlah query turun; hasil halaman sama; test tetap lulus.

### Tantangan 3.3 — Hapus gambar orphan saat artikel dihapus

**Kebutuhan:** setelah artikel dihapus, file cover yang tidak dipakai artikel lain
tidak tertinggal di storage.

**File:** `education/models.py` atau view delete; tests.

**Petunjuk:** jangan hapus file jika masih direferensikan artikel lain (nama file
dapat dipakai ulang). Lakukan pengecekan referensi sebelum menghapus. Ini bukan
default Django; jelaskan trade-off dan backup.

---

## Solusi referensi

### Solusi 1.1

```python
def clean_summary(self):
    summary = self.cleaned_data["summary"]
    if len(summary.strip()) < 20:
        raise forms.ValidationError("Ringkasan minimal 20 karakter.")
    return summary
```

Tes: form dengan summary pendek `assertFalse`, `assertIn("summary", form.errors)`;
POST create dengan summary pendek tidak menambah count.

### Solusi 2.1 (garis besar)

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    status = self.request.GET.get("status")
    articles = Article.objects.all()
    if status == "draft":
        articles = articles.filter(is_published=False)
    elif status == "published":
        articles = articles.filter(is_published=True, published_at__lte=timezone.now())
    context["articles"] = articles
    context["selected_status"] = status if status in {"draft", "published"} else ""
    return context
```

Tambahkan pilihan filter di template dashboard dan test parameter valid/invalid.
Pastikan tidak mengubah queryset agenda/penyaluran.

### Solusi 2.2

```python
def test_non_staff_cannot_post_article_mutations(self):
    self.client.force_login(self.user)
    article = make_article()
    for url in [
        reverse("article_create"),
        reverse("article_update", args=[article.pk]),
        reverse("article_delete", args=[article.pk]),
    ]:
        self.assertEqual(self.client.post(url, {}).status_code, 403)
    self.assertTrue(Article.objects.filter(pk=article.pk).exists())
```

### Solusi 3.1 (garis besar)

Jangan mengandalkan `while` saja. Bungkus `save()` dengan retry `IntegrityError`,
hasilkan slug baru, batasi percobaan, dan lempar error yang bisa ditampilkan form.
Tes unit dapat mensimulasikan slug yang sudah ada; race test nyata memerlukan
transaksi/thread dan harus dipisahkan dari suite cepat.

## Checklist setelah live coding

- [ ] Perubahan minimal dan sesuai requirement.
- [ ] Tes positive + negative ditambahkan/dijalankan.
- [ ] Tidak ada permission yang dilemahkan.
- [ ] `python manage.py check` lulus.
- [ ] `git diff --check` bersih.
- [ ] Data demo sementara dibersihkan.
