from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("courses/", views.course_list, name="course_list"),
    path("courses/<slug:course_slug>/", views.course_detail, name="course_detail"),
    path("courses/<slug:course_slug>/lessons/<slug:lesson_slug>/", views.lesson_detail, name="lesson_detail"),
]


