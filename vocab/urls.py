from django.urls import path
from . import views

app_name = "vocab"

urlpatterns = [
    path("", views.vocab_list, name="list"),
    path("phrases/", views.phrase_list, name="phrases"),
    path("flashcards/", views.flashcard_session, name="flashcards"),
    path("flashcards/grade/", views.flashcard_grade, name="flashcard_grade"),
    path("typing/", views.typing_review, name="typing"),
    path("study-status/", views.study_status, name="study_status"),
    path("word/<int:vocab_id>/", views.vocab_detail, name="detail"),
    path("progress/", views.vocab_progress, name="progress"),   # <--- mới
]
