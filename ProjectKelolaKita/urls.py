""" 
URL configuration for ProjectKelolaKita project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from ProjectKelolaKita.views import landing_page, show_location, create_location, delete_location, location_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing_page'),
    path('locations/', show_location, name="show_location"),
    path('locations/add/', create_location, name="create_location"),
    path("locations/<uuid:location_id>/delete/",delete_location,name="delete_location"),
    path('location/<uuid:pk>/', location_detail, name='location_detail'),
    path('jadwal/', include('Schedule.urls')),
    path('penanganan/', include('penanganan.urls')),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
