import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Location.models import Location
from Schedule.models import Pemeriksaan, Penjadwalan, phone_validator


def _date_offset(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


class PhoneValidatorTests(TestCase):
    def test_accepts_local_format(self):
        phone_validator("08123456789")

    def test_accepts_international_format(self):
        phone_validator("+628123456789")

    def test_rejects_wrong_prefix(self):
        with self.assertRaises(ValidationError):
            phone_validator("07123456789")

    def test_rejects_too_short(self):
        with self.assertRaises(ValidationError):
            phone_validator("08123")


class PemeriksaanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")

    def test_str_shows_nama_dan_kategori(self):
        item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Botol plastik",
            jenis_barang="Plastik",
            kondisi_barang="Masih bagus",
            kategori_penanganan="recycle",
        )
        self.assertEqual(str(item), "Botol plastik (Recycle)")

    def test_default_kategori_is_menunggu(self):
        item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Baju lama",
            jenis_barang="Tekstil",
            kondisi_barang="Sobek",
        )
        self.assertEqual(item.kategori_penanganan, "menunggu")


class PenjadwalanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.location = Location.objects.create(
            name="Bank Sampah Sejahtera",
            description="desc",
            address="Jl. Mawar",
            contact_person="08123456789",
            open_hours="08.00-16.00",
            province="DKI Jakarta",
            city="Jakarta",
            latitude=Decimal("-6.2000"),
            longitude=Decimal("106.8000"),
        )

    def _base_kwargs(self, **overrides):
        kwargs = dict(
            metode=Penjadwalan.Metode.kurir,
            tanggal=datetime.date.today() + datetime.timedelta(days=1),
            sesi=Penjadwalan.Sesi.pagi,
            nama_penerima="Budi",
            nomor_hp="08123456789",
        )
        kwargs.update(overrides)
        return kwargs

    def test_clean_raises_when_kurir_without_alamat(self):
        booking = Penjadwalan(**self._base_kwargs(metode=Penjadwalan.Metode.kurir, alamat_penjemputan=""))
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn("alamat_penjemputan", ctx.exception.message_dict)

    def test_clean_passes_when_kurir_with_alamat(self):
        booking = Penjadwalan(**self._base_kwargs(
            metode=Penjadwalan.Metode.kurir,
            alamat_penjemputan="Jl. Melati No. 5",
        ))
        booking.clean()

    def test_clean_raises_when_titik_without_lokasi(self):
        booking = Penjadwalan(**self._base_kwargs(metode=Penjadwalan.Metode.titik))
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn("lokasi_mitra", ctx.exception.message_dict)

    def test_clean_passes_when_titik_with_lokasi(self):
        booking = Penjadwalan(**self._base_kwargs(
            metode=Penjadwalan.Metode.titik,
            lokasi_mitra=self.location,
        ))
        booking.clean()

    def test_str_includes_barang_names(self):
        item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        booking = Penjadwalan.objects.create(**self._base_kwargs(
            metode=Penjadwalan.Metode.kurir,
            alamat_penjemputan="Jl. Melati No. 5",
        ))
        booking.barang.set([item])
        self.assertIn("Kardus", str(booking))


class ShowScheduleGetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.ready_item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Botol plastik",
            jenis_barang="Plastik",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Baju bekas",
            jenis_barang="Tekstil",
            kondisi_barang="Sobek",
            kategori_penanganan="menunggu",
        )

    def test_get_status_ok_and_uses_correct_template(self):
        response = self.client.get(reverse("show_schedule"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Schedule/schedule.html")

    def test_only_approved_unscheduled_items_are_listed(self):
        response = self.client.get(reverse("show_schedule"))
        items = list(response.context["items"])
        self.assertEqual(items, [self.ready_item])

    def test_item_disappears_once_scheduled(self):
        booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=datetime.date.today() + datetime.timedelta(days=1),
            sesi=Penjadwalan.Sesi.pagi,
            nama_penerima="Budi",
            nomor_hp="08123456789",
            alamat_penjemputan="Jl. Melati No. 5",
        )
        booking.barang.set([self.ready_item])

        response = self.client.get(reverse("show_schedule"))
        self.assertNotIn(self.ready_item, list(response.context["items"]))
