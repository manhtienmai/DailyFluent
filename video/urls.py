from django.urls import path
from . import views

app_name = "video"

urlpatterns = [
    path("", views.video_list, name="list"),
    path("<slug:slug>/", views.video_detail, name="detail"),
]
