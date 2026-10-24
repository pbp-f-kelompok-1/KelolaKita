import uuid

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Location(models.Model):
    class Category(models.TextChoices) :
        bank_sampah = "bank_sampah", "Bank Sampah"
        panti_asuhan = "panti_asuhan", "Panti Asuhan"
        komunitas = "komunitas", "Komunitas"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    address = models.TextField()
    contact_person = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    open_hours = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    category = models.CharField(default=Category.bank_sampah, max_length=20, choices=Category.choices)

    def __str__(self):
        return self.name


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

    kategori_penanganan = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='Menunggu')
    rekomendasi_penanganan = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nama_barang} - {self.kategori_penanganan}"