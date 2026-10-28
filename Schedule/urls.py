from django.urls import path

from Schedule import views

urlpatterns = [
    path('', views.show_schedule, name='show_schedule'),
    path('riwayat/', views.schedule_list, name='schedule_list'),
    path('riwayat/<int:pk>/batalkan/', views.cancel_schedule, name='cancel_schedule'),
]
