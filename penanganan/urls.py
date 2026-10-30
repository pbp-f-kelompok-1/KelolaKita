from django.urls import path
from . import views

app_name = "penanganan"

urlpatterns = [
    path("", views.daftar_pengajuan, name="daftar_pengajuan"),
    path("tambah/", views.tambah_pengajuan, name="tambah_pengajuan"),
    path("<uuid:pk>/periksa/", views.periksa_pengajuan, name="periksa_pengajuan"),
    path("<uuid:pk>/edit/", views.edit_pengajuan, name="edit_pengajuan"),
    path("<uuid:pk>/hapus/", views.hapus_pengajuan, name="hapus_pengajuan"),
]