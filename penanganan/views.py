from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from penanganan.models import Pemeriksaan, FotoBarang

def is_pengelola(user):
    return user.groups.filter(name='Pengelola').exists()

# Membuat data pemeriksaan
#@login_required(login_url="/login/")
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
#@login_required(login_url="/login/")
def daftar_pengajuan(request):
    # Jika Pengelola, tampilkan semua data pengajuan untuk diperiksa
    daftar_pemeriksaan = Pemeriksaan.objects.all().order_by('-created_at')
    #if is_pengelola(request.user):
    # Jika Pengguna biasa, hanya tampilkan riwayat barang miliknya sendiri
#    else:
 #       daftar_pemeriksaan = Pemeriksaan.objects.filter(pengguna=request.user).order_by('-created_at')
        
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