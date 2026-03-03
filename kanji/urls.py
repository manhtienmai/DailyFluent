from django.urls import path
from . import views

app_name = "kanji"

urlpatterns = [
    path("levels/", views.kanji_levels, name="levels"),
    # API must come before the wildcard <str:char>/ pattern
    path("api/progress/update/", views.update_kanji_progress, name="update_progress"),
    path("<str:char>/practice/", views.kanji_practice, name="practice"),
    path("<str:char>/", views.kanji_detail, name="detail"),
]
