from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from education.forms import ArticleForm, DistributionForm, EventForm
from education.models import ARTICLE_COVERS, Article, Distribution, Event
from Location.models import Location


def make_location(**overrides):
    data = {
        "name": "Panti Harapan",
        "description": "Panti asuhan anak",
        "address": "Jl. Melati No. 1",
        "contact_person": "081200000000",
        "open_hours": "08.00-16.00",
        "province": "DKI Jakarta",
        "city": "Jakarta Selatan",
        "latitude": -6.2615,
        "longitude": 106.8106,
        "category": Location.Category.panti_asuhan,
    }
    data.update(overrides)
    return Location.objects.create(**data)


def make_article(**overrides):
    data = {
        "title": "Cara memilah plastik rumah tangga",
        "summary": "Panduan singkat memilah plastik.",
        "body": "Plastik perlu dipilah sebelum disetorkan.",
        "category": Article.Category.panduan,
        "is_published": True,
        "published_at": timezone.now() - timedelta(days=1),
    }
    data.update(overrides)
    return Article.objects.create(**data)


def make_event(location, **overrides):
    data = {
        "title": "Workshop perbaikan elektronik",
        "start_at": timezone.now() + timedelta(days=3),
        "location": location,
        "is_published": True,
    }
    data.update(overrides)
    return Event.objects.create(**data)


def make_distribution(destination, **overrides):
    data = {
        "item_name": "Tote bag katun",
        "quantity": 5,
        "destination": destination,
        "status": Distribution.Status.delivered,
        "distributed_at": timezone.localdate(),
    }
    data.update(overrides)
    return Distribution.objects.create(**data)


class ArticleModelTests(TestCase):
    def test_slug_is_generated_from_title(self):
        article = make_article(title="Belajar Reduce dari Dapur")

        self.assertEqual(article.slug, "belajar-reduce-dari-dapur")

    def test_slug_is_unique_for_same_title(self):
        first = make_article(title="Judul Sama")
        second = make_article(title="Judul Sama")

        self.assertEqual(first.slug, "judul-sama")
        self.assertEqual(second.slug, "judul-sama-2")

    def test_slug_stays_stable_when_title_changes(self):
        article = make_article(title="Judul Awal")
        article.title = "Judul Baru"
        article.save()
        article.refresh_from_db()

        self.assertEqual(article.slug, "judul-awal")

    def test_slug_falls_back_when_title_has_no_slug_characters(self):
        article = make_article(title="!!!")

        self.assertEqual(article.slug, "artikel")

    def test_default_article_is_draft(self):
        article = Article.objects.create(
            title="Artikel Draf",
            summary="Ringkasan",
            body="Isi",
        )

        self.assertFalse(article.is_published)

    def test_published_queryset_excludes_drafts_and_future_articles(self):
        published = make_article(title="Artikel Terbit")
        make_article(title="Artikel Draf", is_published=False)
        make_article(title="Artikel Terjadwal", published_at=timezone.now() + timedelta(days=1))

        self.assertEqual(list(Article.objects.published()), [published])


class PublicAssetTests(TestCase):
    def test_editorial_css_and_js_are_served(self):
        response = self.client.get(reverse("education_home"))

        self.assertContains(response, "/static/css/education.css")
        self.assertContains(response, "/static/js/education.js")
        for path in [
            "css/theme.css",
            "css/education.css",
            "js/education.js",
        ]:
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path))


