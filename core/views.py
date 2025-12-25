# core/views.py
from django.shortcuts import render
from django.utils import timezone
from streak.models import StreakStat, DailyActivity
from vocab.models import UserStudySettings


def home(request):
    """
    Dashboard chính.
    - Nếu user đăng nhập: hiện dashboard với streak.
    - Nếu chưa đăng nhập: gợi ý đăng nhập / đăng ký.
    """
    streak = None
    minutes_today = 0
    cards_today = 0
    new_cards_today = 0
    reviews_today = 0
    if request.user.is_authenticated:
        streak, _ = StreakStat.objects.get_or_create(user=request.user)
        today = timezone.localdate()
        act = DailyActivity.objects.filter(user=request.user, date=today).first()
        if act:
            minutes_today = act.minutes_studied
        study_settings, _ = UserStudySettings.objects.get_or_create(user=request.user)
        study_settings.reset_daily_counts_if_needed()
        new_cards_today = study_settings.new_cards_today
        reviews_today = study_settings.reviews_today
        cards_today = new_cards_today + reviews_today

    context = {
        "streak": streak,
        "minutes_today": minutes_today,
        "cards_today": cards_today,
        "new_cards_today": new_cards_today,
        "reviews_today": reviews_today,
    }
    return render(request, "home.html", context)
