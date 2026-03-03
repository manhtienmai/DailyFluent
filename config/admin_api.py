"""
Admin API endpoints for the Next.js admin dashboard.

Provides data for the dashboard, analytics, and CRUD operations.
Requires staff/superuser authentication.
"""

from ninja import Router, Schema
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from datetime import timedelta
from typing import Optional

User = get_user_model()

router = Router()


# ── Schemas ────────────────────────────────────────────────

class PageStat(Schema):
    path: str
    views: int


class RecentUser(Schema):
    username: str
    email: str
    date_joined: str


class DashboardStats(Schema):
    today_visitors: int = 0
    today_views: int = 0
    users_today: int = 0
    total_users: int = 0
    active_now: int = 0
    peak_hour: str = ""
    user_growth: int = 0
    users_month: int = 0
    users_week: int = 0
    users_yesterday: int = 0
    today_users: int = 0
    total_views: int = 0
    total_views_week: int = 0
    total_views_month: int = 0
    hourly_labels: list[str] = []
    hourly_data: list[int] = []
    user_labels: list[str] = []
    user_data: list[int] = []
    views_labels: list[str] = []
    views_data: list[int] = []
    recent_users: list[RecentUser] = []
    top_pages_today: list[PageStat] = []
    top_pages_week: list[PageStat] = []
    total_vocab: Optional[int] = None
    total_vocab_sets: Optional[int] = None
    total_exams: Optional[int] = None
    total_feedback: Optional[int] = None
    vocab_today: Optional[int] = None
    gemini_tokens_today: int = 0
    gemini_tokens_month: int = 0
    gemini_calls_today: int = 0
    gemini_calls_month: int = 0
    gemini_input_today: int = 0
    gemini_input_month: int = 0
    gemini_output_today: int = 0
    gemini_output_month: int = 0
    gemini_by_model: list = []


# ── Dashboard Endpoint ─────────────────────────────────────

