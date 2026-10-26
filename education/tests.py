from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from education.models import Article, Distribution, Event
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
