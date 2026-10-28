import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from education.models import Article, Distribution
from Location.models import Location
from Schedule.models import Pemeriksaan

BUSINESS_TIMEZONE = ZoneInfo("Asia/Jakarta")


def make_location(name, category, is_active=True):
    return Location.objects.create(
        name=name,
        description="Lokasi uji",
        address="Jl. Uji No. 1",
        contact_person="08123456789",
        open_hours="08.00-16.00",
        province="DKI Jakarta",
        city="Jakarta",
        latitude=Decimal("-6.200000"),
        longitude=Decimal("106.800000"),
        category=category,
        is_active=is_active,
    )


class LandingPageStatsTests(TestCase):
    def setUp(self):
        self.partner = make_location("Panti Asuhan Uji", Location.Category.panti_asuhan)
        self.bank = make_location("Bank Sampah Uji", Location.Category.bank_sampah)
        make_location("Komunitas Nonaktif", Location.Category.komunitas, is_active=False)

        today = timezone.localdate(timezone=BUSINESS_TIMEZONE)
        Distribution.objects.create(
            item_name="Pakaian layak pakai",
            quantity=4,
            destination=self.partner,
            status=Distribution.Status.delivered,
            distributed_at=today,
        )
        # Tujuan bank sampah, belum jatuh tempo, dan masih direncanakan tidak dihitung.
        Distribution.objects.create(
            item_name="Kardus",
            quantity=7,
            destination=self.bank,
            status=Distribution.Status.delivered,
            distributed_at=today,
        )
        Distribution.objects.create(
            item_name="Buku",
            quantity=9,
            destination=self.partner,
            status=Distribution.Status.delivered,
            distributed_at=today + datetime.timedelta(days=1),
        )
        Distribution.objects.create(
            item_name="Mainan",
            quantity=5,
            destination=self.partner,
            status=Distribution.Status.planned,
        )

        warga = User.objects.create_user(username="warga", password="pass12345")
        staf = User.objects.create_user(
            username="staf", password="pass12345", is_staff=True
        )
        for user in (warga, warga, staf):
            Pemeriksaan.objects.create(
                pengguna=user,
                nama_barang="Botol plastik",
                jenis_barang="Plastik",
                kondisi_barang="Masih bersih",
                kategori_penanganan="recycle",
            )

        Article.objects.create(
            title="Panduan memilah",
            summary="Ringkasan",
            body="Isi panduan",
            is_published=True,
            published_at=timezone.now() - datetime.timedelta(days=1),
        )
        Article.objects.create(
            title="Draf",
            summary="Ringkasan",
            body="Isi draf",
            is_published=False,
        )
        Article.objects.create(
            title="Terbit nanti",
            summary="Ringkasan",
            body="Isi",
            is_published=True,
            published_at=timezone.now() + datetime.timedelta(days=1),
        )

    def test_stats_come_from_real_querysets(self):
        response = self.client.get(reverse("landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertEqual(response.context["stats"], {
            "distributed_items": 4,
            "active_locations": 2,
            "participants": 1,
            "published_articles": 1,
        })

    def test_homepage_has_one_h1_and_links_to_existing_routes(self):
        response = self.client.get(reverse("landing_page"))

        self.assertContains(response, "<h1", count=1)
        self.assertNotContains(response, "Platform sirkular warga")
        self.assertContains(response, "home-stat__number", count=4)
        self.assertNotContains(response, 'href="#"')
        for route in (
            "show_schedule",
            "show_location",
            "distribution_list",
            "education_home",
        ):
            self.assertContains(response, reverse(route))


class LandingPageEmptyStateTests(TestCase):
    def test_renders_zero_instead_of_placeholder_numbers(self):
        response = self.client.get(reverse("landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"], {
            "distributed_items": 0,
            "active_locations": 0,
            "participants": 0,
            "published_articles": 0,
        })


class HeaderNavigationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staf-nav", password="pass12345", is_staff=True
        )

    def assert_header(self, response, section):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_nav"], section)
        self.assertContains(response, '<details class="nav-mobile">', count=1)
        self.assertContains(response, 'class="nav-mobile__toggle"', count=1)
        self.assertContains(response, "Menu navigasi", count=1)
        self.assertContains(response, "nav-mobile__icon--open", count=1)
        self.assertContains(response, "nav-mobile__icon--close", count=1)
        self.assertContains(response, 'class="nav-mobile__panel"', count=1)
        self.assertNotContains(response, 'id="mobile-nav"')
        self.assertNotContains(response, 'id="mobile-nav-toggle"')
        self.assertNotContains(response, "Pengajuan")
        self.assertEqual(response.content.count(b'aria-current="page"'), 2)
        for name in (
            "landing_page",
            "show_location",
            "show_schedule",
            "education_home",
        ):
            self.assertContains(response, f'href="{reverse(name)}"')

    def test_public_pages_have_one_mobile_nav_and_active_state(self):
        pages = (
            ("landing_page", "beranda"),
            ("show_location", "peta"),
            ("show_schedule", "jadwal"),
            ("education_home", "edukasi"),
        )
        for name, section in pages:
            with self.subTest(page=name):
                self.assert_header(self.client.get(reverse(name)), section)

    def test_schedule_list_keeps_jadwal_active(self):
        self.assert_header(self.client.get(reverse("schedule_list")), "jadwal")

    def test_education_staff_page_keeps_edukasi_active(self):
        self.client.force_login(self.staff)
        self.assert_header(self.client.get(reverse("education_manage")), "edukasi")