@router.get("/dashboard/stats/", response=DashboardStats)
def dashboard_stats(request):
    """Return all dashboard statistics for the admin panel."""
    if not request.user.is_staff:
        return DashboardStats()

    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = today_start - timedelta(days=7)
    month_ago = today_start - timedelta(days=30)

    # ── User stats ──
    total_users = User.objects.count()
    users_today = User.objects.filter(date_joined__gte=today_start).count()
    users_yesterday = User.objects.filter(
        date_joined__gte=yesterday_start,
        date_joined__lt=today_start
    ).count()
    users_week = User.objects.filter(date_joined__gte=week_ago).count()
    users_month = User.objects.filter(date_joined__gte=month_ago).count()
    user_growth = users_today - users_yesterday

    # ── Recent users ──
    recent = User.objects.order_by('-date_joined')[:10]
    recent_users = [
        RecentUser(
            username=u.username,
            email=u.email,
            date_joined=u.date_joined.isoformat()
        )
        for u in recent
    ]

    # ── User registration chart (7 days) ──
    user_labels = []
    user_data = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        label = day.strftime("%d/%m")
        count = User.objects.filter(date_joined__gte=day, date_joined__lt=next_day).count()
        user_labels.append(label)
        user_data.append(count)

    # ── Analytics (try to import, gracefully degrade) ──
    today_visitors = 0
    today_views = 0
    total_views = 0
    total_views_week = 0
    total_views_month = 0
    today_users_count = 0
    active_now = 0
    peak_hour = ""
    hourly_labels = []
    hourly_data = []
    views_labels = []
    views_data = []
    top_pages_today = []
    top_pages_week = []

    try:
        from analytics.models import PageView, DailyStats

        # Today's views
        today_views_qs = PageView.objects.filter(timestamp__gte=today_start)
        today_views = today_views_qs.count()
        today_visitors = today_views_qs.values('ip_address').distinct().count()
        today_users_count = today_views_qs.filter(user__isnull=False).values('user').distinct().count()

        # Active now (last 5 minutes)
        five_min_ago = now - timedelta(minutes=5)
        active_now = PageView.objects.filter(timestamp__gte=five_min_ago).values('ip_address').distinct().count()

        # Total views
        total_views = PageView.objects.count()
        total_views_week = PageView.objects.filter(timestamp__gte=week_ago).count()
        total_views_month = PageView.objects.filter(timestamp__gte=month_ago).count()

        # Hourly chart
        hourly_qs = (
            today_views_qs
            .annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        peak_count = 0
        for entry in hourly_qs:
            h = timezone.localtime(entry['hour']).strftime("%H:00")
            hourly_labels.append(h)
            hourly_data.append(entry['count'])
            if entry['count'] > peak_count:
                peak_count = entry['count']
                peak_hour = h

        # Views chart (7 days)
        for i in range(6, -1, -1):
            day = today_start - timedelta(days=i)
            next_day = day + timedelta(days=1)
            views_labels.append(day.strftime("%d/%m"))
            views_data.append(
                PageView.objects.filter(timestamp__gte=day, timestamp__lt=next_day).count()
            )

        # Top pages today
        top_today_qs = (
            today_views_qs
            .values('path')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        top_pages_today = [PageStat(path=p['path'], views=p['views']) for p in top_today_qs]

        # Top pages this week
        top_week_qs = (
            PageView.objects.filter(timestamp__gte=week_ago)
            .values('path')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        top_pages_week = [PageStat(path=p['path'], views=p['views']) for p in top_week_qs]

    except Exception:
        pass

    # ── Content stats ──
    total_vocab = None
    total_vocab_sets = None
    total_exams = None
    total_feedback = None
    vocab_today_count = None

    try:
        from vocab.models import Vocabulary, VocabularySet
        total_vocab = Vocabulary.objects.count()
        total_vocab_sets = VocabularySet.objects.count()
        vocab_today_count = Vocabulary.objects.filter(created_at__gte=today_start).count() if hasattr(Vocabulary, 'created_at') else None
    except Exception:
        pass

    try:
        from exam.models import ExamTemplate
        total_exams = ExamTemplate.objects.count()
    except Exception:
        pass

    try:
        from feedback.models import FeedbackItem
        total_feedback = FeedbackItem.objects.count()
    except Exception:
        pass

    # ── Gemini token usage ──
    gemini_tokens_today = 0
    gemini_tokens_month = 0
    gemini_calls_today = 0
    gemini_calls_month = 0
    gemini_input_today = 0
    gemini_input_month = 0
    gemini_output_today = 0
    gemini_output_month = 0
    gemini_by_model = []
    try:
        from analytics.models import GeminiTokenUsage
        from django.db.models import Sum, Count
        today_usage = GeminiTokenUsage.objects.filter(timestamp__gte=today_start)
        month_usage = GeminiTokenUsage.objects.filter(timestamp__gte=month_ago)
        gemini_calls_today = today_usage.count()
        gemini_calls_month = month_usage.count()
        today_agg = today_usage.aggregate(
            total=Sum('total_tokens'), inp=Sum('prompt_tokens'), out=Sum('completion_tokens')
        )
        month_agg = month_usage.aggregate(
            total=Sum('total_tokens'), inp=Sum('prompt_tokens'), out=Sum('completion_tokens')
        )
        gemini_tokens_today = today_agg['total'] or 0
        gemini_tokens_month = month_agg['total'] or 0
        gemini_input_today = today_agg['inp'] or 0
        gemini_input_month = month_agg['inp'] or 0
        gemini_output_today = today_agg['out'] or 0
        gemini_output_month = month_agg['out'] or 0
        # Per-model breakdown (all time)
        by_model = GeminiTokenUsage.objects.values('model_name').annotate(
            calls=Count('id'),
            input_tokens=Sum('prompt_tokens'),
            output_tokens=Sum('completion_tokens'),
            total_tokens=Sum('total_tokens'),
        ).order_by('-total_tokens')
        gemini_by_model = [
            {
                'model': m['model_name'],
                'calls': m['calls'],
                'input': m['input_tokens'] or 0,
                'output': m['output_tokens'] or 0,
                'total': m['total_tokens'] or 0,
            }
            for m in by_model
        ]
    except Exception:
        pass

    return DashboardStats(
        today_visitors=today_visitors,
        today_views=today_views,
        users_today=users_today,
        total_users=total_users,
        active_now=active_now,
        peak_hour=peak_hour,
        user_growth=user_growth,
        users_month=users_month,
        users_week=users_week,
        users_yesterday=users_yesterday,
        today_users=today_users_count,
        total_views=total_views,
        total_views_week=total_views_week,
        total_views_month=total_views_month,
        hourly_labels=hourly_labels,
        hourly_data=hourly_data,
        user_labels=user_labels,
        user_data=user_data,
        views_labels=views_labels,
        views_data=views_data,
        recent_users=recent_users,
        top_pages_today=top_pages_today,
        top_pages_week=top_pages_week,
        total_vocab=total_vocab,
        total_vocab_sets=total_vocab_sets,
        total_exams=total_exams,
        total_feedback=total_feedback,
        vocab_today=vocab_today_count,
        gemini_tokens_today=gemini_tokens_today,
        gemini_tokens_month=gemini_tokens_month,
        gemini_calls_today=gemini_calls_today,
        gemini_calls_month=gemini_calls_month,
        gemini_input_today=gemini_input_today,
        gemini_input_month=gemini_input_month,
        gemini_output_today=gemini_output_today,
        gemini_output_month=gemini_output_month,
        gemini_by_model=gemini_by_model,
    )
