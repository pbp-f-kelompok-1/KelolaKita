from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DaftarPengajuanNavigationTests(TestCase):
    def test_authenticated_user_sees_penanganan_as_current_navigation(self):
        user = User.objects.create_user(username="warga")
        self.client.force_login(user)

        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_nav"], "penanganan")
        self.assertContains(response, reverse("penanganan:daftar_pengajuan"))
        self.assertEqual(response.content.count(b'aria-current="page"'), 2)
