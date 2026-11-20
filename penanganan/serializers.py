from rest_framework import serializers
from django.utils.html import strip_tags

from .models import Pemeriksaan


class PemeriksaanSerializer(serializers.ModelSerializer):
    def validate_nama_barang(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Nama barang tidak boleh kosong.")
        return value

    def validate_kategori_barang(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Kategori barang tidak boleh kosong.")
        return value

    def validate_catatan_tambahan(self, value):
        if value is None:
            return value
        return strip_tags(value).strip()

    def validate_rekomendasi_penanganan(self, value):
        if value is None:
            return value
        return strip_tags(value).strip()

    def validate_mitra_rekomendasi(self, value):
        if value is None:
            return value
        return strip_tags(value).strip()

    class Meta:
        model = Pemeriksaan
        fields = (
            "id",
            "pengguna",
            "nama_barang",
            "kategori_barang",
            "kondisi_barang",
            "catatan_tambahan",
            "kategori_penanganan",
            "rekomendasi_penanganan",
            "mitra_rekomendasi",
            "created_at",
            "updated_at",
        )