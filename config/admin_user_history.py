"""
Admin API: User Learning History & Statistics.

Provides a detailed view of a user's learning activity,
including EN10 vocab/grammar topics, exam attempts, study time, and vocab set progress.
"""

from ninja import Router, Schema
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from typing import Optional

User = get_user_model()

router = Router()


# ── Schemas ────────────────────────────────────────────────

class UserBasicOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_joined: str


class OverviewOut(Schema):
    total_minutes: int = 0
    total_days_active: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    total_words_mastered: int = 0
    total_exams_taken: int = 0


class EN10VocabTopicOut(Schema):
    topic_id: str
    title: str
    title_vi: str
    emoji: str
    total_words: int
    words_mastered: int


class EN10GrammarTopicOut(Schema):
    topic_id: str
    title: str
    title_vi: str
    emoji: str
    total_exercises: int


class ExamAttemptOut(Schema):
    id: int
    template_title: str
    book_title: str
    level: str
    correct_count: int
    total_questions: int
    score_percent: int
    started_at: str
    submitted_at: Optional[str] = None
    duration_minutes: Optional[float] = None


class VocabSetProgressOut(Schema):
    set_title: str
    collection_name: str
    status: str
    words_learned: int
    words_total: int
    quiz_best_score: int


class DailyActivityOut(Schema):
    date: str
    minutes_studied: float
    lessons_completed: int
    points_earned: int


class LearningHistoryOut(Schema):
    user: UserBasicOut
    overview: OverviewOut
    en10_vocab_topics: list[EN10VocabTopicOut]
    en10_grammar_topics: list[EN10GrammarTopicOut]
    exam_attempts: list[ExamAttemptOut]
    vocab_set_progress: list[VocabSetProgressOut]
    daily_activity: list[DailyActivityOut]


# ── Endpoint ───────────────────────────────────────────────

@router.get("/{user_id}/learning-history/", response=LearningHistoryOut)
def user_learning_history(request, user_id: int):
    """Return detailed learning history for a specific user."""
    from exam.models import ExamAttempt, EN10GrammarTopic, EN10VocabTopic
    from vocab.models import FsrsCardStateEn, UserSetProgress
    from streak.models import DailyActivity, StreakStat

    # Only staff can access
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    target_user = User.objects.get(id=user_id)

    # ── Overview ───────────────────────────────────────────
    # Study time from DailyActivity
    activity_agg = DailyActivity.objects.filter(user=target_user).aggregate(
        total_seconds=Sum("seconds_studied"),
        total_days=Count("id"),
    )
    total_seconds = activity_agg["total_seconds"] or 0
    total_days = activity_agg["total_days"] or 0

    # Streak info
    streak = StreakStat.objects.filter(user=target_user).first()
    current_streak = streak.current_streak if streak else 0
    longest_streak = streak.longest_streak if streak else 0

    # Words mastered (FSRS state=2 means "Review" = learned)
    total_words_mastered = FsrsCardStateEn.objects.filter(
        user=target_user, state=2
    ).count()

    # Total exams taken
    total_exams_taken = ExamAttempt.objects.filter(
        user=target_user, status="submitted"
    ).count()

    overview = OverviewOut(
        total_minutes=round(total_seconds / 60),
        total_days_active=total_days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_words_mastered=total_words_mastered,
        total_exams_taken=total_exams_taken,
    )

    # ── EN10 Vocab Topics ──────────────────────────────────
    mastered_vocab_ids = set(
        FsrsCardStateEn.objects.filter(user=target_user, state=2)
        .values_list("vocab_id", flat=True)
    )
    en10_vocab_topics = []
    for topic in EN10VocabTopic.objects.filter(is_active=True).order_by("order"):
        topic_vocab_ids = set(topic.vocabularies.values_list("id", flat=True))
        total_words = len(topic.words) if topic.words else 0
        # If topic has linked Vocabulary records, use those for mastery count
        if topic_vocab_ids:
            words_mastered = len(topic_vocab_ids & mastered_vocab_ids)
        else:
            words_mastered = 0
        en10_vocab_topics.append(EN10VocabTopicOut(
            topic_id=topic.slug,
            title=topic.title,
            title_vi=topic.title_vi,
            emoji=topic.emoji,
            total_words=total_words,
            words_mastered=words_mastered,
        ))

    # ── EN10 Grammar Topics ────────────────────────────────
    en10_grammar_topics = []
    for topic in EN10GrammarTopic.objects.filter(is_active=True).order_by("order"):
        total_exercises = len(topic.exercises) if topic.exercises else 0
        en10_grammar_topics.append(EN10GrammarTopicOut(
            topic_id=topic.topic_id,
            title=topic.title,
            title_vi=topic.title_vi,
            emoji=topic.emoji,
            total_exercises=total_exercises,
        ))

    # ── Exam Attempts ──────────────────────────────────────
    attempts = (
        ExamAttempt.objects
        .filter(user=target_user, status="submitted")
        .select_related("template", "template__book")
        .order_by("-started_at")[:50]
    )
    exam_attempts = []
    for a in attempts:
        duration = None
        if a.submitted_at and a.started_at:
            delta = a.submitted_at - a.started_at
            duration = round(delta.total_seconds() / 60, 1)
        exam_attempts.append(ExamAttemptOut(
            id=a.id,
            template_title=a.template.title,
            book_title=a.template.book.title if a.template.book else "",
            level=a.template.level,
            correct_count=a.correct_count,
            total_questions=a.total_questions,
            score_percent=a.score_percent,
            started_at=a.started_at.isoformat(),
            submitted_at=a.submitted_at.isoformat() if a.submitted_at else None,
            duration_minutes=duration,
        ))

    # ── Vocab Set Progress ─────────────────────────────────
    progress_qs = (
        UserSetProgress.objects
        .filter(user=target_user)
        .select_related("vocabulary_set", "vocabulary_set__collection")
        .order_by("-started_at")
    )
    vocab_set_progress = []
    for p in progress_qs:
        vocab_set_progress.append(VocabSetProgressOut(
            set_title=p.vocabulary_set.title,
            collection_name=p.vocabulary_set.collection.name if p.vocabulary_set.collection else "",
            status=p.status,
            words_learned=p.words_learned,
            words_total=p.words_total,
            quiz_best_score=p.quiz_best_score,
        ))

    # ── Daily Activity (last 60 days) ──────────────────────
    daily_qs = (
        DailyActivity.objects
        .filter(user=target_user)
        .order_by("-date")[:60]
    )
    daily_activity = []
    for d in daily_qs:
        daily_activity.append(DailyActivityOut(
            date=d.date.isoformat(),
            minutes_studied=round(d.seconds_studied / 60, 1) if d.seconds_studied else d.minutes_studied,
            lessons_completed=d.lessons_completed,
            points_earned=d.points_earned,
        ))
    # Reverse so oldest is first (for charts)
    daily_activity.reverse()

    # ── User basic info ────────────────────────────────────
    user_out = UserBasicOut(
        id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        first_name=target_user.first_name,
        last_name=target_user.last_name,
        date_joined=target_user.date_joined.isoformat(),
    )

    return LearningHistoryOut(
        user=user_out,
        overview=overview,
        en10_vocab_topics=en10_vocab_topics,
        en10_grammar_topics=en10_grammar_topics,
        exam_attempts=exam_attempts,
        vocab_set_progress=vocab_set_progress,
        daily_activity=daily_activity,
    )
