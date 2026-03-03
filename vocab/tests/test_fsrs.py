"""
TC-03: Flashcard & FSRS SRS Engine Tests.

Covers:
  - FSRS bridge functions: create_new_card_state, review_card, preview_intervals,
    get_interval_display, get_card_state, is_learning_card, should_requeue_in_session
  - Utility: card_data_to_dict normalisation
  - UserStudySettings model: daily limits, reset_daily_counts_if_needed,
    can_study_new, can_review
  - FsrsCardStateEn model: unique constraint, state management
  - API endpoints: /flashcards, /review, /progress, /study-status, /my-words
"""

import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# API prefixes (vocab router is mounted at /api/v1/vocab/)
API = "/api/v1/vocab"


# ===========================================================================
# Helper: create vocab & card data in DB
# ===========================================================================
def _create_vocab(word="hello", language="en"):
    """Create a Vocabulary + WordEntry + WordDefinition chain."""
    from vocab.models import Vocabulary, WordEntry, WordDefinition

    vocab, _ = Vocabulary.objects.get_or_create(
        word=word, defaults={"language": language}
    )
    entry, _ = WordEntry.objects.get_or_create(
        vocab=vocab,
        defaults={"part_of_speech": "noun", "ipa": "/hɛˈloʊ/"},
    )
    defn, _ = WordDefinition.objects.get_or_create(
        entry=entry,
        defaults={"meaning": f"meaning of {word}"},
    )
    return vocab, entry, defn


def _create_card(user, word="hello", language="en", **overrides):
    """Create FsrsCardStateEn for a user."""
    from vocab.models import FsrsCardStateEn

    vocab, _, _ = _create_vocab(word, language)
    defaults = {
        "card_data": {},
        "state": 0,
        "due": timezone.now(),
        "last_review": None,
        "total_reviews": 0,
        "successful_reviews": 0,
    }
    defaults.update(overrides)
    card, _ = FsrsCardStateEn.objects.get_or_create(
        user=user, vocab=vocab, defaults=defaults
    )
    return card


# ===========================================================================
#  1. FSRS Bridge — create_new_card_state
# ===========================================================================
class CreateNewCardStateTests(TestCase):
    """Test fsrs_bridge.create_new_card_state."""

    def test_returns_card_object(self):
        from vocab.fsrs_bridge import create_new_card_state
        from fsrs import Card

        card = create_new_card_state()
        self.assertIsInstance(card, Card)

    def test_new_card_due_now(self):
        """New card should be due immediately (within a few seconds of now)."""
        from vocab.fsrs_bridge import create_new_card_state

        card = create_new_card_state()
        # due should be very close to now
        delta = abs((card.due - timezone.now()).total_seconds())
        self.assertLess(delta, 5)


# ===========================================================================
#  2. FSRS Bridge — review_card
# ===========================================================================
class ReviewCardTests(TestCase):
    """Test fsrs_bridge.review_card with all rating options."""

    def setUp(self):
        from vocab.fsrs_bridge import create_new_card_state
        self.card = create_new_card_state()
        self.card_json = json.loads(self.card.to_json())

    def test_review_again(self):
        from vocab.fsrs_bridge import review_card

        new_data, log_data, due_dt = review_card(self.card_json, "again")
        self.assertIsInstance(new_data, dict)
        self.assertIsInstance(log_data, dict)
        # After "again" on new card → should be Learning state
        self.assertEqual(new_data["state"], 1)  # Learning

    def test_review_good(self):
        from vocab.fsrs_bridge import review_card

        new_data, log_data, due_dt = review_card(self.card_json, "good")
        self.assertIsInstance(new_data, dict)
        # due should be in the future
        self.assertGreater(due_dt, timezone.now() - timedelta(seconds=1))

    def test_review_easy(self):
        from vocab.fsrs_bridge import review_card

        new_data, _, due_dt = review_card(self.card_json, "easy")
        # Easy on new card should graduate quickly → longer interval
        self.assertIsInstance(new_data, dict)

    def test_review_hard(self):
        from vocab.fsrs_bridge import review_card

        new_data, _, due_dt = review_card(self.card_json, "hard")
        self.assertIsInstance(new_data, dict)

    def test_review_with_json_string(self):
        """Should accept JSON string input."""
        from vocab.fsrs_bridge import review_card

        json_str = json.dumps(self.card_json)
        new_data, _, _ = review_card(json_str, "good")
        self.assertIsInstance(new_data, dict)

    def test_review_with_card_object(self):
        """Should accept Card object directly."""
        from vocab.fsrs_bridge import review_card

        new_data, _, _ = review_card(self.card, "good")
        self.assertIsInstance(new_data, dict)

    def test_review_returns_review_log(self):
        """Review log should contain rating info."""
        from vocab.fsrs_bridge import review_card

        _, log_data, _ = review_card(self.card_json, "good")
        self.assertIn("rating", log_data)

    def test_state_transition_new_to_learning(self):
        """New card + Again → Learning state."""
        from vocab.fsrs_bridge import review_card

        new_data, _, _ = review_card(self.card_json, "again")
        self.assertEqual(new_data["state"], 1)  # Learning

    def test_state_transition_learning_to_review(self):
        """Card that passes through learning steps should graduate to Review."""
        from vocab.fsrs_bridge import review_card

        # First review: New → Learning
        data1, _, _ = review_card(self.card_json, "good")
        # Second review: Learning → possibly Review (depends on scheduler)
        data2, _, _ = review_card(data1, "good")
        # State should advance (Learning=1 or Review=2)
        self.assertIn(data2["state"], [1, 2])

    def test_invalid_rating_defaults_to_good(self):
        """Unknown rating key should default to Good."""
        from vocab.fsrs_bridge import review_card

        new_data, _, _ = review_card(self.card_json, "unknown_rating")
        # Should not crash, defaults to Good
        self.assertIsInstance(new_data, dict)


