from django.urls import path

from Schedule import views

urlpatterns = [
    path('', views.show_schedule, name='show_schedule'),
]
