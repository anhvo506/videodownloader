from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('download_success/', views.download_success, name='download_success'),
    path('download_failure/', views.download_failure, name='download_failure'),
]
