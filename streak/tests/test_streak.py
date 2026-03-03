"""
TC-06: Streak & Badge System Tests.

Covers:
  - DailyActivity model: unique (user, date), accumulation
  - StreakStat model: OneToOne, streak counters
  - Services: register_login_streak, register_study_activity,
    register_flashcard_time, _update_streak_for_user, recalculate_streak_from_history
  - Badge model: ensure_badges_exist, badge check functions
  - UserBadge: unique (user, badge) constraint
  - API: /streak/status, /streak/heatmap, /streak/leaderboard
"""

import json
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()
API = "/api/v1/streak"


# ===========================================================================
#  1. DailyActivity model
# ===========================================================================
class DailyActivityModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("streakuser", "s@t.com", "pass1234")

    def test_create_activity(self):
        from streak.models import DailyActivity
        act = DailyActivity.objects.create(user=self.user, date=date.today())
        self.assertEqual(act.lessons_completed, 0)
        self.assertEqual(act.minutes_studied, 0)

    def test_unique_user_date(self):
        from streak.models import DailyActivity
        DailyActivity.objects.create(user=self.user, date=date.today())
        with self.assertRaises(IntegrityError):
            DailyActivity.objects.create(user=self.user, date=date.today())

    def test_different_dates_ok(self):
        from streak.models import DailyActivity
        DailyActivity.objects.create(user=self.user, date=date.today())
        act2 = DailyActivity.objects.create(user=self.user, date=date.today() - timedelta(days=1))
        self.assertIsNotNone(act2.id)


# ===========================================================================
#  2. StreakStat model
# ===========================================================================
class StreakStatModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("streak2", "s2@t.com", "pass1234")

    def test_create_defaults(self):
        from streak.models import StreakStat
        stat = StreakStat.objects.create(user=self.user)
        self.assertEqual(stat.current_streak, 0)
        self.assertEqual(stat.longest_streak, 0)
        self.assertIsNone(stat.last_active_date)

    def test_one_to_one(self):
        from streak.models import StreakStat
        StreakStat.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            StreakStat.objects.create(user=self.user)


# ===========================================================================
#  3. register_login_streak service
# ===========================================================================
class RegisterLoginStreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("login_streak", "ls@t.com", "pass1234")

    def test_first_login_starts_streak(self):
        from streak.services import register_login_streak
        streak = register_login_streak(self.user)
        self.assertEqual(streak.current_streak, 1)
        self.assertEqual(streak.longest_streak, 1)
        self.assertEqual(streak.last_active_date, timezone.localdate())

    def test_same_day_idempotent(self):
        from streak.services import register_login_streak
        register_login_streak(self.user)
        streak = register_login_streak(self.user)
        self.assertEqual(streak.current_streak, 1)  # Not 2

    def test_consecutive_days_increment(self):
        from streak.services import register_login_streak
        from streak.models import StreakStat

        streak = register_login_streak(self.user)
        # Simulate yesterday login
        yesterday = timezone.localdate() - timedelta(days=1)
        streak.last_active_date = yesterday
        streak.save()

        streak = register_login_streak(self.user)
        self.assertEqual(streak.current_streak, 2)

    def test_gap_resets_streak(self):
        from streak.services import register_login_streak
        from streak.models import StreakStat

        streak = register_login_streak(self.user)
        streak.current_streak = 5
        streak.longest_streak = 5
        streak.last_active_date = timezone.localdate() - timedelta(days=3)
        streak.save()

        streak = register_login_streak(self.user)
        self.assertEqual(streak.current_streak, 1)
        self.assertEqual(streak.longest_streak, 5)  # Preserved

    def test_skip_anonymous(self):
        from streak.services import register_login_streak
        from django.contrib.auth.models import AnonymousUser
        result = register_login_streak(AnonymousUser())
        self.assertIsNone(result)

    def test_skip_none(self):
        from streak.services import register_login_streak
        self.assertIsNone(register_login_streak(None))


# ===========================================================================
#  4. register_study_activity service
# ===========================================================================
class RegisterStudyActivityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("study", "study@t.com", "pass1234")

    def test_creates_activity(self):
        from streak.services import register_study_activity
        from streak.models import DailyActivity
        register_study_activity(self.user, lessons=1, minutes=10, points=20)
        act = DailyActivity.objects.get(user=self.user, date=timezone.localdate())
        self.assertEqual(act.lessons_completed, 1)
        self.assertEqual(act.minutes_studied, 10)
        self.assertEqual(act.points_earned, 20)

    def test_accumulates(self):
        from streak.services import register_study_activity
        from streak.models import DailyActivity
        register_study_activity(self.user, lessons=1, minutes=5)
        register_study_activity(self.user, lessons=2, minutes=10)
        act = DailyActivity.objects.get(user=self.user, date=timezone.localdate())
        self.assertEqual(act.lessons_completed, 3)
        self.assertEqual(act.minutes_studied, 15)

    def test_triggers_streak_update(self):
        from streak.services import register_study_activity
        from streak.models import StreakStat
        register_study_activity(self.user, lessons=1)
        streak = StreakStat.objects.get(user=self.user)
        self.assertEqual(streak.current_streak, 1)


