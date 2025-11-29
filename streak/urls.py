# streak/urls.py
from django.urls import path

from . import views

app_name = "streak"

urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path("api/status/", views.streak_status_api, name="status_api"),
]
