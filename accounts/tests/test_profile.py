from datetime import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.forms import ProfileUpdateForm, UserUpdateForm
from accounts.models import Profile


PASSWORD = "SandiKuat!2026"
AJAX_HEADERS = {
    "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
    "HTTP_ACCEPT": "application/json",
}


class ProfileViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="pemilik_halaman",
            password=PASSWORD,
            first_name="Nama",
            last_name="Awal",
            email="self@example.com",
        )
        cls.other_user = User.objects.create_user(
            username="pengguna_lain",
            password=PASSWORD,
            first_name="Orang",
            last_name="Lain",
            email="other@example.com",
        )
        profile = cls.user.profile
        profile.phone_number = "081200000000"
        profile.address = "Alamat lama"
        profile.role = Profile.Role.MANAGER
        profile.points = 17
        profile.save()

    def setUp(self):
        self.url = reverse("accounts:profile")
        self.client.force_login(self.user)

    def profile_data(self, **overrides):
        data = {
            "first_name": "Nama",
            "last_name": "Baru",
            "email": " NEW@EXAMPLE.COM ",
            "phone_number": "081299999999",
            "address": "Alamat baru",
            "avatar_url": "https://example.com/avatar.png",
        }
        data.update(overrides)
        return data

    def test_anonymous_user_is_redirected_to_login_with_next(self):
        response = Client().get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_logged_in_user_gets_template_and_both_forms(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertIsInstance(response.context["user_form"], UserUpdateForm)
        self.assertIsInstance(response.context["profile_form"], ProfileUpdateForm)
        self.assertEqual(response.context["profile"].user_id, self.user.pk)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_missing_profile_is_recreated_on_get(self):
        Profile.objects.filter(user=self.user).delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        self.assertEqual(response.context["profile"].user_id, self.user.pk)

    def test_plain_post_updates_allowed_fields_and_redirects(self):
        response = self.client.post(self.url, self.profile_data())

        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.user.refresh_from_db()
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(self.user.first_name, "Nama")
        self.assertEqual(self.user.last_name, "Baru")
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(profile.phone_number, "081299999999")
        self.assertEqual(profile.address, "Alamat baru")
        self.assertEqual(profile.avatar_url, "https://example.com/avatar.png")
        self.assertContains(self.client.get(self.url), "Profil berhasil diperbarui.")

    def test_plain_post_rejects_another_users_email_case_insensitively(self):
        response = self.client.post(
            self.url, self.profile_data(email=" OTHER@EXAMPLE.COM ")
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["user_form"], "email", "Email ini sudah digunakan oleh akun lain."
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "self@example.com")

    def test_invalid_profile_form_does_not_partially_save_user(self):
        response = self.client.post(
            self.url, self.profile_data(avatar_url="bukan-url")
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("avatar_url", response.context["profile_form"].errors)
        self.user.refresh_from_db()
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(self.user.last_name, "Awal")
        self.assertEqual(self.user.email, "self@example.com")
        self.assertEqual(profile.address, "Alamat lama")

    def test_invalid_user_form_does_not_partially_save_profile(self):
        response = self.client.post(
            self.url, self.profile_data(email="other@example.com")
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["user_form"].errors)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.phone_number, "081200000000")
        self.assertEqual(profile.address, "Alamat lama")

    def test_extra_role_points_and_username_fields_are_ignored(self):
        response = self.client.post(
            self.url,
            self.profile_data(
                username="diganti",
                role=Profile.Role.PARTNER,
                points="999",
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(self.user.username, "pemilik_halaman")
        self.assertEqual(profile.role, Profile.Role.MANAGER)
        self.assertEqual(profile.points, 17)

    def test_post_cannot_edit_another_users_profile(self):
        response = self.client.post(
            self.url,
            self.profile_data(
                user=str(self.other_user.pk),
                profile=str(self.other_user.profile.pk),
                user_id=str(self.other_user.pk),
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.other_user.refresh_from_db()
        other_profile = Profile.objects.get(user=self.other_user)
        self.assertEqual(self.other_user.first_name, "Orang")
        self.assertEqual(self.other_user.email, "other@example.com")
        self.assertEqual(other_profile.phone_number, "")
        self.assertEqual(Profile.objects.get(user=self.user).address, "Alamat baru")

    def test_ajax_valid_returns_json_and_saves_without_redirect_or_message(self):
        response = self.client.post(
            self.url,
            self.profile_data(role=Profile.Role.PARTNER, points="999"),
            **AJAX_HEADERS,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertNotIn("Location", response)
        payload = response.json()
        self.assertIs(payload["success"], True)
        for key in (
            "message", "full_name", "username", "role", "points", "avatar_url",
            "updated_at", "updated_at_display",
        ):
            self.assertIn(key, payload)
        self.assertEqual(payload["full_name"], "Nama Baru")
        self.assertEqual(payload["username"], self.user.username)
        self.assertEqual(payload["role"], Profile.Role.MANAGER.label)
        self.assertEqual(payload["points"], 17)
        self.assertEqual(payload["avatar_url"], "https://example.com/avatar.png")
        self.assertIsNotNone(datetime.fromisoformat(payload["updated_at"]).tzinfo)
        self.assertTrue(payload["updated_at_display"])
        self.user.refresh_from_db()
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(profile.address, "Alamat baru")
        self.assertEqual(profile.role, Profile.Role.MANAGER)
        self.assertEqual(profile.points, 17)
        self.assertNotContains(self.client.get(self.url), payload["message"])

    def test_ajax_invalid_returns_plain_text_errors_for_both_forms(self):
        response = self.client.post(
            self.url,
            self.profile_data(
                email="OTHER@EXAMPLE.COM", avatar_url="bukan-url"
            ),
            **AJAX_HEADERS,
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertIs(payload["success"], False)
        self.assertIn("Email ini sudah digunakan oleh akun lain.", payload["errors"]["user"]["email"])
        self.assertTrue(payload["errors"]["profile"]["avatar_url"])
        self.assertEqual(payload["non_field_errors"], {"user": [], "profile": []})
        self.assertIsInstance(payload["errors"]["user"]["email"][0], str)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "self@example.com")
        self.assertEqual(Profile.objects.get(user=self.user).address, "Alamat lama")

    def test_anonymous_ajax_request_is_redirected_to_login(self):
        response = Client().post(self.url, self.profile_data(), **AJAX_HEADERS)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_profile_post_without_csrf_is_rejected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(self.url, self.profile_data(), **AJAX_HEADERS)

        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "self@example.com")
