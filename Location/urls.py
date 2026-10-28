from django.urls import path

from Location import views

urlpatterns = [
    path('locations/', views.show_location, name='show_location'),
    path('locations/add/', views.create_location, name='create_location'),
    path('locations/<uuid:location_id>/delete/', views.delete_location, name='delete_location'),
    path('location/<uuid:pk>/', views.location_detail, name='location_detail'),
]
