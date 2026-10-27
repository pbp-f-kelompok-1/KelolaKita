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
