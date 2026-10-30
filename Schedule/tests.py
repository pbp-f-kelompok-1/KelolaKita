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
from Schedule.views import SESSION_QUOTAS, _is_session_passed


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


class IsSessionPassedTests(TestCase):
    def test_future_date_is_never_passed(self):
        future_date = datetime.date.today() + datetime.timedelta(days=1)
        self.assertFalse(_is_session_passed(future_date, "pagi"))

    def test_today_before_session_end_is_not_passed(self):
        today = datetime.date.today()
        mocked_now = timezone.make_aware(datetime.datetime.combine(today, datetime.time(9, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            self.assertFalse(_is_session_passed(today, "pagi"))

    def test_today_after_session_end_is_passed(self):
        today = datetime.date.today()
        mocked_now = timezone.make_aware(datetime.datetime.combine(today, datetime.time(12, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            self.assertTrue(_is_session_passed(today, "pagi"))
            self.assertFalse(_is_session_passed(today, "siang"))


class ScheduleAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")

    def test_show_schedule_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("show_schedule"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('show_schedule')}",
        )

    def test_schedule_list_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("schedule_list"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('schedule_list')}",
        )

    def test_cancel_schedule_redirects_anonymous_user_to_login(self):
        response = self.client.post(reverse("cancel_schedule", args=[1]))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('cancel_schedule', args=[1])}",
        )


class ShowScheduleGetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.client.force_login(self.user)
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

    def test_other_users_items_are_not_listed(self):
        other_user = User.objects.create_user(username="ani", password="pass12345")
        other_item = Pemeriksaan.objects.create(
            pengguna=other_user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        response = self.client.get(reverse("show_schedule"))
        items = list(response.context["items"])
        self.assertNotIn(other_item, items)
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
        self.client.force_login(self.user)
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
            "metode": "kurir",
            "tanggal": _date_offset(3),
            "sesi": "pagi",
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
            metode="titik",
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
        payload = self._valid_kurir_payload(metode="titik", alamat_penjemputan="")
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(Penjadwalan.objects.count(), 0)

    def test_no_barang_selected_is_rejected(self):
        payload = self._valid_kurir_payload(barang=[])
        response = self.client.post(reverse("show_schedule"), payload)
        self.assertEqual(Penjadwalan.objects.count(), 0)

    def test_full_session_is_rejected(self):
        date_iso = _date_offset(3)
        for _ in range(SESSION_QUOTAS["siang"]):
            Penjadwalan.objects.create(
                metode=Penjadwalan.Metode.titik,
                tanggal=date_iso,
                sesi=Penjadwalan.Sesi.siang,
                nama_penerima="Lain",
                nomor_hp="08129999999",
                lokasi_mitra=self.location,
            )
        existing_count = Penjadwalan.objects.count()

        payload = self._valid_kurir_payload(tanggal=date_iso, sesi="siang")
        response = self.client.post(reverse("show_schedule"), payload)

        self.assertEqual(Penjadwalan.objects.count(), existing_count)
        messages = list(response.context["messages"])
        self.assertTrue(any("penuh" in str(m) for m in messages))

    def test_ajax_valid_submission_returns_json_with_remaining_items(self):
        response = self.client.post(
            reverse("show_schedule"),
            self._valid_kurir_payload(barang=[str(self.item.pk)]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(Penjadwalan.objects.count(), 1)
        remaining_pks = [item["pk"] for item in payload["items"]]
        self.assertNotIn(self.item.pk, remaining_pks)
        self.assertIn(self.item2.pk, remaining_pks)

    def test_ajax_invalid_submission_returns_json_error_without_creating(self):
        response = self.client.post(
            reverse("show_schedule"),
            self._valid_kurir_payload(nama_penerima=""),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(Penjadwalan.objects.count(), 0)

    def test_ajax_full_session_returns_json_error_without_creating(self):
        date_iso = _date_offset(3)
        for _ in range(SESSION_QUOTAS["siang"]):
            Penjadwalan.objects.create(
                metode=Penjadwalan.Metode.titik,
                tanggal=date_iso,
                sesi=Penjadwalan.Sesi.siang,
                nama_penerima="Lain",
                nomor_hp="08129999999",
                lokasi_mitra=self.location,
            )
        existing_count = Penjadwalan.objects.count()

        response = self.client.post(
            reverse("show_schedule"),
            self._valid_kurir_payload(tanggal=date_iso, sesi="siang"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("penuh", payload["message"])
        self.assertEqual(Penjadwalan.objects.count(), existing_count)

    def test_session_already_passed_today_is_rejected(self):
        today = datetime.date.today()
        mocked_now = timezone.make_aware(datetime.datetime.combine(today, datetime.time(12, 0)))
        payload = self._valid_kurir_payload(tanggal=today.isoformat(), sesi="pagi")
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(reverse("show_schedule"), payload)

        self.assertEqual(Penjadwalan.objects.count(), 0)
        messages = list(response.context["messages"])
        self.assertTrue(any("lewat" in str(m) for m in messages))

    def test_ajax_session_already_passed_today_returns_json_error(self):
        today = datetime.date.today()
        mocked_now = timezone.make_aware(datetime.datetime.combine(today, datetime.time(12, 0)))
        payload = self._valid_kurir_payload(tanggal=today.isoformat(), sesi="pagi")
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(
                reverse("show_schedule"), payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )

        self.assertEqual(response.status_code, 400)
        json_payload = response.json()
        self.assertFalse(json_payload["success"])
        self.assertIn("lewat", json_payload["message"])
        self.assertEqual(Penjadwalan.objects.count(), 0)

    def test_session_not_yet_passed_today_is_allowed(self):
        today = datetime.date.today()
        mocked_now = timezone.make_aware(datetime.datetime.combine(today, datetime.time(6, 0)))
        payload = self._valid_kurir_payload(tanggal=today.isoformat(), sesi="pagi")
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(reverse("show_schedule"), payload)
            self.assertRedirects(response, reverse("show_schedule"))

        self.assertEqual(Penjadwalan.objects.count(), 1)


class ScheduleListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.client.force_login(self.user)

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

    def test_other_users_booking_is_not_listed(self):
        other_user = User.objects.create_user(username="ani", password="pass12345")
        other_item = Pemeriksaan.objects.create(
            pengguna=other_user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        other_booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=datetime.date.today() + datetime.timedelta(days=5),
            sesi=Penjadwalan.Sesi.pagi,
            nama_penerima="Ani",
            nomor_hp="08129999999",
            alamat_penjemputan="Jl. Kenanga No. 1",
        )
        other_booking.barang.set([other_item])

        response = self.client.get(reverse("schedule_list"))
        bookings_shown = [row["booking"] for row in response.context["rows"]]
        self.assertNotIn(other_booking, bookings_shown)

    def test_no_filter_shows_all_bookings(self):
        past_booking = self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)
        future_booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5), Penjadwalan.Sesi.pagi)

        response = self.client.get(reverse("schedule_list"))
        bookings_shown = [row["booking"] for row in response.context["rows"]]
        self.assertEqual(bookings_shown, [past_booking, future_booking])
        self.assertEqual(response.context["filter_status"], "")

    def test_filter_by_terjadwal_hides_finished_bookings(self):
        self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)
        future_booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5), Penjadwalan.Sesi.pagi)

        response = self.client.get(reverse("schedule_list"), {"status": "terjadwal"})
        bookings_shown = [row["booking"] for row in response.context["rows"]]
        self.assertEqual(bookings_shown, [future_booking])
        self.assertEqual(response.context["filter_status"], "terjadwal")

    def test_filter_by_selesai_hides_upcoming_bookings(self):
        past_booking = self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)
        self._create_booking(datetime.date.today() + datetime.timedelta(days=5), Penjadwalan.Sesi.pagi)

        response = self.client.get(reverse("schedule_list"), {"status": "selesai"})
        bookings_shown = [row["booking"] for row in response.context["rows"]]
        self.assertEqual(bookings_shown, [past_booking])
        self.assertEqual(response.context["filter_status"], "selesai")

    def test_terkunci_counts_as_part_of_terjadwal_filter(self):
        session_date = datetime.date.today() + datetime.timedelta(days=10)
        locked_booking = self._create_booking(session_date, Penjadwalan.Sesi.pagi)
        self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)

        mocked_now = timezone.make_aware(datetime.datetime.combine(session_date, datetime.time(2, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.get(reverse("schedule_list"), {"status": "terjadwal"})

        bookings_shown = [row["booking"] for row in response.context["rows"]]
        self.assertEqual(bookings_shown, [locked_booking])

    def test_invalid_filter_value_is_ignored(self):
        past_booking = self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)
        future_booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5), Penjadwalan.Sesi.pagi)

        response = self.client.get(reverse("schedule_list"), {"status": "bukan-status-valid"})
        bookings_shown = [row["booking"] for row in response.context["rows"]]
        self.assertEqual(bookings_shown, [past_booking, future_booking])
        self.assertEqual(response.context["filter_status"], "")

    def test_filter_control_is_shown_even_when_filtered_result_is_empty(self):
        self._create_booking(datetime.date.today() - datetime.timedelta(days=1), Penjadwalan.Sesi.pagi)

        response = self.client.get(reverse("schedule_list"), {"status": "terjadwal"})
        self.assertEqual(list(response.context["rows"]), [])
        self.assertTrue(response.context["has_bookings"])
        self.assertContains(response, "Tidak ada jadwal dengan status ini.")


class CancelScheduleViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.client.force_login(self.user)
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

    def test_cancelled_booking_frees_up_its_item_for_rescheduling(self):
        booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5))
        self.client.post(reverse("cancel_schedule", args=[booking.pk]))

        response = self.client.get(reverse("show_schedule"))
        self.assertIn(self.item, list(response.context["items"]))

    def test_cancelled_booking_frees_up_its_session_quota(self):
        tanggal = datetime.date.today() + datetime.timedelta(days=5)
        booking = self._create_booking(tanggal, sesi=Penjadwalan.Sesi.siang)
        self.client.post(reverse("cancel_schedule", args=[booking.pk]))

        response = self.client.get(reverse("show_schedule"))
        self.assertEqual(response.context["availability"][tanggal.isoformat()]["siang"], SESSION_QUOTAS["siang"])

    def test_cancel_nonexistent_booking_returns_404(self):
        response = self.client.post(reverse("cancel_schedule", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_cancel_other_users_booking_returns_404_and_keeps_booking(self):
        other_user = User.objects.create_user(username="ani", password="pass12345")
        other_item = Pemeriksaan.objects.create(
            pengguna=other_user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        other_booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=datetime.date.today() + datetime.timedelta(days=5),
            sesi=Penjadwalan.Sesi.pagi,
            nama_penerima="Ani",
            nomor_hp="08129999999",
            alamat_penjemputan="Jl. Kenanga No. 1",
        )
        other_booking.barang.set([other_item])

        response = self.client.post(reverse("cancel_schedule", args=[other_booking.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Penjadwalan.objects.filter(pk=other_booking.pk).exists())

    def test_ajax_cancel_before_cutoff_returns_json_success(self):
        booking = self._create_booking(datetime.date.today() + datetime.timedelta(days=5))
        response = self.client.post(
            reverse("cancel_schedule", args=[booking.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertFalse(Penjadwalan.objects.filter(pk=booking.pk).exists())

    def test_ajax_cancel_within_cutoff_returns_json_error_and_keeps_booking(self):
        session_date = datetime.date.today() + datetime.timedelta(days=10)
        booking = self._create_booking(session_date)

        mocked_now = timezone.make_aware(datetime.datetime.combine(session_date, datetime.time(2, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(
                reverse("cancel_schedule", args=[booking.pk]),
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertTrue(Penjadwalan.objects.filter(pk=booking.pk).exists())


class EditScheduleViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budi", password="pass12345")
        self.client.force_login(self.user)
        self.item = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Botol plastik",
            jenis_barang="Plastik",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        self.booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=datetime.date.today() + datetime.timedelta(days=5),
            sesi=Penjadwalan.Sesi.pagi,
            nama_penerima="Budi",
            nomor_hp="08123456789",
            alamat_penjemputan="Jl. Melati No. 5",
        )
        self.booking.barang.set([self.item])

    def _valid_payload(self, **overrides):
        payload = {
            "metode": "kurir",
            "tanggal": _date_offset(6),
            "sesi": "pagi",
            "nama_penerima": "Budi Santoso",
            "nomor_hp": "08123456789",
            "alamat_penjemputan": "Jl. Mawar No. 9",
            "notes": "",
            "barang": [str(self.item.pk)],
        }
        payload.update(overrides)
        return payload

    def test_get_renders_edit_form_with_existing_values(self):
        response = self.client.get(reverse("edit_schedule", args=[self.booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Schedule/schedule_edit.html")
        self.assertEqual(response.context["nama_penerima_value"], "Budi")

    def test_post_updates_booking_details(self):
        response = self.client.post(reverse("edit_schedule", args=[self.booking.pk]), self._valid_payload())
        self.assertRedirects(response, reverse("schedule_list"))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.nama_penerima, "Budi Santoso")
        self.assertEqual(self.booking.alamat_penjemputan, "Jl. Mawar No. 9")
        self.assertEqual(self.booking.tanggal.isoformat(), _date_offset(6))

    def test_edit_rejected_within_cutoff_window(self):
        session_date = datetime.date.today() + datetime.timedelta(days=10)
        self.booking.tanggal = session_date
        self.booking.save()

        mocked_now = timezone.make_aware(datetime.datetime.combine(session_date, datetime.time(2, 0)))
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(reverse("edit_schedule", args=[self.booking.pk]), self._valid_payload())

        self.assertRedirects(response, reverse("schedule_list"))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.nama_penerima, "Budi")

    def test_edit_rejected_for_already_cancelled_booking(self):
        booking_pk = self.booking.pk
        self.booking.delete()

        response = self.client.post(reverse("edit_schedule", args=[booking_pk]), self._valid_payload())
        self.assertEqual(response.status_code, 404)

    def test_edit_other_users_booking_returns_404(self):
        other_user = User.objects.create_user(username="ani", password="pass12345")
        other_item = Pemeriksaan.objects.create(
            pengguna=other_user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        other_booking = Penjadwalan.objects.create(
            metode=Penjadwalan.Metode.kurir,
            tanggal=datetime.date.today() + datetime.timedelta(days=5),
            sesi=Penjadwalan.Sesi.pagi,
            nama_penerima="Ani",
            nomor_hp="08129999999",
            alamat_penjemputan="Jl. Kenanga No. 1",
        )
        other_booking.barang.set([other_item])

        response = self.client.get(reverse("edit_schedule", args=[other_booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_edit_rejected_when_target_session_is_full_by_another_booking(self):
        other_user = User.objects.create_user(username="ani", password="pass12345")
        other_item = Pemeriksaan.objects.create(
            pengguna=other_user,
            nama_barang="Kardus",
            jenis_barang="Kertas",
            kondisi_barang="Baik",
            kategori_penanganan="recycle",
        )
        full_date = _date_offset(6)
        for _ in range(SESSION_QUOTAS["siang"]):
            Penjadwalan.objects.create(
                metode=Penjadwalan.Metode.kurir,
                tanggal=full_date,
                sesi=Penjadwalan.Sesi.siang,
                nama_penerima="Ani",
                nomor_hp="08129999999",
                alamat_penjemputan="Jl. Kenanga No. 1",
            ).barang.set([other_item])

        payload = self._valid_payload(tanggal=full_date, sesi="siang")
        response = self.client.post(reverse("edit_schedule", args=[self.booking.pk]), payload)

        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.sesi, Penjadwalan.Sesi.pagi)

    def test_edit_without_changing_session_does_not_count_itself_as_full(self):
        payload = self._valid_payload(tanggal=self.booking.tanggal.isoformat(), sesi="pagi")
        response = self.client.post(reverse("edit_schedule", args=[self.booking.pk]), payload)
        self.assertRedirects(response, reverse("schedule_list"))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.nama_penerima, "Budi Santoso")

    def test_edit_rejected_when_moved_to_already_passed_session_today(self):
        today = datetime.date.today()
        mocked_now = timezone.make_aware(datetime.datetime.combine(today, datetime.time(12, 0)))
        payload = self._valid_payload(tanggal=today.isoformat(), sesi="pagi")
        with patch("django.utils.timezone.now", return_value=mocked_now):
            response = self.client.post(reverse("edit_schedule", args=[self.booking.pk]), payload)

        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.nama_penerima, "Budi")
