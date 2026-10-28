import mimetypes
from pathlib import PurePosixPath
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from education.forms import ArticleForm, DistributionForm, EventForm
from education.models import Article, Distribution, Event
from Location.models import Location

BUSINESS_TIMEZONE = ZoneInfo("Asia/Jakarta")
ARTICLE_IMAGE_PREFIX = "education/articles/"
ARTICLE_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def published_events():
    return Event.objects.filter(is_published=True).select_related("location")


def public_distributions():
    return Distribution.objects.filter(
        status=Distribution.Status.delivered,
        distributed_at__isnull=False,
        distributed_at__lte=timezone.localdate(timezone=BUSINESS_TIMEZONE),
        destination__category__in=[
            Location.Category.panti_asuhan,
            Location.Category.komunitas,
        ],
    ).select_related("destination")


class PublicEducationContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = "edukasi"
        return context


def article_image(request, path):
    """Serve only images that are registered as article covers.

    Public requests are limited to published articles; staff may preview drafts.
    """
    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or "\x00" in path
        or ".." in PurePosixPath(path).parts
    ):
        raise Http404

    image_name = f"{ARTICLE_IMAGE_PREFIX}{path}"
    articles = Article.objects.filter(image=image_name)
    article = articles.first()
    if article is None:
        raise Http404

    is_staff = (
        request.user.is_authenticated
        and request.user.is_active
        and request.user.is_staff
    )
    is_public = articles.published().exists()
    if not is_public and not is_staff:
        raise Http404

    if not article.image_available:
        raise Http404

    content_type, _ = mimetypes.guess_type(article.image.name)
    if content_type not in ARTICLE_IMAGE_CONTENT_TYPES:
        raise Http404

    try:
        image_file = article.image.open("rb")
    except OSError:
        raise Http404

    # shortcut: Django/gunicorn streams each image (no CDN/Web server); move to
    # persistent object storage if media volume or traffic grows.
    response = FileResponse(image_file, content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = (
        "public, max-age=3600" if is_public else "private, no-store"
    )
    return response


def public_home(request):
    articles = Article.objects.published()
    featured = articles.first()
    context = {
        "featured": featured,
        "articles": articles.exclude(pk=featured.pk) if featured else articles,
        "events": published_events().filter(start_at__gte=timezone.now()),
        "partners": Location.objects.filter(
            is_active=True,
            category__in=[
                Location.Category.panti_asuhan,
                Location.Category.komunitas,
            ],
        ).order_by("name"),
        "distributions": public_distributions().order_by(
            "-distributed_at", "-created_at"
        )[:5],
        "active_nav": "edukasi",
    }
    return render(request, "education/public_home.html", context)


class ArticleListView(PublicEducationContextMixin, ListView):
    template_name = "education/public_article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return Article.objects.published()


class ArticleDetailView(PublicEducationContextMixin, DetailView):
    model = Article
    template_name = "education/public_article_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        return Article.objects.published()


class EventListView(PublicEducationContextMixin, ListView):
    template_name = "education/public_event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return published_events().filter(start_at__gte=timezone.now())


class EventDetailView(PublicEducationContextMixin, DetailView):
    model = Event
    template_name = "education/public_event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return published_events()


class DistributionListView(PublicEducationContextMixin, ListView):
    template_name = "education/public_distribution_list.html"
    context_object_name = "distributions"

    def get_queryset(self):
        return public_distributions().order_by("-distributed_at", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = self.object_list.aggregate(
            total_records=Count("id"),
            total_quantity=Sum("quantity"),
            total_destinations=Count("destination", distinct=True),
        )
        return context



class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("admin:login")

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = "edukasi"
        return context

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class ManageDashboard(StaffRequiredMixin, TemplateView):
    template_name = "education/manage_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["articles"] = Article.objects.all()
        context["events"] = Event.objects.select_related("location")
        context["distributions"] = Distribution.objects.select_related("destination")
        context["now"] = timezone.now()
        return context


class ManageFormMixin(StaffRequiredMixin):
    template_name = "education/manage_form.html"
    success_url = reverse_lazy("education_manage")
    form_title = ""
    success_message = "Data berhasil disimpan."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = self.form_title
        return context

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class ManageCreateView(ManageFormMixin, CreateView):
    pass


class ManageUpdateView(ManageFormMixin, UpdateView):
    pass


class ManageDeleteView(StaffRequiredMixin, DeleteView):
    template_name = "education/manage_confirm_delete.html"
    success_url = reverse_lazy("education_manage")
    success_message = "Data berhasil dihapus."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class ArticleCreateView(ManageCreateView):
    model = Article
    form_class = ArticleForm
    form_title = "Tambah artikel"
    success_message = "Artikel berhasil disimpan."


class ArticleUpdateView(ManageUpdateView):
    model = Article
    form_class = ArticleForm
    form_title = "Ubah artikel"
    success_message = "Artikel berhasil diperbarui."


class ArticleDeleteView(ManageDeleteView):
    model = Article
    success_message = "Artikel berhasil dihapus."


class EventCreateView(ManageCreateView):
    model = Event
    form_class = EventForm
    form_title = "Tambah agenda"
    success_message = "Agenda berhasil disimpan."


class EventUpdateView(ManageUpdateView):
    model = Event
    form_class = EventForm
    form_title = "Ubah agenda"
    success_message = "Agenda berhasil diperbarui."


class EventDeleteView(ManageDeleteView):
    model = Event
    success_message = "Agenda berhasil dihapus."


class DistributionCreateView(ManageCreateView):
    model = Distribution
    form_class = DistributionForm
    form_title = "Tambah catatan penyaluran"
    success_message = "Catatan penyaluran berhasil disimpan."


class DistributionUpdateView(ManageUpdateView):
    model = Distribution
    form_class = DistributionForm
    form_title = "Ubah catatan penyaluran"
    success_message = "Catatan penyaluran berhasil diperbarui."


class DistributionDeleteView(ManageDeleteView):
    model = Distribution
    success_message = "Catatan penyaluran berhasil dihapus."
