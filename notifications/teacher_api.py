"""
Teacher Dashboard API — analytics and stats for teachers.

Aggregates data from QuizResult, GrammarAttempt, Assignment
to provide a comprehensive overview of student performance.
"""

from datetime import timedelta
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from ninja import Router, Schema

from common.models import QuizResult
from notifications.models import Assignment, Notification

User = get_user_model()

router = Router()


# ── Schemas ────────────────────────────────────────────────


class ScoreDistribution(Schema):
    excellent: int = 0  # 9-10
    good: int = 0       # 7-8.9
    average: int = 0    # 5-6.9
    weak: int = 0       # 3-4.9
    fail: int = 0       # 0-2.9


class QuizTypeStat(Schema):
    type: str
    label: str
    attempts: int
    avg_score: float
    best_score: float = 0


class StudentRanking(Schema):
    id: int
    username: str
    email: str
    total_attempts: int
    avg_score: float
    last_active: Optional[str] = None


class RecentResult(Schema):
    id: int
    username: str
    quiz_type: str
    quiz_id: str
    score: float
    correct: int
    total: int
    completed_at: str


class DailyTrend(Schema):
    date: str
    attempts: int
    avg_score: float


class AssignmentStat(Schema):
    id: int
    title: str
    quiz_type: str
    quiz_id: str
    teacher_name: str
    assigned_count: int
    completed_count: int
    created_at: str


class TeacherDashboardStats(Schema):
    # KPIs
    total_students: int = 0
    total_attempts: int = 0
    avg_score: float = 0
    completion_rate: float = 0
    attempts_today: int = 0
    attempts_week: int = 0

    # Charts
    score_distribution: ScoreDistribution
    by_quiz_type: List[QuizTypeStat]
    daily_trend: List[DailyTrend]

    # Tables
    student_rankings: List[StudentRanking]
    recent_results: List[RecentResult]
    assignment_stats: List[AssignmentStat]


# ── Quiz type labels ───────────────────────────────────────

QUIZ_TYPE_LABELS = {
    "grammar": "Grammar (EN)",
    "bunpou": "Bunpou (JP)",
    "vocab": "Vocabulary",
    "phrasal-verbs": "Phrasal Verbs",
    "usage": "Usage Quiz",
    "collocations": "Collocations",
    "exam": "Exam",
    "kanji": "Kanji",
    "dictation": "Dictation",
}


# ── Endpoint ───────────────────────────────────────────────


