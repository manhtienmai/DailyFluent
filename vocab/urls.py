from django.urls import path
from . import views

app_name = "vocab"

urlpatterns = [
    path("", views.vocab_list, name="list"),
    path("flashcards/", views.flashcard_session, name="flashcards"),
    path("flashcards/grade/", views.flashcard_grade, name="flashcard_grade"),
    path("progress/", views.vocab_progress, name="progress"),   # <--- mới
]
