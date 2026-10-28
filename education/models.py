from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator
from django.templatetags.static import static
from django.utils import timezone
from django.utils.text import slugify

from Location.models import Location

ARTICLE_IMAGE_MAX_BYTES = 5 * 1024 * 1024
ARTICLE_IMAGE_MIN_WIDTH = 800
ARTICLE_IMAGE_MIN_HEIGHT = 450
ARTICLE_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
ARTICLE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ARTICLE_IMAGE_PLACEHOLDER = "images/education/articles/article-placeholder.svg"

ARTICLE_CATEGORY_LABELS = {
    "reuse": "Guna ulang",
    "reduce": "Pengurangan sampah",
}


def validate_article_image(image):
    if image.size > ARTICLE_IMAGE_MAX_BYTES:
        raise ValidationError("Ukuran file gambar maksimal 5 MB.")

    if Path(image.name).suffix.lower() not in ARTICLE_IMAGE_EXTENSIONS:
        raise ValidationError("Format gambar harus berupa JPG, PNG, atau WebP.")

    try:
        with Image.open(image) as opened:
            image_format = opened.format
            width, height = opened.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValidationError("File gambar tidak dapat dibaca.")
    finally:
        image.seek(0)

    if image_format not in ARTICLE_IMAGE_FORMATS:
        raise ValidationError("Format gambar harus berupa JPG, PNG, atau WebP.")

    if width < ARTICLE_IMAGE_MIN_WIDTH or height < ARTICLE_IMAGE_MIN_HEIGHT:
        raise ValidationError(
            "Gambar harus berukuran minimal 800 × 450 piksel."
        )


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Article(models.Model):
    class Category(models.TextChoices):
        panduan = "panduan", "Panduan"
        reuse = "reuse", "Reuse"
        reduce = "reduce", "Reduce"
        kebiasaan = "kebiasaan", "Kebiasaan"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=300)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.panduan)
    image = models.ImageField(
        upload_to="education/articles/%Y/%m/",
        blank=True,
        null=True,
        validators=[validate_article_image],
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["is_published", "published_at"], name="article_pub_idx"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "artikel"
            slug, number = base, 2
            # shortcut: unique constraint + retry loop, bukan concurrency-safe.
            # upgrade path: tangani IntegrityError / gunakan slug sequence bila volume naik.
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{number}"
                number += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def read_minutes(self):
        return max(1, round(len(self.body.split()) / 200))

    @property
    def category_label(self):
        return ARTICLE_CATEGORY_LABELS.get(
            self.category, self.get_category_display()
        )

    @property
    def cover(self):
        if self.image:
            return {"src": self.image.url, "alt": f"Gambar artikel {self.title}"}
        return {
            "src": static(ARTICLE_IMAGE_PLACEHOLDER),
            "alt": f"Ilustrasi artikel {self.title}",
        }


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="events")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["is_published", "start_at"], name="event_pub_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__isnull=True) | models.Q(end_at__gte=models.F("start_at")),
                name="event_end_after_start",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValidationError({"end_at": "Waktu selesai tidak boleh lebih awal daripada waktu mulai."})


class Distribution(models.Model):
    class Status(models.TextChoices):
        planned = "planned", "Direncanakan"
        delivered = "delivered", "Tersalurkan"
        cancelled = "cancelled", "Dibatalkan"

    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    destination = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="distributions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.planned)
    distributed_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="distribution_quantity_gte_1",
            ),
        ]

    def __str__(self):
        return f"{self.item_name} -> {self.destination}"

    def clean(self):
        errors = {}
        if self.destination_id and self.destination.category not in (
            Location.Category.panti_asuhan,
            Location.Category.komunitas,
        ):
            errors["destination"] = "Tujuan penyaluran harus berupa panti asuhan atau komunitas."
        if self.status == self.Status.delivered and not self.distributed_at:
            errors["distributed_at"] = "Tanggal penyaluran wajib diisi untuk status Tersalurkan."
        if errors:
            raise ValidationError(errors)
