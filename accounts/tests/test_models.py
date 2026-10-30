from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Profile


class ProfileModelTests(TestCase):
    def test_creating_user_creates_one_profile_with_defaults(self):
        user = User.objects.create_user(username="pemilik_model", password="SandiKuat!2026")

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.user, user)
        self.assertEqual(user.profile, profile)
        self.assertTrue(Profile._meta.get_field("user").one_to_one)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(profile.role, Profile.Role.USER)
        self.assertEqual(profile.points, 0)

    def test_saving_user_again_does_not_duplicate_profile(self):
        user = User.objects.create_user(username="pemilik_tetap", password="SandiKuat!2026")
        original_profile = user.profile

        user.first_name = "Nama"
        user.save()

        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(user.profile.pk, original_profile.pk)

    def test_string_representation_contains_username(self):
        user = User.objects.create_user(username="pemilik_string", password="SandiKuat!2026")

        self.assertEqual(str(user.profile), "Profil pemilik_string")
