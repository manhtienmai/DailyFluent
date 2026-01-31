# streak/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import StreakStat, DailyActivity
from .services import get_today_for_user, register_flashcard_minutes, register_flashcard_time
from vocab.models import UserStudySettings


@login_required
def overview(request):
    """
    Trang hiển thị bảng xếp hạng (Leaderboard) tính từ thứ 2 đầu tuần.
    Xếp hạng dựa trên số ngày hoạt động (streak) trong tuần này.
    Nếu bằng nhau thì so sánh số phút học.
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Sum
    import datetime
    
    User = get_user_model()
    streak, _ = StreakStat.objects.get_or_create(user=request.user)
    
    # Tính thứ 2 đầu tuần
    today = timezone.localdate()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    
    # Query leaderboard
    leaderboard = User.objects.filter(
        dailyactivity__date__gte=start_of_week
    ).annotate(
        weekly_days=Count('dailyactivity__date', distinct=True),
        weekly_minutes=Sum('dailyactivity__minutes_studied')
    ).order_by('-weekly_days', '-weekly_minutes')[:50]

    context = {
        "streak": streak,
        "leaderboard": leaderboard,
        "start_of_week": start_of_week,
        "today": today,
    }
    return render(request, "streak/overview.html", context)


@login_required
def streak_status_api(request):
    """
    API trả về JSON status streak hiện tại.
    Nếu bạn có frontend JS muốn fetch định kỳ thì dùng endpoint này.
    """
    streak, _ = StreakStat.objects.get_or_create(user=request.user)
    today = get_today_for_user(request.user)

    act = DailyActivity.objects.filter(user=request.user, date=today).first()
    minutes_value = act.minutes_studied if act else 0
    seconds_value = act.seconds_studied if act else 0
    goal_minutes = 10
    study_settings, _ = UserStudySettings.objects.get_or_create(user=request.user)
    study_settings.reset_daily_counts_if_needed()
    new_cards_today = study_settings.new_cards_today
    reviews_today = study_settings.reviews_today

    data = {
        "today": today.isoformat(),
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "last_active_date": streak.last_active_date.isoformat() if streak.last_active_date else None,
        "minutes_today": minutes_value,
        "seconds_today": seconds_value,
        "goal_minutes": goal_minutes,
        "goal_completed": minutes_value >= goal_minutes,
        "cards_today": new_cards_today + reviews_today,
        "new_cards_today": new_cards_today,
        "reviews_today": reviews_today,
    }
    return JsonResponse(data)


@login_required
@require_POST
def log_flashcard_minutes(request):
    # Accept either seconds (preferred) or minutes (legacy)
    try:
        seconds = int(request.POST.get("seconds", 0))
    except (TypeError, ValueError):
        seconds = 0
    try:
        minutes = int(request.POST.get("minutes", 0))
    except (TypeError, ValueError):
        minutes = 0

    if seconds <= 0 and minutes <= 0:
        return HttpResponseBadRequest("Seconds/minutes must be > 0")

    if seconds > 0:
        activity = register_flashcard_time(request.user, seconds=seconds, threshold_minutes=10)
    else:
        activity = register_flashcard_minutes(request.user, minutes=minutes, threshold_minutes=10)
    streak, _ = StreakStat.objects.get_or_create(user=request.user)
    today = get_today_for_user(request.user)

    minutes_today = activity.minutes_studied if activity else 0
    seconds_today = activity.seconds_studied if activity else 0
    goal_minutes = 10
    study_settings, _ = UserStudySettings.objects.get_or_create(user=request.user)
    study_settings.reset_daily_counts_if_needed()
    new_cards_today = study_settings.new_cards_today
    reviews_today = study_settings.reviews_today

    return JsonResponse({
        "ok": True,
        "minutes_today": minutes_today,
        "seconds_today": seconds_today,
        "goal_minutes": goal_minutes,
        "goal_completed": minutes_today >= goal_minutes,
        "cards_today": new_cards_today + reviews_today,
        "new_cards_today": new_cards_today,
        "reviews_today": reviews_today,
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "last_active_date": streak.last_active_date.isoformat() if streak.last_active_date else None,
        "today": today.isoformat(),
    })


@login_required
def heatmap_api(request):
    """
    Trả về dữ liệu heatmap (60 ngày gần nhất) gồm minutes_studied và lessons_completed.
    """
    today = get_today_for_user(request.user)
    start = today - timezone.timedelta(days=59)

    qs = DailyActivity.objects.filter(user=request.user, date__gte=start, date__lte=today)
    data = [
        {
            "date": act.date.isoformat(),
            "minutes": act.minutes_studied,
            "lessons": act.lessons_completed,
        }
        for act in qs.order_by("date")
    ]
    return JsonResponse({"days": data, "start": start.isoformat(), "end": today.isoformat()})
