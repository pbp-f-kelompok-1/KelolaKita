from django import forms
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

from .models import Pemeriksaan


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput
    default_error_messages = {
        **forms.ImageField.default_error_messages,
        "required": "Unggah minimal 2 foto.",
    }

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                return super().clean(data, initial)
            return []

        uploads = data if isinstance(data, (list, tuple)) else [data]
        cleaned_uploads = [
            super(MultipleImageField, self).clean(upload, None)
            for upload in uploads
        ]
        for upload in cleaned_uploads:
            try:
                with Image.open(upload) as image:
                    image_format = image.format
                    image.verify()
            except (
                UnidentifiedImageError,
                OSError,
                ValueError,
                Image.DecompressionBombError,
            ) as error:
                raise ValidationError(
                    "File harus berupa gambar JPG atau PNG yang valid."
                ) from error
            finally:
                upload.seek(0)

            if image_format not in {"JPEG", "PNG"}:
                raise ValidationError("Format foto harus JPG atau PNG.")

        return cleaned_uploads


class PengajuanForm(forms.ModelForm):
    require_multiple_photos = True
    foto_barang = MultipleImageField(
        label="Foto barang",
        widget=MultipleImageInput(
            attrs={
                "id": "foto_barang",
                "multiple": True,
                "accept": "image/png, image/jpeg",
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

    def clean_foto_barang(self):
        fotos = self.cleaned_data["foto_barang"]
        if self.require_multiple_photos and len(fotos) < 2:
            raise ValidationError("Minimal harus mengunggah 2 foto.")
        return fotos

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
    require_multiple_photos = False
    foto_barang = MultipleImageField(
        label="Foto barang",
        required=False,
        widget=MultipleImageInput(
            attrs={
                "id": "foto_barang",
                "multiple": True,
                "accept": "image/png, image/jpeg",
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
