from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r"^(\+62|0)8[0-9]{7,11}$",
    message="Gunakan format nomor HP Indonesia, contoh: 08123456789 atau +628123456789.",
)


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
    nama_penerima = models.CharField(max_length=150)
    nomor_hp = models.CharField(max_length=20, validators=[phone_validator])
    alamat_penjemputan = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Wajib diisi jika metode adalah Dijemput kurir.",
    )
    lokasi_mitra = models.ForeignKey(
        "Location.Location", on_delete=models.PROTECT, null=True, blank=True,
        related_name="penjadwalan_set",
        help_text="Wajib diisi jika metode adalah Antar sendiri.",
    )
    notes = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.barang.nama_barang} - {self.tanggal} {self.sesi}"

    def clean(self):
        if self.metode == self.Metode.kurir and not self.alamat_penjemputan.strip():
            raise ValidationError({"alamat_penjemputan": "Alamat penjemputan wajib diisi untuk metode Dijemput kurir."})
        if self.metode == self.Metode.titik and not self.lokasi_mitra_id:
            raise ValidationError({"lokasi_mitra": "Lokasi mitra wajib dipilih untuk metode Antar sendiri."})
