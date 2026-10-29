from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from penanganan.models import Pemeriksaan, FotoBarang

def is_pengelola(user):
    return user.groups.filter(name='Pengelola').exists()

# Membuat data pemeriksaan
@login_required(login_url="/login/")
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
            # Simpan data Pemeriksaan ke database
            pemeriksaan = Pemeriksaan.objects.create(
                pengguna=request.user,
                nama_barang=nama_barang,
                kategori_barang=kategori_barang,
                kondisi_barang=kondisi_barang,
                catatan_tambahan=catatan_tambahan
            )
            
            # Simpan setiap foto yang diunggah
            for foto in fotos:
                FotoBarang.objects.create(pemeriksaan=pemeriksaan, gambar=foto)
                
            messages.success(request, "Pengajuan barang berhasil ditambahkan!")
            return redirect("penanganan:daftar_pengajuan")
            
    return render(request, "penanganan/pengajuan_form.html")

# Melihat hasil pemeriksaan dan kategori penanganan
@login_required(login_url="/login/")
def daftar_pengajuan(request):
    # Jika Pengelola, tampilkan semua data pengajuan untuk diperiksa
    if is_pengelola(request.user):
        daftar_pemeriksaan = Pemeriksaan.objects.all().order_by('-created_at')
    # Jika Pengguna biasa, hanya tampilkan riwayat barang miliknya sendiri
    else:
        daftar_pemeriksaan = Pemeriksaan.objects.filter(pengguna=request.user).order_by('-created_at')
        
    context = {
        "daftar_pemeriksaan": daftar_pemeriksaan
    }
    return render(request, "penanganan/daftar_pengajuan.html", context)


# Mengubah hasil pemeriksaan apabila diperlukan
@login_required(login_url="/login/")
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
        "pemeriksaan": pemeriksaan
    }
    return render(request, "penanganan/update_pemeriksaan.html", context)

# Menghapus data pemeriksaan sesuai kewenangan
@login_required(login_url="/login/")
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

@login_required(login_url="/login/")
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
        # Ambil data teks baru (jika kosong, gunakan data lama sebagai fallback)
        pemeriksaan.nama_barang = request.POST.get('nama_barang', pemeriksaan.nama_barang)
        pemeriksaan.kategori_barang = request.POST.get('kategori_barang', pemeriksaan.kategori_barang)
        pemeriksaan.kondisi_barang = request.POST.get('kondisi_barang', pemeriksaan.kondisi_barang)
        pemeriksaan.catatan_tambahan = request.POST.get('catatan_tambahan', pemeriksaan.catatan_tambahan)
        
        pemeriksaan.save()

        # Update foto
        fotos_baru = request.FILES.getlist('foto_barang')
        if fotos_baru: 
            # Hapus foto lama dari database
            pemeriksaan.foto_barang.all().delete()
            
            # Simpan foto-foto baru
            for foto in fotos_baru:
                FotoBarang.objects.create(pemeriksaan=pemeriksaan, gambar=foto)

        messages.success(request, "Pengajuan barang berhasil diperbarui!")
        return redirect("penanganan:daftar_pengajuan")

    # Tampilkan Form Edit (GET)
    context = {
        "pemeriksaan": pemeriksaan
    }
    return render(request, "penanganan/edit_pengajuan_form.html", context)