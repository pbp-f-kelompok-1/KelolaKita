from django import forms
from django.forms import ModelForm

from Location.models import Location
from education.models import Article, Distribution, Event


class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ["title", "summary", "body", "category", "is_published", "published_at"]
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


class EventForm(ModelForm):
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
