import uuid
from django.db import models
from django.contrib.auth.models import User

class Pemeriksaan(models.Model):
    # Kondisi barang
    PILIHAN_KONDISI = [
        ('Sangat baik', 'Sangat baik'),
        ('Layak pakai', 'Layak pakai'),
        ('Perlu perbaikan', 'Perlu perbaikan'),
        ('Rusak', 'Rusak'),
    ]

    # Kategori penanganan
    PILIHAN_KATEGORI_PENANGANAN = [
        ('Menunggu', 'Menunggu'),
        ('Recycle', 'Recycle'),
        ('Reduce', 'Reduce'),
        ('Reuse', 'Reuse'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relasi ke pengguna
    pengguna = models.ForeignKey(User, related_name='pemeriksaan_penanganan', on_delete=models.CASCADE)

    # Data pengajuan barang dari pengguna
    nama_barang = models.CharField(max_length=255)
    kategori_barang = models.CharField(max_length=100)
    kondisi_barang = models.CharField(max_length=50, choices=PILIHAN_KONDISI)
    catatan_tambahan = models.TextField(blank=True, null=True)

    # Hasil pemeriksaan
    kategori_penanganan = models.CharField(max_length=20, choices=PILIHAN_KATEGORI_PENANGANAN, default='Menunggu')
    rekomendasi_penanganan = models.TextField(blank=True, null=True)
    mitra_rekomendasi = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nama_barang} - {self.kategori_penanganan}"


class FotoBarang(models.Model):
    pemeriksaan = models.ForeignKey(Pemeriksaan, related_name='foto_barang', on_delete=models.CASCADE)
    gambar = models.ImageField(upload_to='static/img/')
    diunggah_pada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto untuk {self.pemeriksaan.nama_barang}"