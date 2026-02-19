from django.urls import path
from . import views

app_name = "grammar"

urlpatterns = [
    path("", views.grammar_home, name="home"),
    path("books/", views.grammar_book_list, name="book_list"),
    path("books/<slug:slug>/", views.grammar_book_detail, name="book_detail"),
    path("n5/", views.grammar_level_detail, {"level": "N5"}, name="level_n5"),
    path("n4/", views.grammar_level_detail, {"level": "N4"}, name="level_n4"),
    path("n3/", views.grammar_level_detail, {"level": "N3"}, name="level_n3"),
    path("n2/", views.grammar_level_detail, {"level": "N2"}, name="level_n2"),
    path("n1/", views.grammar_level_detail, {"level": "N1"}, name="level_n1"),
    path("exercise/<slug:slug>/", views.grammar_exercise, name="exercise"),
    path("api/check-answer/", views.api_check_answer, name="api_check_answer"),
    path("api/submit-exercise/", views.api_submit_exercise, name="api_submit_exercise"),
    # Point detail last to avoid shadowing other slugs
    path("<slug:slug>/", views.grammar_point_detail, name="point_detail"),
    # Legacy aliases
    path("list/", views.grammar_home, name="list"),
]
