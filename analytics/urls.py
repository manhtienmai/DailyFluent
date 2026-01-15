from django.urls import path
from .admin import AnalyticsDashboard

app_name = 'analytics'

urlpatterns = [
    path('admin/analytics/dashboard/', AnalyticsDashboard.dashboard_view, name='dashboard'),
]