# ===========================================================================
#  5. register_flashcard_time service
# ===========================================================================
class RegisterFlashcardTimeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("flash", "flash@t.com", "pass1234")

    def test_log_seconds(self):
        from streak.services import register_flashcard_time
        act = register_flashcard_time(self.user, seconds=300)
        self.assertEqual(act.seconds_studied, 300)
        self.assertEqual(act.minutes_studied, 5)

    def test_threshold_triggers_lesson(self):
        from streak.services import register_flashcard_time
        act = register_flashcard_time(self.user, seconds=600, threshold_minutes=10)
        self.assertEqual(act.lessons_completed, 1)

    def test_below_threshold_no_lesson(self):
        from streak.services import register_flashcard_time
        act = register_flashcard_time(self.user, seconds=300, threshold_minutes=10)
        self.assertEqual(act.lessons_completed, 0)

    def test_accumulates_across_calls(self):
        from streak.services import register_flashcard_time
        register_flashcard_time(self.user, seconds=300)
        act = register_flashcard_time(self.user, seconds=400)
        self.assertEqual(act.seconds_studied, 700)
        self.assertEqual(act.minutes_studied, 11)

    def test_zero_seconds_returns_none(self):
        from streak.services import register_flashcard_time
        result = register_flashcard_time(self.user, seconds=0)
        self.assertIsNone(result)


# ===========================================================================
#  6. recalculate_streak_from_history
# ===========================================================================
class RecalculateStreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("recalc", "recalc@t.com", "pass1234")

    def test_recalculate_consecutive(self):
        from streak.models import DailyActivity
        from streak.services import recalculate_streak_from_history
        today = date.today()
        for i in range(5):
            DailyActivity.objects.create(
                user=self.user, date=today - timedelta(days=4 - i),
                lessons_completed=1,
            )
        streak = recalculate_streak_from_history(self.user)
        self.assertEqual(streak.current_streak, 5)
        self.assertEqual(streak.longest_streak, 5)

    def test_recalculate_with_gap(self):
        from streak.models import DailyActivity
        from streak.services import recalculate_streak_from_history
        today = date.today()
        # 3 consecutive, gap, 2 consecutive
        for i in [7, 6, 5, 2, 1]:
            DailyActivity.objects.create(
                user=self.user, date=today - timedelta(days=i),
                lessons_completed=1,
            )
        streak = recalculate_streak_from_history(self.user)
        self.assertEqual(streak.longest_streak, 3)
        self.assertEqual(streak.current_streak, 2)

    def test_empty_history(self):
        from streak.services import recalculate_streak_from_history
        streak = recalculate_streak_from_history(self.user)
        self.assertEqual(streak.current_streak, 0)


# ===========================================================================
#  7. Badge & UserBadge models
# ===========================================================================
class BadgeModelTests(TestCase):
    def test_ensure_badges_exist(self):
        from core.badge_service import ensure_badges_exist, BADGE_DEFINITIONS
        from core.models import Badge
        ensure_badges_exist()
        self.assertEqual(Badge.objects.count(), len(BADGE_DEFINITIONS))

    def test_badge_unique_code(self):
        from core.models import Badge
        Badge.objects.create(code="first_step", name="Test", description="", icon="👣")
        with self.assertRaises(IntegrityError):
            Badge.objects.create(code="first_step", name="Dup", description="", icon="👣")

    def test_user_badge_unique(self):
        from core.models import Badge, UserBadge
        user = User.objects.create_user("badgeuser", "b@t.com", "pass1234")
        badge = Badge.objects.create(code="week_warrior", name="WW", description="", icon="🔥")
        UserBadge.objects.create(user=user, badge=badge)
        with self.assertRaises(IntegrityError):
            UserBadge.objects.create(user=user, badge=badge)


# ===========================================================================
#  8. Badge check functions
# ===========================================================================
class BadgeCheckFunctionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("checker", "c@t.com", "pass1234")

    def test_check_week_warrior_false(self):
        from core.badge_service import check_week_warrior
        self.assertFalse(check_week_warrior(self.user))

    def test_check_week_warrior_true(self):
        from core.badge_service import check_week_warrior
        from streak.models import StreakStat
        StreakStat.objects.create(user=self.user, current_streak=7, longest_streak=7)
        self.assertTrue(check_week_warrior(self.user))

    def test_check_streak_30(self):
        from core.badge_service import check_streak_30
        from streak.models import StreakStat
        StreakStat.objects.create(user=self.user, current_streak=30, longest_streak=30)
        self.assertTrue(check_streak_30(self.user))

    def test_check_century_false(self):
        from core.badge_service import check_century
        self.assertFalse(check_century(self.user))


# ===========================================================================
#  9. Streak API endpoints
# ===========================================================================
class StreakAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("apistreak", "api@t.com", "pass1234")
        self.client.force_login(self.user)

    def test_streak_status(self):
        resp = self.client.get(f"{API}/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("current_streak", data)
        self.assertIn("minutes_today", data)
        self.assertIn("goal_completed", data)

    def test_streak_status_after_login(self):
        """StreakMiddleware runs register_login_streak on every request,
        so first API call already sets current_streak=1."""
        resp = self.client.get(f"{API}/status")
        data = resp.json()
        self.assertEqual(data["current_streak"], 1)
        self.assertEqual(data["minutes_today"], 0)
        self.assertFalse(data["goal_completed"])

    def test_heatmap(self):
        resp = self.client.get(f"{API}/heatmap")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("days", data)
        self.assertIn("start", data)
        self.assertIn("end", data)

    def test_leaderboard(self):
        from streak.models import StreakStat
        StreakStat.objects.create(user=self.user, current_streak=10, longest_streak=15)
        resp = self.client.get(f"{API}/leaderboard")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data) >= 1)
        self.assertIn("rank", data[0])
        self.assertIn("current_streak", data[0])

    def test_unauthenticated(self):
        from django.test import Client
        client = Client()
        resp = client.get(f"{API}/status")
        self.assertIn(resp.status_code, [401, 403])
