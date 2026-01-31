# placement/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('api/test', views.PlacementTestViewSet, basename='placement-test')
router.register('api/path', views.LearningPathViewSet, basename='learning-path')
router.register('api/daily', views.DailyLessonViewSet, basename='daily-lesson')

app_name = 'placement'

urlpatterns = [
    # Template views
    path('', views.test_welcome, name='welcome'),
    path('test/', views.test_take, name='test_take'),
    path('test/<int:test_id>/result/', views.test_result, name='test_result'),
    path('goal/', views.goal_setting, name='goal_setting'),
    path('dashboard/', views.daily_dashboard, name='daily_dashboard'),
    path('path/', views.learning_path_view, name='learning_path'),
    
    # AJAX endpoints
    path('api/start-test/', views.api_start_test, name='api_start_test'),
    path('api/test/<int:test_id>/answer/', views.api_submit_answer, name='api_submit_answer'),
    path('api/generate-path/', views.api_generate_path, name='api_generate_path'),
    
    # REST API
    path('', include(router.urls)),
]
