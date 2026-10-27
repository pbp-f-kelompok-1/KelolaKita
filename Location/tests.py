from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from education.models import Event
from Location.models import Location


def make_location(**overrides):
    data = {
        "name": "Lokasi Uji",
        "description": "Deskripsi lokasi",
        "address": "Jl. Uji No. 1",
        "contact_person": "081200000001",
        "open_hours": "08.00-16.00",
        "province": "DKI Jakarta",
        "city": "Jakarta Selatan",
        "latitude": "-6.2615",
        "longitude": "106.8106",
        "category": Location.Category.panti_asuhan,
    }
    data.update(overrides)
    return Location.objects.create(**data)


def location_payload(**overrides):
    data = {
        "name": "Lokasi Baru",
        "description": "Lokasi hasil uji",
        "address": "Jl. Baru No. 2",
        "province": "DKI Jakarta",
        "city": "Jakarta Pusat",
        "open_hours": "09.00-17.00",
        "contact_person": "081200000002",
        "latitude": "-6.2000",
        "longitude": "106.8000",
        "category": Location.Category.komunitas,
    }
    data.update(overrides)
    return data


class LocationManagementAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.user = User.objects.create_user("user", password="x")
        self.inactive_staff = User.objects.create_user(
            "inactive-staff", password="x", is_staff=True, is_active=False
        )
        self.location = make_location()

    def test_anonymous_cannot_open_create_form(self):
        response = self.client.get(reverse("create_location"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_anonymous_post_does_not_create_location(self):
        response = self.client.post(reverse("create_location"), location_payload())

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Location.objects.filter(name="Lokasi Baru").exists())

    def test_non_staff_cannot_open_or_post_create(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("create_location")).status_code, 403)
        response = self.client.post(reverse("create_location"), location_payload())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Location.objects.filter(name="Lokasi Baru").exists())

    def test_inactive_staff_is_forbidden(self):
        self.client.force_login(self.inactive_staff)

        response = self.client.get(reverse("create_location"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_staff_can_open_and_create_location(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse("create_location")).status_code, 200)
        response = self.client.post(reverse("create_location"), location_payload())

        self.assertRedirects(response, reverse("show_location"))
        self.assertTrue(Location.objects.filter(name="Lokasi Baru").exists())

    def test_anonymous_cannot_delete_location(self):
        response = self.client.post(reverse("delete_location", args=[self.location.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])
        self.assertTrue(Location.objects.filter(pk=self.location.pk).exists())

    def test_non_staff_cannot_delete_location(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("delete_location", args=[self.location.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Location.objects.filter(pk=self.location.pk).exists())

    def test_staff_get_does_not_delete_location(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("delete_location", args=[self.location.pk]))

        self.assertRedirects(response, reverse("show_location"))
        self.assertTrue(Location.objects.filter(pk=self.location.pk).exists())

    def test_staff_can_delete_location(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse("delete_location", args=[self.location.pk]))

        self.assertRedirects(response, reverse("show_location"))
        self.assertFalse(Location.objects.filter(pk=self.location.pk).exists())

    def test_delete_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        client.get(reverse("create_location"))
        token = client.cookies["csrftoken"].value

        rejected = client.post(reverse("delete_location", args=[self.location.pk]))
        self.assertEqual(rejected.status_code, 403)
        self.assertTrue(Location.objects.filter(pk=self.location.pk).exists())

        accepted = client.post(
            reverse("delete_location", args=[self.location.pk]),
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertRedirects(accepted, reverse("show_location"))
        self.assertFalse(Location.objects.filter(pk=self.location.pk).exists())

    def test_unsupported_methods_are_rejected_for_staff(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.put(reverse("create_location")).status_code, 405)
        self.assertEqual(
            self.client.put(reverse("delete_location", args=[self.location.pk])).status_code,
            405,
        )

    def test_protected_location_keeps_data_and_shows_error(self):
        event = Event.objects.create(
            title="Agenda Lokasi",
            start_at=timezone.now() + timedelta(days=1),
            location=self.location,
            is_published=True,
        )
        self.client.force_login(self.staff)

        response = self.client.post(reverse("delete_location", args=[self.location.pk]))

        self.assertRedirects(response, reverse("show_location"))
        self.assertTrue(Location.objects.filter(pk=self.location.pk).exists())
        self.assertTrue(Event.objects.filter(pk=event.pk).exists())
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("tidak bisa dihapus" in message for message in messages))

    def test_public_location_pages_remain_accessible(self):
        self.assertEqual(self.client.get(reverse("show_location")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("location_detail", args=[self.location.pk])).status_code,
            200,
        )
