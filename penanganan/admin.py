from django.contrib import admin

from penanganan.models import Pemeriksaan


@admin.register(Pemeriksaan)
class PemeriksaanAdmin(admin.ModelAdmin):
    list_display = ("nama_barang", "kategori_barang", "pengguna", "kategori_penanganan", "created_at")
    list_filter = ("kategori_penanganan",)
    search_fields = ("nama_barang", "kategori_barang")
