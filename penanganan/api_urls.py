from django.urls import path

from . import api_views


app_name = "penanganan_api"

urlpatterns = [
    path(
        "pengajuan/",
        api_views.pemeriksaan_list,
        name="api_v1_pengajuan_list",
    ),
    path(
        "pengajuan/<uuid:pk>/",
        api_views.pemeriksaan_detail,
        name="api_v1_pengajuan_detail",
    ),
]