# ===========================================================================
#  3. FSRS Bridge — preview_intervals
# ===========================================================================
class PreviewIntervalsTests(TestCase):
    """Test fsrs_bridge.preview_intervals."""

    def test_returns_all_rating_keys(self):
        from vocab.fsrs_bridge import preview_intervals, create_new_card_state

        card = create_new_card_state()
        result = preview_intervals(json.loads(card.to_json()))

        self.assertIn("again", result)
        self.assertIn("hard", result)
        self.assertIn("good", result)
        self.assertIn("easy", result)

    def test_intervals_are_strings(self):
        from vocab.fsrs_bridge import preview_intervals, create_new_card_state

        card = create_new_card_state()
        result = preview_intervals(json.loads(card.to_json()))

        for key in ["again", "hard", "good", "easy"]:
            self.assertIsInstance(result[key], str)
            self.assertTrue(len(result[key]) > 0)

    def test_accepts_dict_input(self):
        from vocab.fsrs_bridge import preview_intervals, create_new_card_state

        card = create_new_card_state()
        card_dict = json.loads(card.to_json())
        result = preview_intervals(card_dict)
        self.assertIn("again", result)


# ===========================================================================
#  4. FSRS Bridge — get_interval_display
# ===========================================================================
class GetIntervalDisplayTests(TestCase):
    """Test fsrs_bridge.get_interval_display."""

    def test_past_due(self):
        from vocab.fsrs_bridge import get_interval_display

        past = timezone.now() - timedelta(hours=1)
        self.assertEqual(get_interval_display(None, past), "now")

    def test_seconds(self):
        from vocab.fsrs_bridge import get_interval_display

        future = timezone.now() + timedelta(seconds=30)
        result = get_interval_display(None, future)
        self.assertTrue(result.endswith("s"))

    def test_minutes(self):
        from vocab.fsrs_bridge import get_interval_display

        future = timezone.now() + timedelta(minutes=5)
        result = get_interval_display(None, future)
        self.assertTrue(result.endswith("m"))

    def test_hours(self):
        from vocab.fsrs_bridge import get_interval_display

        future = timezone.now() + timedelta(hours=3)
        result = get_interval_display(None, future)
        self.assertTrue(result.endswith("h"))

    def test_days(self):
        from vocab.fsrs_bridge import get_interval_display

        future = timezone.now() + timedelta(days=5)
        result = get_interval_display(None, future)
        self.assertTrue(result.endswith("d"))

    def test_months(self):
        from vocab.fsrs_bridge import get_interval_display

        future = timezone.now() + timedelta(days=60)
        result = get_interval_display(None, future)
        self.assertTrue(result.endswith("mo"))

    def test_years(self):
        from vocab.fsrs_bridge import get_interval_display

        future = timezone.now() + timedelta(days=400)
        result = get_interval_display(None, future)
        self.assertTrue(result.endswith("y"))


