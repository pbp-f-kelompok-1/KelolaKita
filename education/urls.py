from django.urls import path

from education import views

urlpatterns = [
    path("", views.public_home, name="education_home"),
    path("artikel/", views.ArticleListView.as_view(), name="article_list"),
    path("artikel/<slug:slug>/", views.ArticleDetailView.as_view(), name="article_detail"),
    path("agenda/", views.EventListView.as_view(), name="event_list"),
    path("agenda/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
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
