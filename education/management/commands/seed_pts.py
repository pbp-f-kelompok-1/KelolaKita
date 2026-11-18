"""Isi database pengembangan dengan fixture demonstrasi PTS."""
import json
import os
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from education.models import Article, Distribution, Event
from Location.models import Location
from penanganan.models import FotoBarang, Pemeriksaan
from Schedule.models import Penjadwalan
from Schedule.views import SESSION_QUOTAS


def load_dataset(name):
    filename = settings.BASE_DIR / "seed_data" / name
    return json.loads(filename.read_text(encoding="utf-8"))


def demo_uuid(record_id):
    return uuid5(NAMESPACE_URL, f"https://kelolakita.invalid/pts/{record_id}")


def ensure_record(queryset, fields, **identity):
    existing = queryset.filter(**identity).first()
    if existing is not None:
        return existing
    record = queryset.model(**fields, **identity)
    record.full_clean()
    record.save()
    return record


class Command(BaseCommand):
    help = "Tambahkan data demonstrasi sintetis PTS ke SQLite lokal."

    @transaction.atomic
    def seed(self, datasets):
        today = timezone.localdate()
        now = timezone.now()
        accounts = []
        for index in range(1, 51):
            username = f"pts_demo_{index:02d}"
            email = f"{username}@kelolakita.invalid"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "first_name": "Warga Demo", "last_name": str(index)},
            )
            if user.email != email or user.is_staff or user.is_superuser:
                raise CommandError(f"Identitas akun demo bentrok: {username}.")
            if created:
                user.set_password(os.environ.get("PTS_DEMO_PASSWORD") if index == 1 else None)
                user.save(update_fields=["password"])
            accounts.append(user)

        owner = accounts[0]
        locations = {}
        for row in datasets["location"]:
            fields = {
                key: row[key] for key in (
                    "description", "address", "contact_person", "open_hours",
                    "province", "city", "category", "latitude", "longitude",
                )
            }
            fields.update(name=f"{row['name']} (Demo)", is_active=True)
            for key in ("latitude", "longitude"):
                fields[key] = f"{row[key]:.6f}"
            locations[row["dataset_id"]] = ensure_record(
                Location.objects, fields, pk=demo_uuid(row["dataset_id"])
            )
        partners = [location for location in locations.values() if location.category != Location.Category.bank_sampah]

        banks = [location for location in locations.values() if location.category == Location.Category.bank_sampah]

        items = {}
        attachments = []
        for row in datasets["penanganan"]:
            fields = {
                key: row[key] for key in (
                    "nama_barang", "kategori_barang", "kondisi_barang",
                    "rekomendasi_penanganan", "mitra_rekomendasi",
                )
            }
            fields.update(
                pengguna=owner,
                catatan_tambahan=f"Data demonstrasi. {row['catatan_tambahan']}",
                kategori_penanganan=row["kategori_penanganan_target"],
            )
            # Dataset jadwal berisi satu jadwal untuk tiap barang, jadi semua
            # barang yang menjadi sumber jadwal harus sudah diperiksa.
            if fields["kategori_penanganan"] == "Menunggu":
                fields["kategori_penanganan"] = "Reuse"
            item = ensure_record(Pemeriksaan.objects, fields, pk=demo_uuid(row["dataset_id"]))
            items[row["dataset_id"]] = item
            attachments.append((item, row["dataset_id"].rsplit("-", 1)[-1]))

        ready_item = ensure_record(
            Pemeriksaan.objects,
            dict(pengguna=owner, nama_barang="Kotak penyimpanan lipat (Demo)",
                 kategori_barang="Lainnya", kondisi_barang="Layak pakai",
                 kategori_penanganan="Reuse", catatan_tambahan="Barang demo siap dijadwalkan."),
            pk=demo_uuid("ready-to-schedule"),
        )
        attachments.append((ready_item, "051"))

        bookings = []
        for index, row in enumerate(datasets["schedule"]):
            item = items[row["pemeriksaan_ref"]]
            notes = f"{row['notes']} {row['dataset_id']}"
            existing = Penjadwalan.objects.filter(barang=item, notes=notes).first()
            if existing is not None:
                bookings.append(existing)
                continue
            if item.penjadwalan_set.exists():
                raise CommandError(f"Barang demo sudah mempunyai jadwal lain: {item.nama_barang}.")
            day_offset = row["day_offset"] if index % 4 >= 2 else -row["day_offset"]
            day = today + timedelta(days=day_offset)
            while Penjadwalan.objects.filter(tanggal=day, sesi=row["sesi"]).count() >= SESSION_QUOTAS[row["sesi"]]:
                day += timedelta(days=1 if day_offset > 0 else -1)
            location = locations.get(row["lokasi_ref"])
            if row["lokasi_ref"] == "ACTIVE_VERIFIED_LOCATION":
                location = banks[index % len(banks)]
            booking = Penjadwalan(
                metode=row["metode"], sesi=row["sesi"], tanggal=day,
                nama_penerima=row["nama_penerima"], nomor_hp=row["nomor_hp"],
                alamat_penjemputan=row["alamat_penjemputan"],
                lokasi_mitra=location, notes=notes,
            )
            booking.full_clean()
            booking.save()
            booking.barang.add(item)
            bookings.append(booking)

        articles = []
        for index, row in enumerate(datasets["articles"]):
            fields = {key: row[key] for key in ("title", "summary", "body", "category")}
            fields.update(is_published=True, published_at=now - timedelta(days=index + 1))
            articles.append(ensure_record(Article.objects, fields, slug=row["record_id"].lower()))

        events = []
        for index, row in enumerate(datasets["events"]):
            start = (now + timedelta(days=index + 1)).replace(hour=9, minute=0, second=0, microsecond=0)
            fields = dict(
                title=row["title"], location=partners[index % len(partners)],
                start_at=start, end_at=start + timedelta(hours=2), is_published=True,
            )
            events.append(ensure_record(Event.objects, fields, description=row["description"]))

        distributions = []
        for index, row in enumerate(datasets["distributions"]):
            fields = dict(
                item_name=row["item_name"], quantity=row["quantity"],
                destination=partners[index % len(partners)],
                status=Distribution.Status.delivered, distributed_at=today - timedelta(days=index),
            )
            distributions.append(ensure_record(Distribution.objects, fields, description=row["description"]))

        legacy_images = {
            f"static/img/pts-demo/{row['foto'].rsplit('/', 1)[-1]}"
            for row in datasets["penanganan"]
        }
        photos_dir = settings.BASE_DIR / "seed_data" / "photos" / "items"
        for item, number in attachments:
            path = photos_dir / f"{number}.webp"
            name = f"static/img/pts-demo/items/{path.name}"
            photos = item.foto_barang.all()
            if photos.exclude(gambar__in=legacy_images | {name}).exists():
                continue
            if not default_storage.exists(name):
                with path.open("rb") as image:
                    default_storage.save(name, File(image))
            if not photos.filter(gambar=name).exists():
                legacy_photo = photos.filter(gambar__in=legacy_images).first()
                if legacy_photo:
                    legacy_photo.gambar = name
                    legacy_photo.save(update_fields=["gambar"])
                else:
                    FotoBarang.objects.create(pemeriksaan=item, gambar=name)

        return {
            "Akun & profil": len(accounts),
            "Lokasi": len(locations),
            "Pengajuan": len(items) + 1,
            "Jadwal": len(bookings),
            "Artikel": len(articles),
            "Agenda": len(events),
            "Penyaluran": len(distributions),
        }

    def handle(self, *args, **options):
        if not settings.DEBUG or connection.vendor != "sqlite":
            raise CommandError("Seed PTS hanya untuk SQLite pengembangan.")
        datasets = {
            name: load_dataset(f"{name}_seed_2026.json")["records"]
            for name in ("location", "penanganan", "schedule")
        }
        education = load_dataset("education_pts_2026.json")
        datasets.update({name: education[name] for name in ("articles", "events", "distributions")})
        for name, records in datasets.items():
            ids = {row.get("dataset_id", row.get("record_id")) for row in records}
            if len(records) != 50 or len(ids) != 50 or None in ids:
                raise CommandError(f"Dataset {name} harus berisi 50 ID unik.")
        counts = self.seed(datasets)
        for section, count in counts.items():
            self.stdout.write(f"{section}: {count}")
        self.stdout.write(self.style.SUCCESS("Seed PTS lokal siap."))
