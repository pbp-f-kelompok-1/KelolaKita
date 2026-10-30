from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile


PASSWORD = "SandiKuat!2026"


class RegisterViewTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:register")
        self.landing_url = reverse("landing_page")

    def registration_data(self, **overrides):
        data = {
            "username": "pendaftar_baru",
            "first_name": "Nama",
            "last_name": "Pengguna",
            "email": " Pendaftar@Example.com ",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_get_renders_register_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_valid_registration_saves_user_profile_and_logs_in(self):
        response = self.client.post(self.url, self.registration_data())

        self.assertRedirects(response, self.landing_url, fetch_redirect_response=False)
        user = User.objects.get(username="pendaftar_baru")
        self.assertEqual(user.first_name, "Nama")
        self.assertEqual(user.last_name, "Pengguna")
        self.assertEqual(user.email, "pendaftar@example.com")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(
            any("Akun berhasil dibuat" in str(message) for message in get_messages(response.wsgi_request))
        )

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="pemilik_email", email="existing@example.com", password=PASSWORD
        )

        response = self.client.post(
            self.url, self.registration_data(email="EXISTING@EXAMPLE.COM")
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "email", "Email ini sudah digunakan oleh akun lain.")
        self.assertFalse(User.objects.filter(username="pendaftar_baru").exists())

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(
            self.url, self.registration_data(password2="SandiBerbeda!2026")
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="pendaftar_baru").exists())

    def test_authenticated_user_is_redirected_from_register(self):
        user = User.objects.create_user(username="sudah_masuk", password=PASSWORD)
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertRedirects(response, self.landing_url, fetch_redirect_response=False)


class LoginViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="pengguna_login", password=PASSWORD, first_name="Nama"
        )

    def setUp(self):
        self.url = reverse("accounts:login")
        self.landing_url = reverse("landing_page")

    def credentials(self, **overrides):
        data = {"username": self.user.username, "password": PASSWORD}
        data.update(overrides)
        return data

    def test_get_renders_login_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_valid_credentials_log_in_and_redirect_to_landing(self):
        response = self.client.post(self.url, self.credentials())

        self.assertRedirects(response, self.landing_url, fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        self.assertTrue(
            any("Selamat datang kembali" in str(message) for message in get_messages(response.wsgi_request))
        )

    def test_wrong_password_does_not_authenticate(self):
        response = self.client.post(self.url, self.credentials(password="SandiSalah!2026"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unchecked_remember_me_expires_at_browser_close(self):
        self.client.post(self.url, self.credentials())

        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_checked_remember_me_uses_fourteen_day_expiry(self):
        self.client.post(self.url, self.credentials(remember_me="on"))

        session = self.client.session
        self.assertFalse(session.get_expire_at_browser_close())
        self.assertAlmostEqual(session.get_expiry_age(), 14 * 24 * 60 * 60, delta=10)

    def test_safe_internal_next_url_is_used(self):
        next_url = reverse("accounts:profile")

        response = self.client.post(self.url, self.credentials(next=next_url))

        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_external_next_url_falls_back_to_landing(self):
        response = self.client.post(
            self.url, self.credentials(next="https://evil.example/path")
        )

        self.assertRedirects(response, self.landing_url, fetch_redirect_response=False)

    def test_authenticated_user_is_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertRedirects(response, self.landing_url, fetch_redirect_response=False)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pengguna_keluar", password=PASSWORD)
        self.client.force_login(self.user)
        self.url = reverse("accounts:logout")

    def test_get_is_rejected_and_does_not_log_out(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_post_logs_out_clears_auth_session_and_redirects(self):
        response = self.client.post(self.url)

        self.assertRedirects(
            response, reverse("landing_page"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(
            any("berhasil keluar" in str(message) for message in get_messages(response.wsgi_request))
        )
