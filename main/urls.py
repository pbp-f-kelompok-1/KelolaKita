from django.urls import path
from main import views

from main.views import landing_page
from main.views import show_main

app_name = "main"

urlpatterns = [
    path('', views.index, name='index'),
]