from django.urls import path

from jadwal import views

urlpatterns = [
    path('', views.show_schedule, name='show_schedule'),
]