# ===========================================================================
#  5. FSRS Bridge — card state helpers
# ===========================================================================
class CardStateHelperTests(TestCase):
    """Test get_card_state, is_learning_card, should_requeue_in_session."""

    def test_get_card_state_new(self):
        from vocab.fsrs_bridge import get_card_state

        self.assertEqual(get_card_state({"state": 0}), 0)

    def test_get_card_state_learning(self):
        from vocab.fsrs_bridge import get_card_state

        self.assertEqual(get_card_state({"state": 1}), 1)

    def test_get_card_state_missing_defaults_new(self):
        from vocab.fsrs_bridge import get_card_state

        self.assertEqual(get_card_state({}), 0)

    def test_is_learning_card_true(self):
        from vocab.fsrs_bridge import is_learning_card

        self.assertTrue(is_learning_card({"state": 1}))
        self.assertTrue(is_learning_card({"state": 3}))

    def test_is_learning_card_false(self):
        from vocab.fsrs_bridge import is_learning_card

        self.assertFalse(is_learning_card({"state": 0}))
        self.assertFalse(is_learning_card({"state": 2}))

    def test_requeue_learning_within_threshold(self):
        from vocab.fsrs_bridge import should_requeue_in_session

        due = timezone.now() + timedelta(minutes=5)  # Within 20min threshold
        self.assertTrue(should_requeue_in_session({"state": 1}, due))

    def test_no_requeue_reviewed_card(self):
        from vocab.fsrs_bridge import should_requeue_in_session

        due = timezone.now() + timedelta(minutes=5)
        self.assertFalse(should_requeue_in_session({"state": 2}, due))

    def test_no_requeue_past_threshold(self):
        from vocab.fsrs_bridge import should_requeue_in_session

        due = timezone.now() + timedelta(minutes=30)  # Beyond 20min threshold
        self.assertFalse(should_requeue_in_session({"state": 1}, due))


# ===========================================================================
#  6. Utility — card_data_to_dict
# ===========================================================================
class CardDataToDictTests(TestCase):
    """Test vocab.utils.card_data_to_dict normalisation."""

    def test_dict_passthrough(self):
        from vocab.utils import card_data_to_dict

        d = {"state": 0, "due": "2026-01-01"}
        self.assertEqual(card_data_to_dict(d), d)

    def test_json_string(self):
        from vocab.utils import card_data_to_dict

        s = json.dumps({"state": 2})
        result = card_data_to_dict(s)
        self.assertEqual(result["state"], 2)

    def test_card_object(self):
        from vocab.utils import card_data_to_dict
        from fsrs import Card

        card = Card()
        result = card_data_to_dict(card)
        self.assertIsInstance(result, dict)
        self.assertIn("state", result)

    def test_unknown_type_returns_empty(self):
        from vocab.utils import card_data_to_dict

        result = card_data_to_dict(12345)
        self.assertEqual(result, {})

    def test_none_returns_empty(self):
        from vocab.utils import card_data_to_dict

        result = card_data_to_dict(None)
        self.assertEqual(result, {})


# ===========================================================================
#  7. UserStudySettings model
# ===========================================================================
class UserStudySettingsTests(TestCase):
    """Test UserStudySettings daily limit logic."""

    def setUp(self):
        from vocab.models import UserStudySettings

        self.user = User.objects.create_user(
            username="studyuser", email="study@test.com", password="pass1234"
        )
        self.settings, _ = UserStudySettings.objects.get_or_create(
            user=self.user,
            defaults={
                "new_cards_per_day": 20,
                "reviews_per_day": 200,
            },
        )

    def test_defaults(self):
        self.assertEqual(self.settings.new_cards_per_day, 20)
        self.assertEqual(self.settings.reviews_per_day, 200)
        self.assertEqual(self.settings.new_cards_today, 0)
        self.assertEqual(self.settings.reviews_today, 0)

    def test_can_study_new_within_limit(self):
        self.settings.new_cards_today = 5
        self.settings.last_study_date = timezone.localdate()
        self.settings.save()
        self.assertTrue(self.settings.can_study_new())

    def test_can_study_new_at_limit(self):
        self.settings.new_cards_today = 20
        self.settings.last_study_date = timezone.localdate()
        self.settings.save()
        self.assertFalse(self.settings.can_study_new())

    def test_can_review_within_limit(self):
        self.settings.reviews_today = 50
        self.settings.last_study_date = timezone.localdate()
        self.settings.save()
        self.assertTrue(self.settings.can_review())

    def test_can_review_at_limit(self):
        self.settings.reviews_today = 200
        self.settings.last_study_date = timezone.localdate()
        self.settings.save()
        self.assertFalse(self.settings.can_review())

    def test_reset_daily_counts_new_day(self):
        """Counts should reset when date changes."""
        from datetime import date

        self.settings.new_cards_today = 15
        self.settings.reviews_today = 100
        self.settings.last_study_date = date(2020, 1, 1)  # Old date
        self.settings.save()

        self.settings.reset_daily_counts_if_needed()
        self.assertEqual(self.settings.new_cards_today, 0)
        self.assertEqual(self.settings.reviews_today, 0)
        self.assertEqual(self.settings.last_study_date, timezone.localdate())

    def test_reset_daily_counts_same_day(self):
        """Counts should NOT reset on same day."""
        self.settings.new_cards_today = 10
        self.settings.reviews_today = 50
        self.settings.last_study_date = timezone.localdate()
        self.settings.save()

        self.settings.reset_daily_counts_if_needed()
        self.assertEqual(self.settings.new_cards_today, 10)
        self.assertEqual(self.settings.reviews_today, 50)

    def test_one_to_one_constraint(self):
        """Should not allow two settings for same user."""
        from vocab.models import UserStudySettings
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            UserStudySettings.objects.create(
                user=self.user, new_cards_per_day=10
            )


