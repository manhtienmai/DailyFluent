"""
TC-10: User Profile & Settings Tests.

Covers:
  - UserProfile model: OneToOne, get_or_create_for_user, language preference
  - ExamGoal model: days_until_exam property, None/past date handling
  - UserStudySettings model: voice preference, daily limits
"""

from datetime import date, timedelta

from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()


# ===========================================================================
#  1. UserProfile model
# ===========================================================================
class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("profuser", "p@t.com", "pass1234")

    def test_create_profile(self):
        from core.models import UserProfile
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.study_language, "jp")  # default
        self.assertEqual(profile.bio, "")

    def test_one_to_one(self):
        from core.models import UserProfile
        UserProfile.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)

    def test_get_or_create_for_user(self):
        from core.models import UserProfile
        profile = UserProfile.get_or_create_for_user(self.user)
        self.assertEqual(profile.user, self.user)
        # Second call returns same
        profile2 = UserProfile.get_or_create_for_user(self.user)
        self.assertEqual(profile.pk, profile2.pk)

    def test_str(self):
        from core.models import UserProfile
        profile = UserProfile.objects.create(user=self.user)
        self.assertIn("profuser", str(profile))

    def test_language_choices(self):
        from core.models import UserProfile
        profile = UserProfile.objects.create(user=self.user, study_language="en")
        profile.refresh_from_db()
        self.assertEqual(profile.study_language, "en")

    def test_social_links_default(self):
        from core.models import UserProfile
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.social_links, {})

    def test_json_fields_default(self):
        from core.models import UserProfile
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.info_items, [])
        self.assertEqual(profile.skills, {})
        self.assertEqual(profile.certificates, [])
        self.assertEqual(profile.hobbies, [])


# ===========================================================================
#  2. ExamGoal model
# ===========================================================================
class ExamGoalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("goaluser", "g@t.com", "pass1234")

    def test_create_goal(self):
        from core.models import ExamGoal
        goal = ExamGoal.objects.create(user=self.user)
        self.assertEqual(goal.exam_type, "TOEIC")
        self.assertEqual(goal.target_score, 600)

    def test_days_until_exam_future(self):
        from core.models import ExamGoal
        future = date.today() + timedelta(days=30)
        goal = ExamGoal.objects.create(user=self.user, exam_date=future)
        self.assertEqual(goal.days_until_exam, 30)

    def test_days_until_exam_past(self):
        """Past dates should return 0 (not negative)."""
        from core.models import ExamGoal
        past = date.today() - timedelta(days=10)
        goal = ExamGoal.objects.create(user=self.user, exam_date=past)
        self.assertEqual(goal.days_until_exam, 0)

    def test_days_until_exam_today(self):
        from core.models import ExamGoal
        goal = ExamGoal.objects.create(user=self.user, exam_date=date.today())
        self.assertEqual(goal.days_until_exam, 0)

    def test_days_until_exam_none(self):
        from core.models import ExamGoal
        goal = ExamGoal.objects.create(user=self.user, exam_date=None)
        self.assertIsNone(goal.days_until_exam)

    def test_one_to_one(self):
        from core.models import ExamGoal
        ExamGoal.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            ExamGoal.objects.create(user=self.user)


# ===========================================================================
#  3. UserStudySettings
# ===========================================================================
class StudySettingsProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("settuser", "s@t.com", "pass1234")

    def test_voice_preference_default(self):
        from vocab.models import UserStudySettings
        settings = UserStudySettings.objects.create(user=self.user)
        self.assertEqual(settings.english_voice_preference, "us")

    def test_voice_preference_uk(self):
        from vocab.models import UserStudySettings
        settings = UserStudySettings.objects.create(
            user=self.user, english_voice_preference="uk"
        )
        settings.refresh_from_db()
        self.assertEqual(settings.english_voice_preference, "uk")

    def test_daily_limits_default(self):
        from vocab.models import UserStudySettings
        settings = UserStudySettings.objects.create(user=self.user)
        self.assertEqual(settings.new_cards_per_day, 20)
        self.assertEqual(settings.reviews_per_day, 200)

    def test_custom_limits(self):
        from vocab.models import UserStudySettings
        settings = UserStudySettings.objects.create(
            user=self.user, new_cards_per_day=50, reviews_per_day=500,
        )
        self.assertEqual(settings.new_cards_per_day, 50)
        self.assertEqual(settings.reviews_per_day, 500)
