import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from education.models import Article, Distribution, Event
from Location.models import Location


MANIFEST = Path(settings.BASE_DIR) / "education/management/commands/pws_public_content.json"


class PwsImportTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(shutil.rmtree, self.media_root, True)
        self.addCleanup(self.media_override.disable)

    def import_content(self, *args, manifest=MANIFEST):
        output = StringIO()
        call_command(
            "import_pws_public_content",
            *args,
            manifest=manifest,
            stdout=output,
        )
        return output.getvalue()

    def test_dry_run_does_not_write(self):
        output = self.import_content("--dry-run")

        self.assertIn("DRY-RUN", output)
        self.assertIn("articles: discovered=3", output)
        self.assertEqual(Article.objects.count(), 0)
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(Distribution.objects.count(), 0)

    def test_import_is_idempotent_and_keeps_relations(self):
        first = self.import_content()
        second = self.import_content()

        self.assertIn("articles: discovered=3 created=3", first)
        self.assertIn("articles: discovered=3 created=0 updated=0 unchanged=3", second)
        self.assertIn("images: verified=0 missing=3", second)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Distribution.objects.count(), 1)

        article = Article.objects.get(slug="7-jenis-plastik-dan-ke-mana-harus-membawanya")
        self.assertIn("Ke mana harus membawanya?", article.body)
        self.assertFalse(article.image)

        event = Event.objects.get(title="Aksi Pilah Sampah dan Setor Daur Ulang Bersama")
        self.assertEqual(event.location.name, "Bank Sampah Induk Rumah Harum")
        self.assertEqual(event.description[:20], "Kegiatan edukasi dan")

        distribution = Distribution.objects.get()
        self.assertEqual(distribution.item_name, "Pakaian bekas layak pakai")
        self.assertEqual(distribution.destination.name, "LKSA Muhammadiyah Darul Ilmi (Panti Asuhan Darul Ilmi)")
        self.assertEqual(distribution.quantity, 100)

    def test_existing_alias_is_updated_not_duplicated(self):
        old = Article.objects.create(
            title="Data lama",
            slug="test",
            summary="Ringkasan lama",
            body="Isi lama",
            category=Article.Category.reuse,
            is_published=False,
        )

        self.import_content()

        old.refresh_from_db()
        self.assertEqual(old.slug, "cek-cepat-barang-layak-pakai-atau-perlu-diperbaiki")
        self.assertEqual(old.title, "Cek Cepat: Barang Layak Pakai atau Perlu Diperbaiki")
        self.assertTrue(old.is_published)
        self.assertEqual(Article.objects.count(), 3)

    def test_invalid_manifest_rolls_back_all_writes(self):
        data = json.loads(MANIFEST.read_text())
        data["articles"][1]["category"] = "tidak-ada"
        path = Path(self.media_root) / "invalid-manifest.json"
        path.write_text(json.dumps(data))

        with self.assertRaises(CommandError):
            self.import_content(manifest=path)

        self.assertEqual(Article.objects.count(), 0)
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(Distribution.objects.count(), 0)

    def test_imported_content_renders_on_public_pages(self):
        self.import_content()

        response = self.client.get("/edukasi/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cek Cepat: Barang Layak Pakai atau Perlu Diperbaiki")
        self.assertContains(response, "7 Jenis Plastik dan ke Mana Harus Membawanya")
        self.assertContains(response, "Mulai Reduce dari Belanja Mingguan Keluarga")

        response = self.client.get(
            "/edukasi/artikel/7-jenis-plastik-dan-ke-mana-harus-membawanya/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ke mana harus membawanya?")
        self.assertContains(response, "Ke mana harus membawanya?</p>", html=False)
