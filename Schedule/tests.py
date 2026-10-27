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
