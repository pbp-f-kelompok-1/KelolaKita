from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from penanganan.models import Pemeriksaan

phone_validator = RegexValidator(
    regex=r"^(\+62|0)8[0-9]{7,11}$",
    message="Gunakan format nomor HP Indonesia, contoh: 08123456789 atau +628123456789.",
)


class Penjadwalan(models.Model):
    class Metode(models.TextChoices):
        kurir = "kurir", "Dijemput kurir"
        titik = "titik", "Antar sendiri"

    class Sesi(models.TextChoices):
        pagi = "pagi", "Pagi"
        siang = "siang", "Siang"

    barang = models.ManyToManyField(Pemeriksaan, related_name="penjadwalan_set")
    metode = models.CharField(max_length=10, choices=Metode.choices)
    tanggal = models.DateField()
    sesi = models.CharField(max_length=10, choices=Sesi.choices)
    nama_penerima = models.CharField(max_length=150)
    nomor_hp = models.CharField(max_length=20, validators=[phone_validator])
    alamat_penjemputan = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Wajib diisi jika metode adalah Dijemput kurir.",
    )
    alamat_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    alamat_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    lokasi_mitra = models.ForeignKey(
        "Location.Location", on_delete=models.PROTECT, null=True, blank=True,
        related_name="penjadwalan_set",
        help_text="Wajib diisi jika metode adalah Antar sendiri.",
    )
    notes = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        nama = ", ".join(self.barang.values_list("nama_barang", flat=True)) if self.pk else ""
        return f"{nama or 'Penjadwalan'} - {self.tanggal} {self.sesi}"

    def clean(self):
        if self.metode == self.Metode.kurir and not self.alamat_penjemputan.strip():
            raise ValidationError({"alamat_penjemputan": "Alamat penjemputan wajib diisi untuk metode Dijemput kurir."})
        if self.metode == self.Metode.titik and not self.lokasi_mitra_id:
            raise ValidationError({"lokasi_mitra": "Lokasi mitra wajib dipilih untuk metode Antar sendiri."})
