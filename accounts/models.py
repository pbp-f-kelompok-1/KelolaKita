from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Pengguna"
        MANAGER = "manager", "Pengelola KelolaKita"
        PARTNER = "partner", "Mitra"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Nomor telepon",
    )
    address = models.TextField(
        blank=True,
        verbose_name="Alamat utama",
    )
    avatar_url = models.URLField(
        blank=True,
        verbose_name="URL foto profil",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    points = models.PositiveIntegerField(
        default=0,
        verbose_name="Poin dampak",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil {self.user.username}"