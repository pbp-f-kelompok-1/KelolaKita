from django.urls import path
from Location import views

from Location.views import landing_page
from Location.views import show_main

app_name = "main"

urlpatterns = [
    path('', views.index, name='index'),
]