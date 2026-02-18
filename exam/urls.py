from django.urls import path
from . import views

app_name = "exam"

urlpatterns = [
    path("", views.exam_list, name="exam_list"),
    path("toeic/", views.toeic_list, name="toeic_list"),

    # CHOUKAI (Listening) — must be before <slug:slug> catch-all
    path("choukai/", views.choukai_book_list, name="choukai_book_list"),
    path("choukai/save-answer/", views.choukai_save_answer, name="choukai_save_answer"),
    path("choukai/<slug:slug>/", views.choukai_book_detail, name="choukai_book_detail"),

    # BOOKS — must be before <slug:slug> catch-all
    path("books/", views.book_list, name="book_list"),
    path("books/<slug:slug>/", views.book_detail, name="book_detail"),

    path("session/<int:session_id>/", views.take_exam, name="take_exam"),
    path("session/<int:session_id>/toeic/", views.take_exam, name="take_toeic_exam"),
    path("session/<int:session_id>/result/", views.exam_result, name="exam_result"),
    path("session/<int:session_id>/result/question/<int:question_id>/", views.exam_result_question_detail, name="exam_result_question_detail"),
    path("session/<int:session_id>/redo-wrong/", views.redo_wrong_questions, name="redo_wrong_questions"),

    # Slug catch-all — must be last
    path("<slug:slug>/", views.exam_detail, name="exam_detail"),
    path("<slug:slug>/start/", views.start_exam, name="start_exam"),
]
