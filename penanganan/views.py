from pathlib import Path
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from PIL import Image, UnidentifiedImageError
from penanganan.models import Pemeriksaan, FotoBarang


PENANGANAN_IMAGE_STORAGE = FileSystemStorage(
    location=Path(__file__).resolve().parent.parent / "static" / "img" / "penanganan",
)


def _image_extension(upload):
    try:
        with Image.open(upload) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValueError("File harus berupa gambar JPG atau PNG yang valid.")
    finally:
        upload.seek(0)

    extensions = {"JPEG": ".jpg", "PNG": ".png"}
    if image_format not in extensions:
        raise ValueError("Format foto harus JPG atau PNG.")
    return extensions[image_format]


def _store_foto_barang(upload, extension):
    return PENANGANAN_IMAGE_STORAGE.save(f"{uuid4().hex}{extension}", upload)


def _delete_foto_barang_files(fotos):
    for foto in fotos:
        if "/" not in foto.gambar.name and "\\" not in foto.gambar.name:
            PENANGANAN_IMAGE_STORAGE.delete(foto.gambar.name)


def is_pengelola(user):
    return user.groups.filter(name='Pengelola').exists()

# Membuat data pemeriksaan
@login_required
def tambah_pengajuan(request):
    if request.method == "POST":
        # Mengambil input
        nama_barang = request.POST.get('nama_barang')
        kategori_barang = request.POST.get('kategori_barang')
        kondisi_barang = request.POST.get('kondisi_barang')
        catatan_tambahan = request.POST.get('catatan_tambahan')

        # Mengambil input file gambar
        fotos = request.FILES.getlist('foto_barang')

        # Validasi minimal 2 foto
        if len(fotos) < 2:
            messages.error(request, "Minimal harus mengunggah 2 foto agar pemeriksaan lebih akurat.")
        else:
            try:
                extensions = [_image_extension(foto) for foto in fotos]
            except ValueError as error:
                messages.error(request, str(error))
            else:
                stored_names = [
                    _store_foto_barang(foto, extension)
                    for foto, extension in zip(fotos, extensions)
                ]
                pemeriksaan = Pemeriksaan.objects.create(
                    pengguna=request.user,
                    nama_barang=nama_barang,
                    kategori_barang=kategori_barang,
                    kondisi_barang=kondisi_barang,
                    catatan_tambahan=catatan_tambahan
                )

                for stored_name in stored_names:
                    FotoBarang.objects.create(
                        pemeriksaan=pemeriksaan,
                        gambar=stored_name,
                    )

                messages.success(request, "Pengajuan barang berhasil ditambahkan!")
                return redirect("penanganan:daftar_pengajuan")
            
    return render(request, "penanganan/pengajuan_form.html", {
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
    
    if request.method == "POST":
        pemeriksaan.kategori_penanganan = request.POST.get('kategori_penanganan')
        pemeriksaan.rekomendasi_penanganan = request.POST.get('rekomendasi_penanganan')
        pemeriksaan.mitra_rekomendasi = request.POST.get('mitra_rekomendasi')
        
        pemeriksaan.save() # Menyimpan perubahan ke database
        messages.success(request, "Hasil pemeriksaan berhasil disimpan!")
        return redirect("penanganan:daftar_pengajuan")
        
    context = {
        "pemeriksaan": pemeriksaan,
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
        return redirect("pengajuan:daftar_pengajuan")

    # Proses Simpan Data (POST)
    if request.method == "POST":
        fotos_baru = request.FILES.getlist('foto_barang')
        try:
            extensions = [_image_extension(foto) for foto in fotos_baru]
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, "penanganan/edit_pengajuan_form.html", {
                "pemeriksaan": pemeriksaan,
                "active_nav": "penanganan",
            })

        # Ambil data teks baru (jika kosong, gunakan data lama sebagai fallback)
        pemeriksaan.nama_barang = request.POST.get('nama_barang', pemeriksaan.nama_barang)
        pemeriksaan.kategori_barang = request.POST.get('kategori_barang', pemeriksaan.kategori_barang)
        pemeriksaan.kondisi_barang = request.POST.get('kondisi_barang', pemeriksaan.kondisi_barang)
        pemeriksaan.catatan_tambahan = request.POST.get('catatan_tambahan', pemeriksaan.catatan_tambahan)
        
        pemeriksaan.save()

        # Update foto
        if fotos_baru: 
            foto_lama = pemeriksaan.foto_barang.all()
            stored_names = [
                _store_foto_barang(foto, extension)
                for foto, extension in zip(fotos_baru, extensions)
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
        "active_nav": "penanganan",
    }
    return render(request, "penanganan/edit_pengajuan_form.html", context)