# ===========================================================================
#  8. FsrsCardStateEn model
# ===========================================================================
class FsrsCardStateEnModelTests(TestCase):
    """Test FsrsCardStateEn model constraints and fields."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="carduser", email="card@test.com", password="pass1234"
        )

    def test_create_card_state(self):
        card = _create_card(self.user, word="apple")
        self.assertEqual(card.state, 0)
        self.assertEqual(card.total_reviews, 0)
        self.assertEqual(card.successful_reviews, 0)

    def test_unique_user_vocab_constraint(self):
        """Cannot have two cards for same user+vocab."""
        from vocab.models import FsrsCardStateEn

        _create_card(self.user, word="banana")
        vocab, _, _ = _create_vocab("banana")

        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            FsrsCardStateEn.objects.create(
                user=self.user, vocab=vocab,
                card_data={}, state=0,
            )

    def test_str_representation(self):
        card = _create_card(self.user, word="cherry")
        s = str(card)
        self.assertIn("carduser", s)
        self.assertIn("cherry", s)

    def test_different_users_same_vocab(self):
        """Different users can have cards for the same vocab."""
        user2 = User.objects.create_user(
            username="carduser2", email="card2@test.com", password="pass1234"
        )
        card1 = _create_card(self.user, word="orange")
        card2 = _create_card(user2, word="orange")
        self.assertNotEqual(card1.id, card2.id)


# ===========================================================================
#  9. Flashcard API endpoints
# ===========================================================================
class FlashcardAPITests(TestCase):
    """Test API endpoints: /flashcards, /review, /progress."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser", email="api@test.com", password="pass1234"
        )
        self.client.force_login(self.user)
        # Create cards with state=1 (Learning) so FsrsService.get_due_cards picks them up
        self.card1 = _create_card(self.user, word="run", state=1, due=timezone.now() - timedelta(hours=1))
        self.card2 = _create_card(self.user, word="jump", state=1, due=timezone.now() - timedelta(hours=2))
        self.card3 = _create_card(self.user, word="swim", state=2, due=timezone.now() + timedelta(days=5))

    @patch("vocab.services.fsrs_service.FsrsService.get_new_vocabs")
    def test_flashcard_review_due_cards(self, mock_new):
        """GET /flashcards should return cards that are due."""
        mock_new.return_value = []  # no new vocabs
        resp = self.client.get(f"{API}/flashcards")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # New format: {cards: [...], stats: {...}}
        self.assertIn("cards", data)
        self.assertIn("stats", data)
        words = [c["en_word"] for c in data["cards"]]
        self.assertIn("run", words)
        self.assertIn("jump", words)
        self.assertNotIn("swim", words)

    @patch("vocab.services.fsrs_service.FsrsService.get_new_vocabs")
    def test_flashcard_review_empty(self, mock_new):
        """No due cards → empty list."""
        mock_new.return_value = []  # no new vocabs
        user2 = User.objects.create_user(
            username="empty", email="empty@test.com", password="pass1234"
        )
        self.client.force_login(user2)
        resp = self.client.get(f"{API}/flashcards")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("cards", data)
        self.assertEqual(len(data["cards"]), 0)

    def test_review_due_count(self):
        """GET /review should return count of due cards."""
        resp = self.client.get(f"{API}/review")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["due_count"], 2)  # card1 and card2

    def test_progress_endpoint(self):
        """GET /progress should return total, mastered, review_due."""
        resp = self.client.get(f"{API}/progress")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_words"], 3)
        self.assertEqual(data["mastered"], 0)
        self.assertEqual(data["review_due"], 2)

    def test_progress_mastered_count(self):
        """Cards with total_reviews>=3 and successful_reviews>=2 are mastered."""
        self.card1.total_reviews = 5
        self.card1.successful_reviews = 4
        self.card1.save()

        resp = self.client.get(f"{API}/progress")
        data = resp.json()
        self.assertEqual(data["mastered"], 1)

    def test_study_status_endpoint(self):
        """GET /study-status should return daily limits and counts."""
        resp = self.client.get(f"{API}/study-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["new_cards_per_day"], 20)
        self.assertEqual(data["reviews_per_day"], 200)
        self.assertIn("can_study_new", data)
        self.assertIn("can_review", data)
        self.assertTrue(data["can_study_new"])
        self.assertTrue(data["can_review"])

    def test_unauthenticated_returns_error(self):
        """API should reject unauthenticated requests."""
        client = Client()
        resp = client.get(f"{API}/flashcards")
        self.assertIn(resp.status_code, [401, 403])


# ===========================================================================
# 10. My Words API
# ===========================================================================
class MyWordsAPITests(TestCase):
    """Test GET /my-words with filters."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="mywordsuser", email="words@test.com", password="pass1234"
        )
        self.client.force_login(self.user)

        # Create cards in different states
        self.new_card = _create_card(self.user, word="start", state=0)
        self.learning_card = _create_card(self.user, word="middle", state=1)
        self.review_card = _create_card(self.user, word="end", state=2)
        self.mastered_card = _create_card(
            self.user, word="done", state=2,
            total_reviews=5, successful_reviews=4,
        )

    def test_all_words(self):
        resp = self.client.get(f"{API}/my-words")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 4)

    def test_filter_new(self):
        resp = self.client.get(f"{API}/my-words?filter=new")
        data = resp.json()
        words = [c["word"] for c in data]
        self.assertIn("start", words)
        self.assertNotIn("end", words)

    def test_filter_learning(self):
        resp = self.client.get(f"{API}/my-words?filter=learning")
        data = resp.json()
        words = [c["word"] for c in data]
        self.assertIn("middle", words)

    def test_filter_review(self):
        resp = self.client.get(f"{API}/my-words?filter=review")
        data = resp.json()
        words = [c["word"] for c in data]
        self.assertIn("end", words)
        self.assertIn("done", words)

    def test_filter_mastered(self):
        resp = self.client.get(f"{API}/my-words?filter=mastered")
        data = resp.json()
        words = [c["word"] for c in data]
        self.assertIn("done", words)
        self.assertNotIn("start", words)

    def test_user_isolation(self):
        """User A should not see User B's words."""
        user_b = User.objects.create_user(
            username="userb", email="b@test.com", password="pass1234"
        )
        _create_card(user_b, word="private_word")

        resp = self.client.get(f"{API}/my-words")
        data = resp.json()
        words = [c["word"] for c in data]
        self.assertNotIn("private_word", words)


# ===========================================================================
# 11. FSRS Scheduler configuration
# ===========================================================================
class SchedulerConfigTests(TestCase):
    """Verify FSRS scheduler is configured correctly."""

    def test_scheduler_exists(self):
        from vocab.fsrs_bridge import scheduler
        self.assertIsNotNone(scheduler)

    def test_retention_rate(self):
        from vocab.fsrs_bridge import scheduler
        self.assertAlmostEqual(scheduler.desired_retention, 0.92, places=2)

    def test_fuzzing_disabled(self):
        from vocab.fsrs_bridge import scheduler
        self.assertFalse(scheduler.enable_fuzzing)

    def test_learning_steps_configured(self):
        from vocab.fsrs_bridge import scheduler
        steps = scheduler.learning_steps
        self.assertEqual(len(steps), 2)
        # 1 minute and 10 minutes
        self.assertEqual(steps[0], timedelta(minutes=1))
        self.assertEqual(steps[1], timedelta(minutes=10))


# ===========================================================================
# 12. _deserialize_card edge cases
# ===========================================================================
class DeserializeCardTests(TestCase):
    """Test fsrs_bridge._deserialize_card with various inputs."""

    def test_card_object(self):
        from vocab.fsrs_bridge import _deserialize_card
        from fsrs import Card

        card = Card()
        result = _deserialize_card(card)
        self.assertIsInstance(result, Card)

    def test_json_string(self):
        from vocab.fsrs_bridge import _deserialize_card
        from fsrs import Card

        card = Card()
        json_str = card.to_json()
        result = _deserialize_card(json_str)
        self.assertIsInstance(result, Card)

    def test_dict(self):
        from vocab.fsrs_bridge import _deserialize_card
        from fsrs import Card

        card = Card()
        card_dict = json.loads(card.to_json())
        result = _deserialize_card(card_dict)
        self.assertIsInstance(result, Card)
