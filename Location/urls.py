from    django.urls import path
from Location import views

app_name = "Location"

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('api/geocode/', views.geocode_location, name='geocode_location'),
]