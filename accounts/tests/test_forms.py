from django.contrib.auth.models import User
from django.test import TestCase

from accounts.forms import ProfileUpdateForm, RegisterForm, UserUpdateForm


PASSWORD = "SandiKuat!2026"


class RegisterFormTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "username": "pendaftar_form",
            "first_name": "Nama",
            "last_name": "Pendaftar",
            "email": " Pendaftar@Example.com ",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_email_is_normalized_before_saving(self):
        form = RegisterForm(self.registration_data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, "pendaftar@example.com")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="pemilik_email", email="existing@example.com", password=PASSWORD
        )
        form = RegisterForm(self.registration_data(email="EXISTING@EXAMPLE.COM"))

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_confirmation_must_match(self):
        form = RegisterForm(self.registration_data(password2="SandiLain!2026"))

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class UserUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="pemilik_update", email="self@example.com", password=PASSWORD
        )
        User.objects.create_user(
            username="pengguna_lain", email="taken@example.com", password=PASSWORD
        )

    def update_data(self, **overrides):
        data = {
            "first_name": "Nama",
            "last_name": "Baru",
            "email": "self@example.com",
        }
        data.update(overrides)
        return data

    def test_own_email_is_allowed_and_normalized(self):
        form = UserUpdateForm(
            self.update_data(email=" SELF@EXAMPLE.COM "), instance=self.user
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "self@example.com")

    def test_another_users_email_is_rejected_case_insensitively(self):
        form = UserUpdateForm(
            self.update_data(email=" TAKEN@EXAMPLE.COM "), instance=self.user
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_names_and_email_are_required_and_username_is_not_editable(self):
        form = UserUpdateForm(
            self.update_data(first_name="", last_name="", email="", username="changed"),
            instance=self.user,
        )

        self.assertEqual(set(form.fields), {"first_name", "last_name", "email"})
        self.assertFalse(form.is_valid())
        self.assertTrue({"first_name", "last_name", "email"}.issubset(form.errors))


class ProfileUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="pemilik_profil", password=PASSWORD)

    def test_only_contact_fields_are_editable(self):
        form = ProfileUpdateForm(instance=self.user.profile)

        self.assertEqual(
            set(form.fields), {"phone_number", "address", "avatar_url"}
        )
        self.assertTrue(
            {"role", "points", "user", "updated_at"}.isdisjoint(form.fields)
        )

    def test_avatar_url_must_be_valid_url(self):
        form = ProfileUpdateForm(
            {"phone_number": "08123456789", "address": "Alamat", "avatar_url": "bukan-url"},
            instance=self.user.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("avatar_url", form.errors)
