from django import forms
from django.forms import ModelForm

from Location.models import Location
from education.models import (
    ARTICLE_CATEGORY_LABELS,
    Article,
    Distribution,
    Event,
    validate_article_image,
)


class ArticleForm(ModelForm):
    """Form artikel staff dengan validasi gambar dan label kategori publik."""

    image = forms.ImageField(
        label="Gambar artikel",
        required=False,
        help_text="Unggah gambar utama yang sesuai dengan isi artikel. Disarankan berukuran 1.200 × 675 piksel (rasio 16:9), dengan ukuran file maksimal 5 MB.",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "class": "field-input",
            }
        ),
        error_messages={"invalid_image": "File gambar tidak dapat dibaca."},
        validators=[validate_article_image],
    )

    class Meta:
        model = Article
        fields = ["title", "summary", "body", "category", "image", "is_published", "published_at"]
        labels = {
            "title": "Judul artikel",
            "summary": "Ringkasan",
            "body": "Isi artikel",
            "category": "Kategori",
            "is_published": "Terbitkan",
            "published_at": "Tanggal terbit",
        }
        widgets = {
            "published_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [
            (value, ARTICLE_CATEGORY_LABELS.get(value, label))
            for value, label in self.fields["category"].choices
        ]


class EventForm(ModelForm):
    """Form agenda; hanya lokasi aktif yang dapat dipilih untuk agenda baru."""

    class Meta:
        model = Event
        fields = ["title", "description", "start_at", "end_at", "location", "is_published"]
        labels = {
            "title": "Nama agenda",
            "description": "Deskripsi",
            "start_at": "Mulai",
            "end_at": "Selesai (opsional)",
            "location": "Lokasi",
            "is_published": "Terbitkan",
        }
        widgets = {
            "start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = Location.objects.filter(pk=self.instance.location_id) if self.instance.pk else Location.objects.none()
        self.fields["location"].queryset = (Location.objects.filter(is_active=True) | current).order_by("name")


class DistributionForm(ModelForm):
    """Form penyaluran yang dibatasi ke tujuan panti/komunitas aktif."""

    class Meta:
        model = Distribution
        fields = ["item_name", "description", "quantity", "destination", "status", "distributed_at"]
        labels = {
            "item_name": "Nama barang",
            "description": "Keterangan",
            "quantity": "Jumlah",
            "destination": "Tujuan penyaluran",
            "status": "Status",
            "distributed_at": "Tanggal penyaluran",
        }
        widgets = {
            "distributed_at": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = Location.objects.filter(pk=self.instance.destination_id) if self.instance.pk else Location.objects.none()
        active = Location.objects.filter(is_active=True, category__in=[Location.Category.panti_asuhan, Location.Category.komunitas])
        self.fields["destination"].queryset = (active | current).order_by("name")
