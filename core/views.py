# core/views.py
from django.shortcuts import render
from streak.models import StreakStat


def home(request):
    """
    Dashboard chính.
    - Nếu user đăng nhập: hiện dashboard với streak.
    - Nếu chưa đăng nhập: gợi ý đăng nhập / đăng ký.
    """
    streak = None
    if request.user.is_authenticated:
        streak, _ = StreakStat.objects.get_or_create(user=request.user)

    context = {
        "streak": streak,
    }
    return render(request, "home.html", context)
