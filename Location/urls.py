from django.urls import path

from Location import views
from ProjectKelolaKita.views import landing_page

app_name = "Location"

# Route halaman pengelolaan lokasi berada di ProjectKelolaKita/urls.py.
# Di sini hanya endpoint yang di-include di bawah /locations/api/.
urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('api/geocode/', views.geocode_location, name='geocode_location'),
]
