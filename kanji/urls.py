from django.urls import path
from . import views

app_name = "kanji"

urlpatterns = [
    path("levels/", views.kanji_levels, name="levels"),
    path("<str:char>/", views.kanji_detail, name="detail"),
]
