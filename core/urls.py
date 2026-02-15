from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("courses/", views.course_list, name="course_list"),
    path("courses/<slug:course_slug>/", views.course_detail, name="course_detail"),
    path("courses/<slug:course_slug>/lessons/<slug:lesson_slug>/", views.lesson_detail, name="lesson_detail"),
    path("dictation/", views.dictation_list, name="dictation_list"),
    path("dictation/<slug:exercise_slug>/", views.dictation_detail, name="dictation_detail"),
    path("dictation/api/progress/", views.dictation_progress_update, name="dictation_progress_update"),
    path("profile/", views.profile, name="profile"),
    path("profile/<str:username>/", views.profile, name="profile_user"),
    path("settings/", views.settings, name="settings"),
    path("api/exam-goal/update/", views.update_exam_goal, name="update_exam_goal"),
    # Direct upload to Azure (SAS) for dictation audio
    path("api/dictation/upload-sas/", views.dictation_upload_sas, name="dictation_upload_sas"),
    path("api/dictation/complete-upload/", views.dictation_upload_complete, name="dictation_upload_complete"),
    
    # Language preference
    path("api/set-language/", views.set_language, name="set_language"),

    # Profile API endpoints
    path("api/profile/update/", views.profile_update, name="profile_update"),
    path("api/profile/upload-avatar/", views.profile_upload_avatar, name="profile_upload_avatar"),
    path("api/profile/upload-cover/", views.profile_upload_cover, name="profile_upload_cover"),
]
