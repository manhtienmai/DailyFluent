from django.urls import path
from . import views

app_name = "exam"

urlpatterns = [
    path("", views.exam_list, name="exam_list"),
    path("<slug:slug>/start/", views.start_exam, name="start_exam"),
    path("session/<int:session_id>/", views.take_exam, name="take_exam"),
    path("session/<int:session_id>/result/", views.exam_result, name="exam_result"),

    # BOOKS
    path("books/", views.book_list, name="book_list"),
    path("books/<slug:slug>/", views.book_detail, name="book_detail"),

]
