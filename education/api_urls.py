from django.urls import path
from django.utils import timezone
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer

from education.models import Article
from education.serializers import (
    ArticleDetailSerializer,
    ArticleSerializer,
    DistributionSerializer,
    EventSerializer,
)
from education.views import public_distributions, published_events


class PublicReadAPI:
    authentication_classes = ()
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        # These routes expose only public, anonymous data to Flutter Web.
        response["Access-Control-Allow-Origin"] = "*"
        return response


class EducationPagination(PageNumberPagination):
    page_size = 20


class ArticleList(PublicReadAPI, generics.ListAPIView):
    serializer_class = ArticleSerializer
    pagination_class = EducationPagination

    def get_queryset(self):
        return Article.objects.published().order_by("-published_at", "-pk")


class ArticleDetail(PublicReadAPI, generics.RetrieveAPIView):
    lookup_field = "slug"
    serializer_class = ArticleDetailSerializer

    def get_queryset(self):
        return Article.objects.published()


class EventList(PublicReadAPI, generics.ListAPIView):
    serializer_class = EventSerializer
    pagination_class = EducationPagination

    def get_queryset(self):
        return published_events().filter(start_at__gte=timezone.now()).order_by("start_at", "pk")


class DistributionList(PublicReadAPI, generics.ListAPIView):
    serializer_class = DistributionSerializer
    pagination_class = EducationPagination

    def get_queryset(self):
        return public_distributions().order_by("-distributed_at", "-pk")


urlpatterns = [
    path("articles/", ArticleList.as_view(), name="education_api_articles"),
    path("articles/<slug:slug>/", ArticleDetail.as_view(), name="education_api_article"),
    path("events/", EventList.as_view(), name="education_api_events"),
    path("distributions/", DistributionList.as_view(), name="education_api_distributions"),
]
