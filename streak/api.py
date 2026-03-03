"""
Streak API router.

Endpoints:
  GET  /api/v1/streak/status       – Current streak + today's study stats
  POST /api/v1/streak/log-minutes  – Log study time (seconds or minutes)
  GET  /api/v1/streak/heatmap      – 60-day activity heatmap
"""

import datetime
from typing import List, Optional

from ninja import Router, Schema
from ninja.errors import HttpError
from django.utils import timezone

from .models import DailyActivity, StreakStat
from .services import get_today_for_user, register_flashcard_minutes, register_flashcard_time
from vocab.models import UserStudySettings

router = Router()


# ── Schemas ────────────────────────────────────────────────

class StreakStatusOut(Schema):
    today: datetime.date
    current_streak: int
    longest_streak: int
    last_active_date: Optional[datetime.date] = None
    minutes_today: int
    seconds_today: int
    goal_minutes: int
    goal_completed: bool
    cards_today: int
    new_cards_today: int
    reviews_today: int


class LogTimeIn(Schema):
    seconds: int = 0
    minutes: int = 0


class LogTimeOut(Schema):
    ok: bool
    minutes_today: int
    seconds_today: int
    goal_minutes: int
    goal_completed: bool
    cards_today: int
    new_cards_today: int
    reviews_today: int
    current_streak: int
    longest_streak: int
    last_active_date: Optional[datetime.date] = None
    today: datetime.date


class HeatmapDayOut(Schema):
    date: datetime.date
    minutes: int
    lessons: int


class HeatmapOut(Schema):
    days: List[HeatmapDayOut]
    start: datetime.date
    end: datetime.date


# ── Helpers ────────────────────────────────────────────────

def _card_stats(user) -> tuple[int, int]:
    """Return (new_cards_today, reviews_today) for the user."""
    settings, _ = UserStudySettings.objects.get_or_create(user=user)
    settings.reset_daily_counts_if_needed()
    return settings.new_cards_today, settings.reviews_today


# ── Endpoints ──────────────────────────────────────────────

@router.get("/status", response=StreakStatusOut)
def streak_status(request):
    """Return the user's current streak and today's study statistics."""
    streak, _ = StreakStat.objects.get_or_create(user=request.user)
    today = get_today_for_user(request.user)
    act = DailyActivity.objects.filter(user=request.user, date=today).first()
    new_cards, reviews = _card_stats(request.user)

    minutes = act.minutes_studied if act else 0
    seconds = act.seconds_studied if act else 0
    goal = 10

    return StreakStatusOut(
        today=today,
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_active_date=streak.last_active_date,
        minutes_today=minutes,
        seconds_today=seconds,
        goal_minutes=goal,
        goal_completed=minutes >= goal,
        cards_today=new_cards + reviews,
        new_cards_today=new_cards,
        reviews_today=reviews,
    )


@router.post("/log-minutes", response=LogTimeOut)
def log_minutes(request, payload: LogTimeIn):
    """
    Log study time for the current user.
    Supply either `seconds` (preferred) or `minutes`.
    """
    if payload.seconds <= 0 and payload.minutes <= 0:
        raise HttpError(400, "seconds or minutes must be > 0")

    if payload.seconds > 0:
        activity = register_flashcard_time(
            request.user, seconds=payload.seconds, threshold_minutes=10
        )
    else:
        activity = register_flashcard_minutes(
            request.user, minutes=payload.minutes, threshold_minutes=10
        )

    streak, _ = StreakStat.objects.get_or_create(user=request.user)
    today = get_today_for_user(request.user)
    new_cards, reviews = _card_stats(request.user)

    minutes = activity.minutes_studied if activity else 0
    seconds = activity.seconds_studied if activity else 0
    goal = 10

    return LogTimeOut(
        ok=True,
        minutes_today=minutes,
        seconds_today=seconds,
        goal_minutes=goal,
        goal_completed=minutes >= goal,
        cards_today=new_cards + reviews,
        new_cards_today=new_cards,
        reviews_today=reviews,
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_active_date=streak.last_active_date,
        today=today,
    )


@router.get("/heatmap", response=HeatmapOut)
def heatmap(request):
    """Return 60 days of daily activity data for the heatmap calendar."""
    today = get_today_for_user(request.user)
    start = today - datetime.timedelta(days=59)

    activities = DailyActivity.objects.filter(
        user=request.user,
        date__gte=start,
        date__lte=today,
    ).order_by("date")

    return HeatmapOut(
        days=[
            HeatmapDayOut(
                date=act.date,
                minutes=act.minutes_studied,
                lessons=act.lessons_completed,
            )
            for act in activities
        ],
        start=start,
        end=today,
    )


@router.get("/leaderboard")
def leaderboard(request):
    """Return top streakers for the leaderboard."""
    top = StreakStat.objects.select_related("user").order_by(
        "-current_streak", "-longest_streak"
    )[:20]
    return [
        {
            "rank": i + 1,
            "username": s.user.username,
            "current_streak": s.current_streak,
            "longest_streak": s.longest_streak,
        }
        for i, s in enumerate(top)
    ]
