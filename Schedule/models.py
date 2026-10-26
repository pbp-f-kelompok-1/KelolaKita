from django.contrib.auth.models import User
from django.db import models


class Pemeriksaan(models.Model):
    KATEGORI_CHOICES = [
        ('menunggu', 'Menunggu'),
        ('recycle', 'Recycle'),
        ('reduce', 'Reduce'),
        ('reuse', 'Reuse'),
    ]

    pengguna = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_barang = models.CharField(max_length=255)
    jenis_barang = models.CharField(max_length=100)
    kondisi_barang = models.TextField()
    kategori_penanganan = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='menunggu')
    rekomendasi_penanganan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nama_barang} ({self.get_kategori_penanganan_display()})"


class Penjadwalan(models.Model):
    class Metode(models.TextChoices):
        kurir = "kurir", "Dijemput kurir"
        titik = "titik", "Antar sendiri"

    class Sesi(models.TextChoices):
        pagi = "pagi", "Pagi"
        siang = "siang", "Siang"

    barang = models.ForeignKey(Pemeriksaan, on_delete=models.PROTECT, related_name="penjadwalan_set")
    metode = models.CharField(max_length=10, choices=Metode.choices)
    tanggal = models.DateField()
    sesi = models.CharField(max_length=10, choices=Sesi.choices)
    contact = models.CharField(max_length=255)
    notes = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.barang.nama_barang} - {self.tanggal} {self.sesi}"