@router.get("/stats", response=TeacherDashboardStats)
def teacher_dashboard_stats(request):
    """Return all teacher dashboard statistics."""
    if not request.user.is_staff:
        from ninja.errors import HttpError
        raise HttpError(403, "Staff only")

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    two_weeks_ago = today_start - timedelta(days=14)

    # ── Base queryset ──────────────────────────────────────
    all_results = QuizResult.objects.all()

    # ── KPIs ───────────────────────────────────────────────
    total_students = User.objects.filter(is_staff=False, is_active=True).count()
    total_attempts = all_results.count()
    avg_score_val = all_results.aggregate(avg=Avg("score"))["avg"] or 0
    attempts_today = all_results.filter(completed_at__gte=today_start).count()
    attempts_week = all_results.filter(completed_at__gte=week_start).count()

    # ── Score distribution ─────────────────────────────────
    score_dist = ScoreDistribution(
        excellent=all_results.filter(score__gte=9).count(),
        good=all_results.filter(score__gte=7, score__lt=9).count(),
        average=all_results.filter(score__gte=5, score__lt=7).count(),
        weak=all_results.filter(score__gte=3, score__lt=5).count(),
        fail=all_results.filter(score__lt=3).count(),
    )

    # ── By quiz type ───────────────────────────────────────
    type_stats = (
        all_results.values("quiz_type")
        .annotate(
            attempts=Count("id"),
            avg_score=Avg("score"),
        )
        .order_by("-attempts")
    )

    by_quiz_type = []
    for ts in type_stats:
        qt = ts["quiz_type"]
        by_quiz_type.append(
            QuizTypeStat(
                type=qt,
                label=QUIZ_TYPE_LABELS.get(qt, qt.replace("-", " ").title()),
                attempts=ts["attempts"],
                avg_score=round(ts["avg_score"] or 0, 1),
            )
        )

    # ── Daily trend (14 days) ──────────────────────────────
    daily_trend = []
    for i in range(14):
        day = today_start - timedelta(days=13 - i)
        day_end = day + timedelta(days=1)
        day_results = all_results.filter(
            completed_at__gte=day, completed_at__lt=day_end
        )
        count = day_results.count()
        avg = day_results.aggregate(avg=Avg("score"))["avg"] or 0
        daily_trend.append(
            DailyTrend(
                date=day.strftime("%Y-%m-%d"),
                attempts=count,
                avg_score=round(avg, 1),
            )
        )

    # ── Student rankings (top 50) ──────────────────────────
    student_stats = (
        all_results.filter(user__is_staff=False)
        .values("user__id", "user__username", "user__email")
        .annotate(
            total_attempts=Count("id"),
            avg_score=Avg("score"),
        )
        .order_by("-avg_score")[:50]
    )

    student_rankings = []
    for ss in student_stats:
        # Get last active time
        last_result = (
            all_results.filter(user_id=ss["user__id"])
            .order_by("-completed_at")
            .values_list("completed_at", flat=True)
            .first()
        )
        student_rankings.append(
            StudentRanking(
                id=ss["user__id"],
                username=ss["user__username"],
                email=ss["user__email"],
                total_attempts=ss["total_attempts"],
                avg_score=round(ss["avg_score"] or 0, 1),
                last_active=last_result.isoformat() if last_result else None,
            )
        )

    # ── Recent results (last 50) ───────────────────────────
    recent_qs = (
        all_results.select_related("user")
        .order_by("-completed_at")[:50]
    )
    recent_results = [
        RecentResult(
            id=r.id,
            username=r.user.username,
            quiz_type=r.quiz_type,
            quiz_id=r.quiz_id,
            score=r.score,
            correct=r.correct_count,
            total=r.total_questions,
            completed_at=r.completed_at.isoformat(),
        )
        for r in recent_qs
    ]

    # ── Assignment stats ───────────────────────────────────
    assignments = Assignment.objects.select_related("teacher").all()
    assignment_stats = []
    total_assigned = 0
    total_completed = 0

    for a in assignments:
        assigned_count = a.assigned_to.count()
        # Count students who completed this quiz
        completed_count = QuizResult.objects.filter(
            quiz_type=a.quiz_type,
            quiz_id=a.quiz_id,
            user__in=a.assigned_to.all(),
        ).values("user").distinct().count()
        total_assigned += assigned_count
        total_completed += completed_count

        assignment_stats.append(
            AssignmentStat(
                id=a.id,
                title=a.title,
                quiz_type=a.quiz_type,
                quiz_id=a.quiz_id,
                teacher_name=a.teacher.get_full_name() or a.teacher.username,
                assigned_count=assigned_count,
                completed_count=completed_count,
                created_at=a.created_at.isoformat(),
            )
        )

    completion_rate = (
        round((total_completed / total_assigned) * 100, 1)
        if total_assigned > 0
        else 0
    )

    return {
        "total_students": total_students,
        "total_attempts": total_attempts,
        "avg_score": round(avg_score_val, 1),
        "completion_rate": completion_rate,
        "attempts_today": attempts_today,
        "attempts_week": attempts_week,
        "score_distribution": score_dist,
        "by_quiz_type": by_quiz_type,
        "daily_trend": daily_trend,
        "student_rankings": student_rankings,
        "recent_results": recent_results,
        "assignment_stats": assignment_stats,
    }
