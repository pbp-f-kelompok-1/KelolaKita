from django import forms

from .models import Pemeriksaan


class PengajuanForm(forms.ModelForm):
    foto_barang = forms.ImageField(
        label="Foto barang",
        widget=forms.ClearableFileInput(
            attrs={
                "id": "foto_barang",
                "accept": "image/*",
                "class": "absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20",
                "onchange": "previewImages(event)",
            }
        ),
    )
    kategori_barang = forms.ChoiceField(
        choices=(
            ("", "Pilih Kategori"),
            ("Furnitur rumah", "Furnitur rumah"),
            ("Elektronik", "Elektronik"),
            ("Pakaian", "Pakaian"),
            ("Lainnya", "Lainnya"),
        ),
    )
    kondisi_barang = forms.ChoiceField(
        choices=Pemeriksaan.PILIHAN_KONDISI,
        widget=forms.RadioSelect(
            attrs={"class": "w-3.5 h-3.5 md:w-4 md:h-4 text-[#2e7d32]"}
        ),
    )

    class Meta:
        model = Pemeriksaan
        fields = (
            "nama_barang",
            "kategori_barang",
            "kondisi_barang",
            "catatan_tambahan",
        )
        widgets = {
            "nama_barang": forms.TextInput(attrs={"placeholder": "Meja belajar kayu"}),
            "kondisi_barang": forms.RadioSelect(
                attrs={"class": "w-3.5 h-3.5 md:w-4 md:h-4 text-[#2e7d32]"}
            ),
            "catatan_tambahan": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Kokoh, ada goresan ringan..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "text-sm")


class EditPengajuanForm(PengajuanForm):
    foto_barang = forms.ImageField(
        label="Foto barang",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "id": "foto_barang",
                "accept": "image/*",
                "class": "absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20",
                "onchange": "previewImages(event)",
            }
        ),
    )


class HasilPemeriksaanForm(forms.ModelForm):
    class Meta:
        model = Pemeriksaan
        fields = (
            "kategori_penanganan",
            "mitra_rekomendasi",
            "rekomendasi_penanganan",
        )
        widgets = {
            "mitra_rekomendasi": forms.TextInput(
                attrs={"placeholder": "Contoh: Komunitas Ruang Tumbuh"}
            ),
            "rekomendasi_penanganan": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Berikan alasan atau instruksi penanganan selanjutnya...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kategori_penanganan"].choices = (
            ("Menunggu", "Menunggu Pemeriksaan"),
            ("Reuse", "Reuse (Guna Ulang)"),
            ("Recycle", "Recycle (Daur Ulang)"),
            ("Reduce", "Reduce (Pengurangan)"),
        )
        self.fields["kategori_penanganan"].widget.attrs.update(
            {
                "class": "bg-[#e8f5e9] border-[#81c784] font-bold text-[#1f5a23] text-sm",
            }
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "text-sm")
