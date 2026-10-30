from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Profile
from penanganan.forms import EditPengajuanForm, HasilPemeriksaanForm, PengajuanForm
from penanganan.models import Pemeriksaan, FotoBarang


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

        foto = form.cleaned_data["foto_barang"]
        if foto:
            FotoBarang.objects.create(
                pemeriksaan=pemeriksaan,
                gambar=foto,
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
    pengelola = is_pengelola(request.user)
    if pengelola:
        daftar_pemeriksaan = Pemeriksaan.objects.all().order_by('-created_at')
    # Jika Pengguna biasa, hanya tampilkan riwayat barang miliknya sendiri
    else:
        daftar_pemeriksaan = Pemeriksaan.objects.filter(pengguna=request.user).order_by('-created_at')
        
    context = {
        "daftar_pemeriksaan": daftar_pemeriksaan,
        "is_pengelola": pengelola,
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
        foto_nueva = form.cleaned_data["foto_barang"]

        if foto_nueva:
            pemeriksaan.foto_barang.all().delete()
            FotoBarang.objects.create(pemeriksaan=pemeriksaan, gambar=foto_nueva)

        messages.success(request, "Pengajuan barang berhasil diperbarui!")
        return redirect("penanganan:daftar_pengajuan")

    # Tampilkan Form Edit (GET)
    context = {
        "pemeriksaan": pemeriksaan,
        "form": form,
        "active_nav": "penanganan",
    }
    return render(request, "penanganan/edit_pengajuan_form.html", context)