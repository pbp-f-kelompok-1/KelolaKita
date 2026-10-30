from pathlib import Path
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from PIL import Image
from accounts.models import Profile
from penanganan.forms import EditPengajuanForm, HasilPemeriksaanForm, PengajuanForm
from penanganan.models import Pemeriksaan, FotoBarang


LEGACY_PENANGANAN_IMAGE_STORAGE = FileSystemStorage(
    location=Path(__file__).resolve().parent.parent / "static" / "img" / "penanganan",
)


def _store_foto_barang(upload):
    with Image.open(upload) as image:
        image_format = image.format
    upload.seek(0)
    extensions = {"JPEG": ".jpg", "PNG": ".png"}
    return default_storage.save(
        f"foto_pemeriksaan/{uuid4().hex}{extensions[image_format]}",
        upload,
    )


def _delete_foto_barang_files(fotos):
    for foto in fotos:
        if foto.gambar.name.startswith("foto_pemeriksaan/"):
            default_storage.delete(foto.gambar.name)
        elif "/" not in foto.gambar.name and "\\" not in foto.gambar.name:
            LEGACY_PENANGANAN_IMAGE_STORAGE.delete(foto.gambar.name)


def is_pengelola(user):
    return Profile.objects.filter(
        user=user,
        role=Profile.Role.MANAGER,
    ).exists()

# Membuat data pemeriksaan
@login_required
def tambah_pengajuan(request):
    form = (
        PengajuanForm(request.POST, request.FILES)
        if request.method == "POST"
        else PengajuanForm()
    )
    if request.method == "POST" and form.is_valid():
        pemeriksaan = form.save(commit=False)
        pemeriksaan.pengguna = request.user
        pemeriksaan.save()

        for foto in form.cleaned_data["foto_barang"]:
            FotoBarang.objects.create(
                pemeriksaan=pemeriksaan,
                gambar=_store_foto_barang(foto),
            )

        messages.success(request, "Pengajuan barang berhasil ditambahkan!")
        return redirect("penanganan:daftar_pengajuan")

    return render(request, "penanganan/pengajuan_form.html", {
        "form": form,
        "active_nav": "penanganan",
    })

# Melihat hasil pemeriksaan dan kategori penanganan
@login_required
def daftar_pengajuan(request):
    # Jika Pengelola, tampilkan semua data pengajuan untuk diperiksa
    if is_pengelola(request.user):
        daftar_pemeriksaan = Pemeriksaan.objects.all().order_by('-created_at')
    # Jika Pengguna biasa, hanya tampilkan riwayat barang miliknya sendiri
    else:
        daftar_pemeriksaan = Pemeriksaan.objects.filter(pengguna=request.user).order_by('-created_at')
        
    context = {
        "daftar_pemeriksaan": daftar_pemeriksaan,
        "active_nav": "penanganan",
    }
    return render(request, "penanganan/daftar_pengajuan.html", context)


# Mengubah hasil pemeriksaan apabila diperlukan
@login_required
def periksa_pengajuan(request, pk):
    # Cek apakah akun yang sedang login adalah pengelola; kalau bukan, hentikan permintaannya dengan 403
    if not is_pengelola(request.user):
        raise PermissionDenied
        
    # Ambil objek pemeriksaan berdasarkan ID-nya
    pemeriksaan = get_object_or_404(Pemeriksaan, pk=pk) 
    
    form = (
        HasilPemeriksaanForm(request.POST, instance=pemeriksaan)
        if request.method == "POST"
        else HasilPemeriksaanForm(instance=pemeriksaan)
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Hasil pemeriksaan berhasil disimpan!")
        return redirect("penanganan:daftar_pengajuan")
        
    context = {
        "pemeriksaan": pemeriksaan,
        "form": form,
        "active_nav": "penanganan",
    }
    return render(request, "penanganan/update_pemeriksaan.html", context)

# Menghapus data pemeriksaan sesuai kewenangan
@login_required
def hapus_pengajuan(request, pk):
    # Ambil objek pemeriksaan berdasarkan ID-nya
    pemeriksaan = get_object_or_404(Pemeriksaan, pk=pk)
    
    # Cek apakah user adalah Pengelola
    pengelola = is_pengelola(request.user)
    
    # Cek apakah user adalah pemilik barang DAN statusnya masih 'Menunggu'
    owner = pemeriksaan.pengguna == request.user
    menunggu = pemeriksaan.kategori_penanganan == 'Menunggu'
    
    # Jika bukan pengelola dan tidak memenuhi syarat sebagai pemilik, tolak aksesnya
    if not (pengelola or (owner and menunggu)):
        raise PermissionDenied
    
    # Proses Hapus
    if request.method == "POST":
        _delete_foto_barang_files(pemeriksaan.foto_barang.all())
        pemeriksaan.delete()
        messages.success(request, "Data pengajuan berhasil dihapus!")
        return redirect("penanganan:daftar_pengajuan")
        
    return redirect("penanganan:daftar_pengajuan")

@login_required
def edit_pengajuan(request, pk):
    pemeriksaan = get_object_or_404(Pemeriksaan, pk=pk)

    # Validasi Autentikasi & Kewenangan
    if pemeriksaan.pengguna != request.user:
        raise PermissionDenied
    
    if pemeriksaan.kategori_penanganan != 'Menunggu':
        messages.error(request, "Data yang sudah diproses tidak dapat diubah lagi.")
        return redirect("penanganan:daftar_pengajuan")

    form = (
        EditPengajuanForm(request.POST, request.FILES, instance=pemeriksaan)
        if request.method == "POST"
        else EditPengajuanForm(instance=pemeriksaan)
    )
    if request.method == "POST" and form.is_valid():
        pemeriksaan = form.save()
        fotos_nuevas = form.cleaned_data["foto_barang"]

        if fotos_nuevas:
            foto_lama = pemeriksaan.foto_barang.all()
            stored_names = [
                _store_foto_barang(foto)
                for foto in fotos_nuevas
            ]
            _delete_foto_barang_files(foto_lama)
            foto_lama.delete()

            for stored_name in stored_names:
                FotoBarang.objects.create(
                    pemeriksaan=pemeriksaan,
                    gambar=stored_name,
                )

        messages.success(request, "Pengajuan barang berhasil diperbarui!")
        return redirect("penanganan:daftar_pengajuan")

    # Tampilkan Form Edit (GET)
    context = {
        "pemeriksaan": pemeriksaan,
        "form": form,
        "active_nav": "penanganan",
    }
    return render(request, "penanganan/edit_pengajuan_form.html", context)