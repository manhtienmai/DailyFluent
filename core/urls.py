from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("courses/", views.course_list, name="course_list"),
    path("courses/<slug:course_slug>/", views.course_detail, name="course_detail"),
    path("courses/<slug:course_slug>/lessons/<slug:lesson_slug>/", views.lesson_detail, name="lesson_detail"),
    path("dictation/", views.dictation_list, name="dictation_list"),
    path("dictation/<slug:exercise_slug>/", views.dictation_detail, name="dictation_detail"),
    path("profile/", views.profile, name="profile"),
    path("profile/<str:username>/", views.profile, name="profile_user"),
    path("settings/", views.settings, name="settings"),
]
