from django.urls import path
from . import views

app_name = "vocab"

urlpatterns = [
    path("", views.vocab_list, name="list"),
    path("english/", views.english_list, name="english_list"),
    path("phrases/", views.phrase_list, name="phrases"),
    path("flashcards/", views.flashcard_session, name="flashcards"),
    path("flashcards/grade/", views.flashcard_grade, name="flashcard_grade"),
    path("flashcards/english/", views.english_flashcard_session, name="flashcards_english"),
    path("flashcards/english/grade/", views.english_flashcard_grade, name="flashcard_grade_english"),
    path("typing/", views.typing_review, name="typing"),
    path("study-status/", views.study_status, name="study_status"),
    path("word/<int:vocab_id>/", views.vocab_detail, name="detail"),
    path("progress/", views.vocab_progress, name="progress"),
    path("games/", views.vocab_games, name="games"),
    # Standalone vocabulary games
    path("games/mcq/", views.game_mcq, name="game_mcq"),
    path("games/matching/", views.game_matching, name="game_matching"),
    path("games/listening/", views.game_listening, name="game_listening"),
    path("games/fill/", views.game_fill, name="game_fill"),
    path("games/dictation/", views.game_dictation, name="game_dictation"),
]



