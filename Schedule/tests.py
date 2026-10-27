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


class ShowSchedulePostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Botol plastik",
            jenis_barang="Plastik",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        self.item2 = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="reuse",
        )
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

    def _valid_kurir_payload(self, **overrides):
        payload = {
            "method": "kurir",
            "date": _date_offset(3),
            "session": "pagi",
            "nama_penerima": "Budi",
            "nomor_hp": "08123456789",
            "alamat_penjemputan": "Jl. Melati No. 5",
            "notes": "",
            "barang": [str(self.item.pk)],
        }
        payload.update(overrides)
        return payload

    def test_valid_kurir_submission_creates_booking(self):
        response = self.client.post(reverse("show_schedule"), self._valid_kurir_payload())
        self.assertRedirects(response, reverse("show_schedule"))
        self.assertEqual(Penjadwalan.objects.count(), 1)
        booking = Penjadwalan.objects.first()
        self.assertEqual(booking.metode, "kurir")
        self.assertEqual(booking.alamat_penjemputan, "Jl. Melati No. 5")
        self.assertEqual(list(booking.barang.all()), [self.item])

    def test_valid_titik_submission_creates_booking(self):
        payload = self._valid_kurir_payload(
            method="titik",
            lokasi_mitra=str(self.location.pk),
            alamat_penjemputan="",
        )
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertRedirects(response, reverse("show_schedule"))
        booking = Penjadwalan.objects.get()
        self.assertEqual(booking.metode, "titik")
        self.assertEqual(booking.lokasi_mitra, self.location)

    def test_multi_item_submission_links_all_items(self):
        payload = self._valid_kurir_payload(barang=[str(self.item.pk), str(self.item2.pk)])
        self.client.post(reverse("show_schedule"), payload)
        booking = Penjadwalan.objects.get()
        self.assertEqual(set(booking.barang.all()), {self.item, self.item2})

    def test_missing_nama_penerima_shows_error_and_creates_nothing(self):
        payload = self._valid_kurir_payload(nama_penerima="")
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Penjadwalan.objects.count(), 0)
        messages = list(response.context["messages"])
        self.assertTrue(any("Lengkapi" in str(m) for m in messages))

    def test_invalid_phone_shows_error_and_creates_nothing(self):
        payload = self._valid_kurir_payload(nomor_hp="12345")
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(Penjadwalan.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_kurir_without_alamat_is_rejected(self):
        payload = self._valid_kurir_payload(alamat_penjemputan="")
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(Penjadwalan.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_titik_without_lokasi_is_rejected(self):
        payload = self._valid_kurir_payload(method="titik", alamat_penjemputan="")
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(Penjadwalan.objects.count(), 0)

    def test_no_barang_selected_is_rejected(self):
        payload = self._valid_kurir_payload(barang=[])
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(Penjadwalan.objects.count(), 0)

    def test_full_session_is_rejected(self):
        date_iso = _date_offset(3)
        Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.titik,
            tanggal=date_iso,
            sesi=Penjadwalan.Sesi.siang,
            nama_penerima="Lain",
            nomor_hp="08129999999",
            lokasi_mitra=self.location,
        )

        payload = self._valid_kurir_payload(date=date_iso, session="siang")
        response = self.client.post(reverse("show_schedule"), payload)

        self.assertEqual(Penjadwalan.objects.count(), 1)
        messages = list(response.context["messages"])
        self.assertTrue(any("penuh" in str(m) for m in messages))


class ScheduleListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")

    def _create_booking(self, tanggal, sesi):
        item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Botol plastik",
            jenis_barang="Plastik",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=tanggal,
            sesi=sesi,
            nama_penerima="Budi",
            nomor_hp="08123456789",
            alamat_penjemputan="Jl. Melati No. 5",
        )
        booking.barang.set([item])
        return booking

    def test_empty_state_message(self):
        response = self.client.get(reverse("schedule_list"))
        self.assertContains(response, "Belum ada jadwal")

    def test_future_booking_is_terjadwal_and_cancelable(self):
        self._create_booking(datetime.date.today() + datetime.timedelta(days=5), Penjadwalan.Sesi.pagi)
        response = self.client.get(reverse("schedule_list"))
        row = response.context["rows"][0]
        self.assertEqual(row["status"], "terjadwal")
        self.assertTrue(row["can_cancel"])

    def test_past_booking_is_selesai_and_not_cancelable(self):
        self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)
        response = self.client.get(reverse("schedule_list"))
        row = response.context["rows"][0]
        self.assertEqual(row["status"], "selesai")
        self.assertFalse(row["can_cancel"])

    def test_booking_within_cutoff_window_is_terkunci(self):
        session_date = datetime.date.today() + datetime.timedelta(days=10)
        self._create_booking(session_date, Penjadwalan.Sesi.pagi)

        mocked_now = timezone.make_aware(datetime.datetime.combine(session_date, datetime.time(2, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.get(reverse("schedule_list"))
            row = response.context["rows"][0]

        self.assertEqual(row["status"], "terkunci")
        self.assertFalse(row["can_cancel"])


class CancelScheduleViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Botol plastik",
            jenis_barang="Plastik",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )

    def _create_booking(self, tanggal, sesi=Penjadwalan.Sesi.pagi):
        booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=tanggal,
            sesi=sesi,
            nama_penerima="Budi",
            nomor_hp="08123456789",
            alamat_penjemputan="Jl. Melati No. 5",
        )
        booking.barang.set([self.item])
        return booking

    def test_cancel_deletes_booking_before_cutoff(self):
        booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5))
        response = self.client.post(reverse("cancel_schedule", args=[booking.pk]))
        self.assertRedirects(response, reverse("schedule_list"))
        self.assertFalse(Penjadwalan.objects.filter(pk=booking.pk).exists())

    def test_cancel_rejected_within_cutoff_window(self):
        session_date = datetime.date.today() + datetime.timedelta(days=10)
        booking = self._create_booking(session_date)

        mocked_now = timezone.make_aware(datetime.datetime.combine(session_date, datetime.time(2, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(reverse("cancel_schedule", args=[booking.pk]))

        self.assertRedirects(response, reverse("schedule_list"))
        self.assertTrue(Penjadwalan.objects.filter(pk=booking.pk).exists())

    def test_get_request_does_not_delete_booking(self):
        booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5))
        self.client.get(reverse("cancel_schedule", args=[booking.pk]))
        self.assertTrue(Penjadwalan.objects.filter(pk=booking.pk).exists())

    def test_cancel_nonexistent_booking_returns_404(self):
        response = self.client.post(reverse("cancel_schedule", args=[999999]))
        self.assertEqual(response.status_code, 404)
