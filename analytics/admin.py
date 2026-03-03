from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Min
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta

from .models import PageView, DailyStats, PopularPage

User = get_user_model()


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
        yesterday = today - timedelta(days=1)
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        # ========================================
        # Page View Stats
        # ========================================
        today_views = PageView.objects.filter(timestamp__date=today).count()
        today_visitors = PageView.objects.filter(timestamp__date=today).values('ip_address').distinct().count()
        today_users = PageView.objects.filter(timestamp__date=today, user__isnull=False).values('user').distinct().count()
        
        # Total views
        total_views = PageView.objects.count()
        total_views_month = PageView.objects.filter(timestamp__date__gte=last_30_days).count()
        total_views_week = PageView.objects.filter(timestamp__date__gte=last_7_days).count()
        
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
        
        # ========================================
        # User Registration Stats
        # ========================================
        total_users = User.objects.count()
        users_today = User.objects.filter(date_joined__date=today).count()
        users_yesterday = User.objects.filter(date_joined__date=yesterday).count()
        users_week = User.objects.filter(date_joined__date__gte=last_7_days).count()
        users_month = User.objects.filter(date_joined__date__gte=last_30_days).count()
        
        # Calculate user growth
        user_growth = users_today - users_yesterday
        user_growth_str = f"+{user_growth}" if user_growth > 0 else str(user_growth) if user_growth < 0 else "0"
        
        # User registration chart (last 7 days)
        user_reg_data = (
            User.objects
            .filter(date_joined__date__gte=last_7_days)
            .annotate(date=TruncDate('date_joined'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        user_chart_labels = []
        user_chart_data = []
        for item in user_reg_data:
            user_chart_labels.append(item['date'].strftime('%d/%m'))
            user_chart_data.append(item['count'])
        
        # Recent registered users
        recent_users = User.objects.order_by('-date_joined')[:10]
        
        # ========================================
        # Top Pages
        # ========================================
        top_pages_today = (
            PageView.objects
            .filter(timestamp__date=today)
            .values('path')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        
        top_pages_week = (
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('path')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        
        # ========================================
        # Hourly Views Today
        # ========================================
        hourly_data = (
            PageView.objects
            .filter(timestamp__date=today)
            .annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(views=Count('id'), visitors=Count('ip_address', distinct=True))
            .order_by('hour')
        )

        hourly_labels = []
        hourly_views_data = []
        hourly_visitors_data = []
        for item in hourly_data:
            local_hour = timezone.localtime(item['hour'])
            hourly_labels.append(local_hour.strftime('%H:00'))
            hourly_views_data.append(item['views'])
            hourly_visitors_data.append(item['visitors'])

        # Peak hour today
        peak_hour = None
        if hourly_data:
            peak = max(hourly_data, key=lambda x: x['views'])
            local_peak = timezone.localtime(peak['hour'])
            peak_hour = local_peak.strftime('%H:00')

        # Active now (views in last 30 minutes)
        active_now = PageView.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        ).values('ip_address').distinct().count()

        # ========================================
        # Browser / Device / OS Stats
        # ========================================
        browser_qs = list(
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('browser')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]
        )
        total_browser = sum(s['count'] for s in browser_qs) or 1
        browser_stats = [
            {**s, 'pct': round(s['count'] / total_browser * 100)}
            for s in browser_qs
        ]

        device_qs = list(
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('device')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        total_device = sum(s['count'] for s in device_qs) or 1
        device_stats = [
            {**s, 'pct': round(s['count'] / total_device * 100)}
            for s in device_qs
        ]

        os_qs = list(
            PageView.objects
            .filter(timestamp__date__gte=last_7_days)
            .values('os')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]
        )
        total_os = sum(s['count'] for s in os_qs) or 1
        os_stats = [
            {**s, 'pct': round(s['count'] / total_os * 100)}
            for s in os_qs
        ]
        
        # ========================================
        # Additional Stats (from other models)
        # ========================================
        additional_stats = {}
        
        # Try to get exam stats
        try:
            from exam.models import ExamTemplate, ExamAttempt
            additional_stats['total_exams'] = ExamTemplate.objects.count()
            additional_stats['total_attempts'] = ExamAttempt.objects.count()
            additional_stats['attempts_today'] = ExamAttempt.objects.filter(created_at__date=today).count()
            additional_stats['attempts_week'] = ExamAttempt.objects.filter(created_at__date__gte=last_7_days).count()
        except:
            pass
        
        # Try to get vocab stats
        try:
            from vocab.models import Vocabulary, VocabularySet, SetItem
            additional_stats['total_vocab'] = Vocabulary.objects.count()
            additional_stats['total_vocab_sets'] = VocabularySet.objects.count()
            additional_stats['total_set_items'] = SetItem.objects.count()
            
            # Vocab added recently
            additional_stats['vocab_today'] = Vocabulary.objects.filter(created_at__date=today).count()
            additional_stats['vocab_week'] = Vocabulary.objects.filter(created_at__date__gte=last_7_days).count()
        except Exception:
            pass
        
        # Try to get feedback stats
        try:
            from feedback.models import Feedback
            additional_stats['total_feedback'] = Feedback.objects.count()
            additional_stats['feedback_pending'] = Feedback.objects.filter(status='pending').count()
        except:
            pass
        
        context = {
            'title': 'Thống kê tổng hợp',
            # Page view stats
            'today_views': today_views,
            'today_visitors': today_visitors,
            'today_users': today_users,
            'total_views': total_views,
            'total_views_month': total_views_month,
            'total_views_week': total_views_week,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            # Hourly data
            'hourly_labels': hourly_labels,
            'hourly_views_data': hourly_views_data,
            'hourly_visitors_data': hourly_visitors_data,
            'peak_hour': peak_hour,
            'active_now': active_now,
            # User stats
            'total_users': total_users,
            'users_today': users_today,
            'users_yesterday': users_yesterday,
            'users_week': users_week,
            'users_month': users_month,
            'user_growth_str': user_growth_str,
            'user_growth': user_growth,
            'user_chart_labels': user_chart_labels,
            'user_chart_data': user_chart_data,
            'recent_users': recent_users,
            # Page stats
            'top_pages_today': top_pages_today,
            'top_pages_week': top_pages_week,
            # Tech stats
            'browser_stats': browser_stats,
            'device_stats': device_stats,
            'os_stats': os_stats,
            # Additional
            **additional_stats,
        }
        
        return render(request, 'admin/analytics/dashboard.html', context)
