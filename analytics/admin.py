from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta

from .models import PageView, DailyStats, PopularPage


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['path_short', 'user', 'ip_address', 'browser', 'device', 'os', 'timestamp']
    list_filter = ['browser', 'device', 'os', 'timestamp']
    search_fields = ['path', 'ip_address', 'user__username']
    date_hierarchy = 'timestamp'
    readonly_fields = ['path', 'user', 'ip_address', 'user_agent', 'referer', 'browser', 'device', 'os', 'timestamp']
    
    def path_short(self, obj):
        if len(obj.path) > 50:
            return obj.path[:50] + '...'
        return obj.path
    path_short.short_description = 'Path'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_views', 'unique_visitors', 'unique_users']
    date_hierarchy = 'date'
    readonly_fields = ['date', 'total_views', 'unique_visitors', 'unique_users']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PopularPage)
class PopularPageAdmin(admin.ModelAdmin):
    list_display = ['path_short', 'views', 'date']
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['date', 'path', 'views']
    
    def path_short(self, obj):
        if len(obj.path) > 60:
            return obj.path[:60] + '...'
        return obj.path
    path_short.short_description = 'Path'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Custom Admin Dashboard View
class AnalyticsDashboard:
    """Custom admin dashboard for analytics"""
    
    @staticmethod
    @staff_member_required
    def dashboard_view(request):
        today = timezone.localdate()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        # Today's stats
        today_views = PageView.objects.filter(timestamp__date=today).count()
        today_visitors = PageView.objects.filter(timestamp__date=today).values('ip_address').distinct().count()
        today_users = PageView.objects.filter(timestamp__date=today, user__isnull=False).values('user').distinct().count()
        
        # Last 7 days chart data
        last_7_days_data = (
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(views=Count('id'))
            .order_by('date')
        )
        
        chart_labels = []
        chart_data = []
        for item in last_7_days_data:
            chart_labels.append(item['date'].strftime('%d/%m'))
            chart_data.append(item['views'])
        
        # Top pages today
        top_pages_today = (
            PageView.objects
            .filter(timestamp__date=today)
            .values('path')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        
        # Top pages last 7 days
        top_pages_week = (
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('path')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        
        # Browser stats
        browser_stats = (
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('browser')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Device stats
        device_stats = (
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('device')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # OS stats
        os_stats = (
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('os')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Total stats
        total_views = PageView.objects.count()
        total_views_month = PageView.objects.filter(timestamp__date__gte=last_30_days).count()
        total_views_week = PageView.objects.filter(timestamp__date__gte=last_7_days).count()
        
        context = {
            'title': 'Thống kê truy cập',
            'today_views': today_views,
            'today_visitors': today_visitors,
            'today_users': today_users,
            'total_views': total_views,
            'total_views_month': total_views_month,
            'total_views_week': total_views_week,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'top_pages_today': top_pages_today,
            'top_pages_week': top_pages_week,
            'browser_stats': browser_stats,
            'device_stats': device_stats,
            'os_stats': os_stats,
        }
        
        return render(request, 'admin/analytics/dashboard.html', context)
