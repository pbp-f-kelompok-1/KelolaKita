import hashlib
import json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from education.models import Article, Distribution, Event
from Location.models import Location


DEFAULT_MANIFEST = Path(__file__).with_name("pws_public_content.json")
MODELS = ("articles", "locations", "events", "distributions")


class Command(BaseCommand):
    """Mengimpor snapshot konten publik PWS ke model lokal secara idempoten.

    Pencocokan memakai slug/nama kanonis dan alias lokal yang eksplisit. Gambar
    diverifikasi dengan SHA-256 lalu digunakan dari media lokal; file lain tidak
    dipakai sebagai pengganti jika gambar sumber tidak tersedia.
    """

    help = "Mengimpor konten Education publik dari PWS ke basis data lokal."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report planned changes without writing to the database.",
        )
        parser.add_argument(
            "--manifest",
            type=Path,
            default=DEFAULT_MANIFEST,
            help="Path to the public content snapshot JSON.",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.manifest = self._load_manifest(options["manifest"])
        self.stats = {model: Counter() for model in MODELS}
        self.images = {"verified": 0, "missing": []}
        self.provenance = []
        self.stale = {model: [] for model in MODELS}

        with transaction.atomic():
            self._import_locations()
            self._import_articles()
            self._import_events()
            self._import_distributions()
            self._report_stale()

        self._print_report()

    def _load_manifest(self, path):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Manifest tidak dapat dibaca: {exc}") from exc

        if data.get("schema_version") != 1:
            raise CommandError("schema_version manifest tidak didukung.")
        for key in ("articles", "locations", "events", "distributions"):
            if not isinstance(data.get(key), list):
                raise CommandError(f"Bagian '{key}' pada manifest tidak valid.")
        return data

    def _parse_datetime(self, value):
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise CommandError(f"Datetime sumber tidak valid: {value!r}") from exc

    def _parse_date(self, value):
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise CommandError(f"Tanggal sumber tidak valid: {value!r}") from exc

    def _image_name(self, item, existing):
        image = item.get("image") or {}
        path = image.get("path")
        if not path:
            self.images["missing"].append(f"{item['slug']}: tidak ada path gambar")
            return existing.image.name if existing and existing.image else None

        storage = Article._meta.get_field("image").storage
        if not storage.exists(path):
            self.images["missing"].append(f"{item['slug']}: {path} tidak ada")
            return existing.image.name if existing and existing.image else None

        try:
            with storage.open(path, "rb") as image_file:
                digest = hashlib.sha256(image_file.read()).hexdigest()
        except OSError as exc:
            self.images["missing"].append(f"{item['slug']}: gagal membaca {path} ({exc})")
            return existing.image.name if existing and existing.image else None

        expected = image.get("sha256")
        if expected and digest != expected:
            self.images["missing"].append(f"{item['slug']}: hash gambar tidak cocok")
            return existing.image.name if existing and existing.image else None

        self.images["verified"] += 1
        return path

    def _import_locations(self):
        for item in self.manifest["locations"]:
            self.stats["locations"]["discovered"] += 1
            matches = list(Location.objects.filter(name=item["name"])[:2])
            if len(matches) > 1:
                self.stats["locations"]["conflicts"] += 1
                self.stdout.write(f"CONFLICT location: nama ganda {item['name']}")
                continue
            existing = matches[0] if matches else None

            category = item["category"]
            if category not in Location.Category.values:
                raise CommandError(f"Kategori lokasi tidak valid: {category!r}")
            description = item.get("description") or ""
            if len(description) > Location._meta.get_field("description").max_length:
                raise CommandError(f"Deskripsi lokasi terlalu panjang: {item['name']}")

            desired = {
                "name": item["name"],
                "category": category,
                "description": description,
                "address": item["address"],
                "city": item["city"],
                "open_hours": item["open_hours"],
                "latitude": Decimal(item["latitude"]),
                "longitude": Decimal(item["longitude"]),
                "is_active": item.get("is_active", True),
            }
            # Province dan contact_person tidak dipublikasikan di halaman sumber.
            if item.get("province") is not None:
                desired["province"] = item["province"]
            elif existing is None:
                desired["province"] = ""
            if item.get("contact_person") is not None:
                desired["contact_person"] = item["contact_person"]
            elif existing is None:
                desired["contact_person"] = ""

            changed = self._assign(existing, desired)
            if existing is None:
                self.stats["locations"]["created"] += 1
                self.provenance.append((item["source_url"], f"Location: {item['name']}"))
                if not self.dry_run:
                    Location.objects.create(**self._object_values(desired))
            elif changed:
                self.stats["locations"]["updated"] += 1
                self.provenance.append((item["source_url"], f"Location: {item['name']}"))
                if not self.dry_run:
                    existing.save()
            else:
                self.stats["locations"]["unchanged"] += 1

    def _import_articles(self):
        imported = {}
        for item in self.manifest["articles"]:
            self.stats["articles"]["discovered"] += 1
            existing = self._find_article(item)
            desired = {
                "title": item["title"],
                "slug": item["slug"],
                "summary": item["summary"],
                "body": item["body"],
                "category": item["category"],
                "is_published": True,
                "published_at": self._parse_datetime(item["published_at"]),
            }
            if item["category"] not in Article.Category.values:
                raise CommandError(f"Kategori artikel tidak valid: {item['category']!r}")

            if existing and existing.slug != item["slug"]:
                if Article.objects.filter(slug=item["slug"]).exclude(pk=existing.pk).exists():
                    self.stats["articles"]["conflicts"] += 1
                    self.stdout.write(f"CONFLICT article: slug sudah dipakai {item['slug']}")
                    continue

            image_name = self._image_name(item, existing)
            if image_name:
                desired["image"] = image_name

            changed = self._assign(existing, desired)
            if existing is None:
                if not image_name:
                    desired.pop("image", None)
                self.stats["articles"]["created"] += 1
                imported[item["slug"]] = True
                self.provenance.append((item["source_url"], f"Article: {item['slug']}"))
                if not self.dry_run:
                    article = Article(**desired)
                    article.save()
            else:
                if changed:
                    self.stats["articles"]["updated"] += 1
                    self.provenance.append((item["source_url"], f"Article: {item['slug']}"))
                    if not self.dry_run:
                        existing.save()
                else:
                    self.stats["articles"]["unchanged"] += 1
                imported[existing.slug] = True
        return imported

    def _find_article(self, item):
        exact = Article.objects.filter(slug=item["slug"]).first()
        if exact:
            return exact
        for alias in item.get("local_slug_aliases", []):
            matches = list(Article.objects.filter(slug=alias)[:2])
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise CommandError(f"Slug alias ganda: {alias!r}")
        return None

    def _import_events(self):
        location_names = {item["name"] for item in self.manifest["locations"]}
        for item in self.manifest["events"]:
            self.stats["events"]["discovered"] += 1
            if item["location_name"] not in location_names:
                raise CommandError(f"Lokasi agenda tidak ada di manifest: {item['location_name']}")
            location = Location.objects.filter(name=item["location_name"]).first()
            if location is None:
                self.stats["events"]["skipped"] += 1
                self.stdout.write(f"SKIP event: lokasi tidak ditemukan {item['location_name']}")
                continue

            start_at = self._parse_datetime(item["start_at"])
            end_at = self._parse_datetime(item["end_at"]) if item.get("end_at") else None
            if end_at and end_at < start_at:
                raise CommandError(f"Waktu agenda tidak valid: {item['title']}")

            existing = self._find_event(item, location, start_at)
            desired = {
                "title": item["title"],
                "description": item.get("description", ""),
                "start_at": start_at,
                "end_at": end_at,
                "location": location,
                "is_published": item.get("is_published", True),
            }
            changed = self._assign(existing, desired)
            if existing is None:
                self.stats["events"]["created"] += 1
                self.provenance.append((item["source_url"], f"Event: {item['title']}"))
                if not self.dry_run:
                    Event.objects.create(**self._object_values(desired))
            elif changed:
                self.stats["events"]["updated"] += 1
                self.provenance.append((item["source_url"], f"Event: {item['title']}"))
                if not self.dry_run:
                    existing.save()
            else:
                self.stats["events"]["unchanged"] += 1

    def _find_event(self, item, location, start_at):
        exact = Event.objects.filter(
            title=item["title"], location=location, start_at=start_at
        ).first()
        if exact:
            return exact
        for alias in item.get("local_title_aliases", []):
            matches = list(Event.objects.filter(title=alias)[:2])
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise CommandError(f"Alias agenda ganda: {alias!r}")
        return None

    def _import_distributions(self):
        for item in self.manifest["distributions"]:
            self.stats["distributions"]["discovered"] += 1
            destination = Location.objects.filter(name=item["destination_name"]).first()
            if destination is None:
                self.stats["distributions"]["skipped"] += 1
                self.stdout.write(f"SKIP distribution: tujuan tidak ditemukan {item['destination_name']}")
                continue

            distributed_at = self._parse_date(item["distributed_at"])
            matches = list(
                Distribution.objects.filter(
                    destination=destination, distributed_at=distributed_at
                )[:2]
            )
            if len(matches) > 1:
                self.stats["distributions"]["conflicts"] += 1
                self.stdout.write("CONFLICT distribution: beberapa record cocok")
                continue
            existing = matches[0] if matches else None
            desired = {
                "item_name": item["item_name"],
                "description": item.get("description", ""),
                "quantity": item["quantity"],
                "destination": destination,
                "status": item["status"],
                "distributed_at": distributed_at,
            }
            if item["status"] not in Distribution.Status.values:
                raise CommandError(f"Status penyaluran tidak valid: {item['status']!r}")
            changed = self._assign(existing, desired)
            if existing is None:
                self.stats["distributions"]["created"] += 1
                self.provenance.append((item["source_url"], f"Distribution: {item['item_name']}"))
                if not self.dry_run:
                    Distribution.objects.create(**self._object_values(desired))
            elif changed:
                self.stats["distributions"]["updated"] += 1
                self.provenance.append((item["source_url"], f"Distribution: {item['item_name']}"))
                if not self.dry_run:
                    existing.save()
            else:
                self.stats["distributions"]["unchanged"] += 1

    def _assign(self, instance, desired):
        changed = False
        for field, value in desired.items():
            if instance is None or getattr(instance, field) != value:
                changed = True
                if instance is not None:
                    setattr(instance, field, value)
        return changed

    def _object_values(self, desired):
        return {field: value for field, value in desired.items() if field != "image"}

    def _report_stale(self):
        source_slugs = {item["slug"] for item in self.manifest["articles"]}
        for item in self.manifest["articles"]:
            source_slugs.update(item.get("local_slug_aliases", []))
        source_locations = {item["name"] for item in self.manifest["locations"]}
        source_events = {item["title"] for item in self.manifest["events"]}
        for item in self.manifest["events"]:
            source_events.update(item.get("local_title_aliases", []))
        source_distributions = {
            (item["destination_name"], item["distributed_at"])
            for item in self.manifest["distributions"]
        }
        for article in Article.objects.all():
            if article.slug not in source_slugs:
                self.stale["articles"].append(article.slug)
        for location in Location.objects.all():
            if location.name not in source_locations:
                self.stale["locations"].append(location.name)
        for event in Event.objects.all():
            if event.title not in source_events:
                self.stale["events"].append(event.title)
        for distribution in Distribution.objects.all():
            key = (distribution.destination.name, str(distribution.distributed_at))
            if key not in source_distributions:
                self.stale["distributions"].append(str(distribution))

    def _print_report(self):
        mode = "DRY-RUN" if self.dry_run else "APPLIED"
        self.stdout.write(f"PWS public content import ({mode})")
        for model in MODELS:
            stats = self.stats[model]
            self.stdout.write(
                f"{model}: discovered={stats['discovered']} created={stats['created']} "
                f"updated={stats['updated']} unchanged={stats['unchanged']} "
                f"skipped={stats['skipped']} conflicts={stats['conflicts']}"
            )
        self.stdout.write(f"images: verified={self.images['verified']} missing={len(self.images['missing'])}")
        for missing in self.images["missing"]:
            self.stdout.write(f"  missing image: {missing}")
        for model, values in self.stale.items():
            if values:
                self.stdout.write(f"stale local {model} (not deleted): {', '.join(values)}")
        if self.dry_run:
            self.stdout.write("Dry-run: tidak ada perubahan database.")
