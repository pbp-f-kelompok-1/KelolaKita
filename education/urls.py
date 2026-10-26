from django.urls import path

from education import views

urlpatterns = [
    path("kelola/", views.ManageDashboard.as_view(), name="education_manage"),
    path("kelola/artikel/tambah/", views.ArticleCreateView.as_view(), name="article_create"),
    path("kelola/artikel/<int:pk>/ubah/", views.ArticleUpdateView.as_view(), name="article_update"),
    path("kelola/artikel/<int:pk>/hapus/", views.ArticleDeleteView.as_view(), name="article_delete"),
    path("kelola/agenda/tambah/", views.EventCreateView.as_view(), name="event_create"),
    path("kelola/agenda/<int:pk>/ubah/", views.EventUpdateView.as_view(), name="event_update"),
    path("kelola/agenda/<int:pk>/hapus/", views.EventDeleteView.as_view(), name="event_delete"),
    path("kelola/penyaluran/tambah/", views.DistributionCreateView.as_view(), name="distribution_create"),
    path("kelola/penyaluran/<int:pk>/ubah/", views.DistributionUpdateView.as_view(), name="distribution_update"),
    path("kelola/penyaluran/<int:pk>/hapus/", views.DistributionDeleteView.as_view(), name="distribution_delete"),
]