class ArticlePresentationTests(TestCase):
    def test_read_minutes_has_a_minimum_of_one(self):
        article = make_article(body="satu dua")

        self.assertEqual(article.read_minutes, 1)

    def test_read_minutes_counts_words(self):
        article = make_article(body="kata " * 400)

        self.assertEqual(article.read_minutes, 2)

    def test_cover_uses_known_slug_then_category_fallback(self):
        featured = make_article(title="Mulai Reduce dari Belanja Mingguan Keluarga")
        fallback = make_article(title="Artikel Reuse Baru", category=Article.Category.reuse)

        self.assertEqual(
            featured.cover["src"], "images/education/articles/belanja-pasar-reusable.jpg"
        )
        self.assertEqual(
            fallback.cover["src"], "images/education/articles/barang-layak-pakai.jpg"
        )

    def test_all_configured_cover_assets_exist(self):
        for cover in ARTICLE_COVERS.values():
            with self.subTest(src=cover["src"]):
                self.assertIsNotNone(finders.find(cover["src"]))


class EventModelTests(TestCase):
    def setUp(self):
        self.location = make_location()

    def test_valid_event_passes_validation(self):
        event = Event(
            title="Kerja bakti",
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1, hours=2),
            location=self.location,
        )

        event.full_clean()

    def test_end_before_start_is_rejected(self):
        event = Event(
            title="Agenda salah",
            start_at=timezone.now() + timedelta(days=1, hours=2),
            end_at=timezone.now() + timedelta(days=1),
            location=self.location,
        )

        with self.assertRaises(ValidationError) as context:
            event.full_clean()

        self.assertIn("end_at", context.exception.message_dict)

    def test_end_equal_to_start_is_allowed(self):
        start = timezone.now() + timedelta(days=1)
        event = Event(title="Agenda singkat", start_at=start, end_at=start, location=self.location)

        event.full_clean()

    def test_database_rejects_end_before_start(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_event(
                    self.location,
                    start_at=timezone.now() + timedelta(days=2),
                    end_at=timezone.now() + timedelta(days=1),
                )

    def test_location_with_event_cannot_be_deleted(self):
        make_event(self.location)

        with self.assertRaises(ProtectedError):
            self.location.delete()


class DistributionModelTests(TestCase):
    def setUp(self):
        self.panti = make_location(name="Panti Tujuan")
        self.bank = make_location(name="Bank Sampah", category=Location.Category.bank_sampah)

    def test_valid_delivered_distribution_passes_validation(self):
        distribution = Distribution(
            item_name="Botol stainless",
            quantity=3,
            destination=self.panti,
            status=Distribution.Status.delivered,
            distributed_at=timezone.localdate(),
        )

        distribution.full_clean()

    def test_quantity_must_be_at_least_one(self):
        distribution = Distribution(item_name="Tote bag", quantity=0, destination=self.panti)

        with self.assertRaises(ValidationError) as context:
            distribution.full_clean()

        self.assertIn("quantity", context.exception.message_dict)

    def test_destination_must_be_panti_or_komunitas(self):
        distribution = Distribution(
            item_name="Tote bag",
            quantity=1,
            destination=self.bank,
            status=Distribution.Status.planned,
        )

        with self.assertRaises(ValidationError) as context:
            distribution.full_clean()

        self.assertIn("destination", context.exception.message_dict)

    def test_delivered_requires_date(self):
        distribution = Distribution(
            item_name="Tote bag",
            quantity=1,
            destination=self.panti,
            status=Distribution.Status.delivered,
        )

        with self.assertRaises(ValidationError) as context:
            distribution.full_clean()

        self.assertIn("distributed_at", context.exception.message_dict)

    def test_planned_distribution_may_omit_date(self):
        distribution = Distribution(
            item_name="Tote bag",
            quantity=1,
            destination=self.panti,
            status=Distribution.Status.planned,
        )

        distribution.full_clean()

    def test_database_rejects_zero_quantity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_distribution(self.panti, quantity=0)



class FormTests(TestCase):
    def setUp(self):
        self.location = make_location()

    def test_article_form_saves_published_article(self):
        form = ArticleForm(data={
            "title": "Artikel dari Form",
            "summary": "Ringkasan",
            "body": "Isi artikel",
            "category": Article.Category.panduan,
            "is_published": "on",
            "published_at": "2026-10-26T10:00",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().slug, "artikel-dari-form")

    def test_article_form_rejects_missing_title(self):
        form = ArticleForm(data={
            "title": "",
            "summary": "Ringkasan",
            "body": "Isi",
            "category": Article.Category.panduan,
            "published_at": "2026-10-26T10:00",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_event_form_rejects_end_before_start(self):
        form = EventForm(data={
            "title": "Agenda salah",
            "description": "",
            "start_at": "2026-11-01T11:00",
            "end_at": "2026-11-01T09:00",
            "location": self.location.pk,
            "is_published": "on",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("end_at", form.errors)

    def test_distribution_form_rejects_bank_destination(self):
        bank = make_location(name="Bank Sampah", category=Location.Category.bank_sampah)
        form = DistributionForm(data={
            "item_name": "Tote bag",
            "description": "",
            "quantity": 1,
            "destination": bank.pk,
            "status": Distribution.Status.planned,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("destination", form.errors)

    def test_event_form_keeps_inactive_location_on_edit(self):
        inactive = make_location(name="Nonaktif", is_active=False)
        create = EventForm().fields["location"].queryset
        edit = EventForm(instance=make_event(inactive)).fields["location"].queryset
        self.assertIn(self.location, create)
        self.assertNotIn(inactive, create)
        self.assertIn(inactive, edit)

    def test_distribution_form_keeps_inactive_destination_on_edit(self):
        inactive = make_location(name="Nonaktif", is_active=False)
        bank = make_location(name="Bank", category=Location.Category.bank_sampah)
        create = DistributionForm().fields["destination"].queryset
        edit = DistributionForm(instance=make_distribution(inactive)).fields["destination"].queryset
        self.assertIn(self.location, create)
        self.assertNotIn(inactive, create)
        self.assertNotIn(bank, create)
        self.assertIn(inactive, edit)


class ManagementAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.user = User.objects.create_user("user", password="x")

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("education_manage"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_non_staff_is_forbidden(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("education_manage")).status_code, 403)

    def test_staff_can_open_management_and_forms(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse("education_manage")).status_code, 200)
        for name in ["article_create", "event_create", "distribution_create"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)


class CrudTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(self.staff)
        self.location = make_location()

    def test_article_create_update_and_post_only_delete(self):
        self.client.post(reverse("article_create"), {
            "title": "Artikel Baru",
            "summary": "Ringkasan",
            "body": "Isi",
            "category": Article.Category.panduan,
            "is_published": "on",
            "published_at": "2026-10-26T10:00",
        })
        article = Article.objects.get(title="Artikel Baru")

        self.client.post(reverse("article_update", args=[article.pk]), {
            "title": "Artikel Diubah",
            "summary": "Ringkasan",
            "body": "Isi",
            "category": Article.Category.panduan,
            "is_published": "on",
            "published_at": "2026-10-26T10:00",
        })
        article.refresh_from_db()
        self.assertEqual(article.title, "Artikel Diubah")

        self.assertEqual(self.client.get(reverse("article_delete", args=[article.pk])).status_code, 200)
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())
        self.client.post(reverse("article_delete", args=[article.pk]))
        self.assertFalse(Article.objects.filter(pk=article.pk).exists())

    def test_event_and_distribution_create(self):
        self.client.post(reverse("event_create"), {
            "title": "Agenda Baru", "description": "",
            "start_at": "2026-11-01T09:00", "end_at": "2026-11-01T11:00",
            "location": self.location.pk, "is_published": "on",
        })
        self.client.post(reverse("distribution_create"), {
            "item_name": "Tote bag", "description": "", "quantity": 2,
            "destination": self.location.pk, "status": Distribution.Status.planned,
        })

        self.assertTrue(Event.objects.filter(title="Agenda Baru").exists())
        self.assertTrue(Distribution.objects.filter(item_name="Tote bag").exists())

    def test_invalid_form_does_not_create_article(self):
        self.client.post(reverse("article_create"), {
            "title": "", "summary": "Ringkasan", "body": "Isi",
            "category": Article.Category.panduan, "published_at": "2026-10-26T10:00",
        })

        self.assertFalse(Article.objects.exists())

    def test_csrf_required_for_delete(self):
        article = make_article()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)

        response = client.post(reverse("article_delete", args=[article.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())


class LocationRegressionTests(TestCase):
    def test_location_used_by_event_cannot_be_deleted(self):
        staff = User.objects.create_user("location-staff", password="x", is_staff=True)
        self.client.force_login(staff)
        location = make_location()
        event = make_event(location)
        distribution = make_distribution(location)

        response = self.client.post(reverse("delete_location", args=[location.pk]))

        self.assertRedirects(response, reverse("show_location"))
        self.assertTrue(Location.objects.filter(pk=location.pk).exists())
        self.assertTrue(Event.objects.filter(pk=event.pk).exists())
        self.assertTrue(Distribution.objects.filter(pk=distribution.pk).exists())


class UrlTests(TestCase):
    def test_management_url_names_resolve(self):
        for name in [
            "education_manage", "article_create", "article_update", "article_delete",
            "event_create", "event_update", "event_delete",
            "distribution_create", "distribution_update", "distribution_delete",
        ]:
            with self.subTest(name=name):
                self.assertTrue(reverse(name, args=[1]) if name.endswith(("update", "delete")) else reverse(name))


class PublicPagesTests(TestCase):
    def setUp(self):
        self.location = make_location()

    def test_home_shows_published_content_and_links(self):
        article = make_article(title="Artikel Publik")
        event = make_event(self.location, title="Agenda Publik")

        response = self.client.get(reverse("education_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, article.title)
        self.assertContains(response, event.title)
        self.assertContains(response, reverse("article_detail", args=[article.slug]))
        self.assertContains(response, reverse("event_detail", args=[event.pk]))

    def test_home_lists_only_active_reuse_partners(self):
        panti = make_location(name="Panti Tampil")
        komunitas = make_location(
            name="Komunitas Tampil", category=Location.Category.komunitas
        )
        make_location(name="Bank Tersembunyi", category=Location.Category.bank_sampah)
        make_location(name="Panti Nonaktif", is_active=False)

        response = self.client.get(reverse("education_home"))

        self.assertContains(response, panti.name)
        self.assertContains(response, komunitas.name)
        self.assertNotContains(response, "Bank Tersembunyi")
        self.assertNotContains(response, "Panti Nonaktif")

    def test_home_handles_empty_optional_sections(self):
        self.location.is_active = False
        self.location.save(update_fields=["is_active"])

        response = self.client.get(reverse("education_home"))

        self.assertContains(response, "Belum ada panduan yang terbit")
        self.assertContains(response, "Belum ada mitra penyaluran aktif")
        self.assertContains(response, "Belum ada agenda mendatang")

    def test_home_and_lists_render_empty_states(self):
        for name in ["education_home", "article_list", "event_list"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
        self.assertContains(self.client.get(reverse("article_list")), "Belum ada artikel")
        self.assertContains(self.client.get(reverse("event_list")), "Belum ada agenda")

    def test_article_list_hides_draft_and_future_articles(self):
        published = make_article(title="Artikel Terbit")
        make_article(title="Artikel Draf", is_published=False)
        make_article(title="Artikel Terjadwal", published_at=timezone.now() + timedelta(days=1))

        response = self.client.get(reverse("article_list"))

        self.assertContains(response, published.title)
        self.assertNotContains(response, "Artikel Draf")
        self.assertNotContains(response, "Artikel Terjadwal")

    def test_article_detail_only_serves_published_articles(self):
        article = make_article(title="Artikel Detail")
        draft = make_article(title="Artikel Draf", is_published=False)
        future = make_article(title="Artikel Terjadwal", published_at=timezone.now() + timedelta(days=1))

        self.assertEqual(
            self.client.get(reverse("article_detail", args=[article.slug])).status_code, 200
        )
        self.assertContains(
            self.client.get(reverse("article_detail", args=[article.slug])), article.body
        )
        self.assertEqual(
            self.client.get(reverse("article_detail", args=[draft.slug])).status_code, 404
        )
        self.assertEqual(
            self.client.get(reverse("article_detail", args=[future.slug])).status_code, 404
        )
        self.assertEqual(self.client.get(reverse("article_detail", args=["tidak-ada"])).status_code, 404)

    def test_event_list_is_upcoming_and_handles_inactive_location(self):
        later = make_event(
            self.location, title="Agenda Lebih Lambat", start_at=timezone.now() + timedelta(days=5)
        )
        earlier = make_event(
            self.location, title="Agenda Lebih Awal", start_at=timezone.now() + timedelta(days=2)
        )
        make_event(self.location, title="Agenda Lampau", start_at=timezone.now() - timedelta(days=2))
        inactive = make_location(name="Lokasi Nonaktif", is_active=False)
        inactive_event = make_event(
            inactive, title="Agenda Lokasi Nonaktif", start_at=timezone.now() + timedelta(days=4)
        )

        response = self.client.get(reverse("event_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Agenda Lampau")
        self.assertContains(response, "Agenda Lokasi Nonaktif")
        self.assertContains(response, "Lokasi Nonaktif")
        self.assertEqual(list(response.context["events"]), [earlier, inactive_event, later])

    def test_event_detail_only_serves_published_events(self):
        event = make_event(self.location, title="Agenda Detail")
        draft = make_event(self.location, title="Agenda Draf", is_published=False)

        response = self.client.get(reverse("event_detail", args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)
        self.assertContains(response, self.location.name)
        self.assertEqual(self.client.get(reverse("event_detail", args=[draft.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("event_detail", args=[999999])).status_code, 404)

    def test_event_detail_handles_inactive_location(self):
        inactive = make_location(name="Lokasi Nonaktif", is_active=False)
        event = make_event(inactive, title="Agenda Lokasi Nonaktif")

        response = self.client.get(reverse("event_detail", args=[event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lokasi Nonaktif")

    def test_public_urls_resolve_without_login(self):
        self.assertEqual(self.client.get(reverse("education_home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("article_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("event_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("education_manage")).status_code, 302)


class PublicDistributionTests(TestCase):
    def setUp(self):
        self.panti = make_location(
            name="Panti Publik",
            description="Deskripsi Lokasi Internal",
            address="Jl. Rahasia 99",
            contact_person="081299999999",
            city="Kota Rahasia",
            province="Provinsi Rahasia",
            open_hours="Jam Rahasia",
            longitude=106.999999,
        )
        self.komunitas = make_location(
            name="Komunitas Publik",
            category=Location.Category.komunitas,
        )
        self.bank = make_location(name="Bank Rahasia", category=Location.Category.bank_sampah)

    def test_list_shows_only_completed_relevant_distributions(self):
        selimut = make_distribution(
            self.panti,
            item_name="Selimut",
            quantity=5,
            distributed_at=timezone.localdate() - timedelta(days=2),
        )
        buku = make_distribution(
            self.komunitas,
            item_name="Buku",
            quantity=3,
            distributed_at=timezone.localdate() - timedelta(days=1),
        )
        make_distribution(self.panti, item_name="Rencana", status=Distribution.Status.planned)
        make_distribution(self.panti, item_name="Batal", status=Distribution.Status.cancelled)
        make_distribution(self.bank, item_name="Bank", quantity=100)
        make_distribution(
            self.panti,
            item_name="Masa Depan",
            distributed_at=timezone.localdate() + timedelta(days=1),
        )

        response = self.client.get(reverse("distribution_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, selimut.item_name)
        self.assertContains(response, buku.item_name)
        self.assertNotContains(response, "Rencana")
        self.assertNotContains(response, "Batal")
        self.assertNotContains(response, "Bank")
        self.assertNotContains(response, "Masa Depan")
        self.assertEqual(response.context["stats"]["total_records"], 2)
        self.assertEqual(response.context["stats"]["total_quantity"], 8)
        self.assertEqual(response.context["stats"]["total_destinations"], 2)

    def test_public_list_does_not_render_private_location_fields(self):
        distribution = make_distribution(
            self.panti,
            item_name="Barang Aman",
            description="Catatan internal jangan tampil",
            quantity=4,
            distributed_at=timezone.localdate(),
        )

        response = self.client.get(reverse("distribution_list"))

        self.assertContains(response, distribution.item_name)
        self.assertContains(response, self.panti.name)
        self.assertContains(response, self.panti.get_category_display())
        for private_value in [
            "Catatan internal jangan tampil",
            "Deskripsi Lokasi Internal",
            "Jl. Rahasia 99",
            "081299999999",
            "Kota Rahasia",
            "Provinsi Rahasia",
            "Jam Rahasia",
            str(self.panti.latitude),
            str(self.panti.longitude),
        ]:
            self.assertNotContains(response, private_value)

    def test_inactive_destination_is_rendered_without_error(self):
        inactive = make_location(name="Panti Nonaktif", is_active=False)
        distribution = make_distribution(
            inactive,
            item_name="Barang Historis",
            distributed_at=timezone.localdate(),
        )

        response = self.client.get(reverse("distribution_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, distribution.item_name)
        self.assertContains(response, "Panti Nonaktif")
        self.assertEqual(response.context["stats"]["total_records"], 1)

    @patch("django.utils.timezone.now")
    def test_public_date_uses_jakarta_business_day(self, mock_now):
        mock_now.return_value = datetime(2026, 10, 26, 18, 30, tzinfo=dt_timezone.utc)
        distribution = make_distribution(
            self.panti,
            item_name="Hari Ini WIB",
            quantity=4,
            distributed_at=date(2026, 10, 27),
        )

        response = self.client.get(reverse("distribution_list"))

        self.assertContains(response, distribution.item_name)
        self.assertEqual(response.context["stats"]["total_records"], 1)
        self.assertEqual(response.context["stats"]["total_quantity"], 4)
        self.assertEqual(response.context["stats"]["total_destinations"], 1)

    def test_empty_state_and_zero_statistics(self):
        response = self.client.get(reverse("distribution_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belum ada catatan penyaluran")
        self.assertEqual(response.context["stats"]["total_records"], 0)
        self.assertEqual(response.context["stats"]["total_destinations"], 0)

    def test_home_links_to_public_distribution_page(self):
        response = self.client.get(reverse("education_home"))

        self.assertContains(response, reverse("distribution_list"))

    def test_public_route_does_not_open_staff_management(self):
        self.assertEqual(self.client.get(reverse("distribution_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("education_manage")).status_code, 302)

    def test_statistics_count_distinct_destinations(self):
        make_distribution(self.panti, item_name="Barang A", quantity=2)
        make_distribution(self.panti, item_name="Barang B", quantity=3)

        response = self.client.get(reverse("distribution_list"))

        self.assertEqual(response.context["stats"]["total_records"], 2)
        self.assertEqual(response.context["stats"]["total_quantity"], 5)
        self.assertEqual(response.context["stats"]["total_destinations"], 1)

    def test_list_orders_by_delivery_date_and_excludes_missing_date(self):
        older = make_distribution(
            self.panti, item_name="Lebih Lama",
            distributed_at=timezone.localdate() - timedelta(days=2),
        )
        newer = make_distribution(
            self.panti, item_name="Lebih Baru",
            distributed_at=timezone.localdate() - timedelta(days=1),
        )
        make_distribution(self.panti, item_name="Tanpa Tanggal", distributed_at=None)

        response = self.client.get(reverse("distribution_list"))

        self.assertEqual(list(response.context["distributions"]), [newer, older])
