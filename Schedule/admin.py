from django.contrib import admin

from Schedule.models import Pemeriksaan, Penjadwalan


@admin.register(Pemeriksaan)
class PemeriksaanAdmin(admin.ModelAdmin):
    list_display = ("nama_barang", "jenis_barang", "pengguna", "kategori_penanganan", "created_at")
    list_filter = ("kategori_penanganan",)
    search_fields = ("nama_barang", "jenis_barang")


@admin.register(Penjadwalan)
class PenjadwalanAdmin(admin.ModelAdmin):
    list_display = ("barang", "metode", "tanggal", "sesi", "contact", "created_at")
    list_filter = ("metode", "sesi", "tanggal")
    search_fields = ("barang__nama_barang", "contact")
