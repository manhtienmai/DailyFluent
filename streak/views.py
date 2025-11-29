# streak/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import StreakStat
from .services import get_today_for_user


@login_required
def overview(request):
    """
    Trang đơn giản hiển thị card streak.
    Bạn có thể include template _streak_card.html vào dashboard chính của app học tập.
    """
    streak, _ = StreakStat.objects.get_or_create(user=request.user)
    context = {
        "streak": streak,
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

    data = {
        "today": today.isoformat(),
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "last_active_date": streak.last_active_date.isoformat() if streak.last_active_date else None,
    }
    return JsonResponse(data)
