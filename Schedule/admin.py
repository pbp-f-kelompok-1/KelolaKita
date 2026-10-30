from django.contrib import admin

from Schedule.models import Penjadwalan


@admin.register(Penjadwalan)
class PenjadwalanAdmin(admin.ModelAdmin):
    list_display = ("barang_list", "metode", "tanggal", "sesi", "nama_penerima", "nomor_hp", "created_at")
    list_filter = ("metode", "sesi", "tanggal")
    search_fields = ("barang__nama_barang", "nama_penerima", "nomor_hp")

    @admin.display(description="Barang")
    def barang_list(self, obj):
        return ", ".join(obj.barang.values_list("nama_barang", flat=True))
