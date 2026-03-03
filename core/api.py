"""Core API — courses, lessons, dictation, home stats, profile, settings."""

from ninja import Router, Schema
from typing import List, Optional

router = Router()


# ── Course Endpoints ──────────────────────────────────────

@router.get("/courses", response=list)
def list_courses(request):
    """List all courses."""
    from django.core.cache import cache
    from core.models import Course
    from django.db.models import Count

    cache_key = "core_courses_v1"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    courses = Course.objects.filter(is_active=True).annotate(
        _section_count=Count("sections", distinct=True),
        _lesson_count=Count("sections__lessons", distinct=True),
    )
    result = [
        {
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "order": c.order,
            "image": c.image.url if c.image else None,
            "description": c.description,
            "section_count": c._section_count,
            "lesson_count": c._lesson_count,
        }
        for c in courses
    ]
    cache.set(cache_key, result, 3600)  # 1 hour
    return result


@router.get("/courses/{slug}")
def course_detail(request, slug: str):
    """Get course detail with sections and lessons."""
    from core.models import Course
    c = Course.objects.prefetch_related("sections__lessons").get(slug=slug)
    sections = []
    for s in c.sections.filter(is_active=True):
        sections.append({
            "id": s.id,
            "title": s.title,
            "slug": s.slug,
            "order": s.order,
            "lessons": [
                {"id": l.id, "title": l.title, "slug": l.slug, "order": l.order}
                for l in s.lessons.filter(is_active=True)
            ],
        })
    return {
        "id": c.id,
        "title": c.title,
        "slug": c.slug,
        "description": c.description,
        "image": c.image.url if c.image else None,
        "sections": sections,
    }


@router.get("/courses/{course_slug}/lessons/{lesson_slug}")
def lesson_detail(request, course_slug: str, lesson_slug: str):
    """Get lesson content."""
    from core.models import Lesson
    lesson = Lesson.objects.select_related("section__course").get(
        slug=lesson_slug, section__course__slug=course_slug
    )
    # Get prev/next lessons
    siblings = list(Lesson.objects.filter(
        section__course=lesson.section.course, is_active=True
    ).order_by("section__order", "order"))
    idx = next((i for i, l in enumerate(siblings) if l.id == lesson.id), -1)
    prev_l = {"slug": siblings[idx - 1].slug, "title": siblings[idx - 1].title} if idx > 0 else None
    next_l = {"slug": siblings[idx + 1].slug, "title": siblings[idx + 1].title} if idx < len(siblings) - 1 else None

    return {
        "id": lesson.id,
        "title": lesson.title,
        "slug": lesson.slug,
        "content": lesson.content,
        "section_title": lesson.section.title if lesson.section else "",
        "course_title": lesson.section.course.title if lesson.section else "",
        "course_slug": lesson.section.course.slug if lesson.section else "",
        "prev_lesson": prev_l,
        "next_lesson": next_l,
    }


# ── Dictation Endpoints ───────────────────────────────────

@router.get("/dictation", response=list)
def list_dictation(request):
    """List dictation exercises."""
    from core.models import DictationExercise
    exercises = DictationExercise.objects.filter(is_active=True).prefetch_related("segments")
    return [
        {
            "id": e.id,
            "title": e.title,
            "slug": e.slug,
            "description": e.description,
            "difficulty": e.difficulty,
            "language": e.language,
            "audio_url": e.audio_file.url if e.audio_file else None,
            "audio_duration": e.audio_duration,
            "segment_count": e.segments.count(),
        }
        for e in exercises
    ]


@router.get("/dictation/{slug}")
def dictation_detail(request, slug: str):
    """Get dictation exercise with segments."""
    from core.models import DictationExercise
    e = DictationExercise.objects.prefetch_related("segments").get(slug=slug)
    return {
        "id": e.id,
        "title": e.title,
        "slug": e.slug,
        "description": e.description,
        "difficulty": e.difficulty,
        "language": e.language,
        "audio_url": e.audio_file.url if e.audio_file else None,
        "audio_duration": e.audio_duration,
        "full_transcript": e.full_transcript,
        "segment_count": e.segments.count(),
        "segments": [
            {
                "id": s.id,
                "order": s.order,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "correct_text": s.correct_text,
                "hint": s.hint,
                "duration": s.duration,
            }
            for s in e.segments.all()
        ],
    }


# ── Home Stats ────────────────────────────────────────────

@router.get("/home/stats")
def home_stats(request):
    """Get dashboard stats."""
    from streak.models import UserStreak
    from core.models import ExamGoal, UserBadge
    try:
        streak = UserStreak.objects.get(user=request.user)
        streak_days = streak.current_streak
    except Exception:
        streak_days = 0

    # Exam goal
    goal = None
    try:
        eg = ExamGoal.objects.get(user=request.user)
        goal = {
            "exam_type": eg.exam_type,
            "target_score": eg.target_score,
            "exam_date": eg.exam_date.isoformat() if eg.exam_date else None,
            "days_until_exam": eg.days_until_exam,
        }
    except ExamGoal.DoesNotExist:
        pass

    # Badges count
    badge_count = UserBadge.objects.filter(user=request.user).count()

    return {
        "streak_days": streak_days,
        "badge_count": badge_count,
        "exam_goal": goal,
    }


# ── Profile ───────────────────────────────────────────────

@router.get("/profile/me")
def my_profile(request):
    """Get current user's profile."""
    from core.models import UserProfile
    u = request.user
    profile = UserProfile.get_or_create_for_user(u)
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "date_joined": u.date_joined.isoformat(),
        "bio": profile.bio,
        "display_title": profile.display_title,
        "subtitle": profile.subtitle,
        "avatar": profile.avatar.url if profile.avatar else None,
        "cover_image": profile.cover_image.url if profile.cover_image else None,
        "social_links": profile.social_links,
        "info_items": profile.info_items,
        "skills": profile.skills,
        "certificates": profile.certificates,
        "hobbies": profile.hobbies,
        "study_language": profile.study_language,
    }


@router.get("/profile/{username}")
def user_profile(request, username: str):
    """Get public profile by username."""
    from django.contrib.auth import get_user_model
    from core.models import UserProfile
    User = get_user_model()
    u = User.objects.get(username=username)
    profile = UserProfile.get_or_create_for_user(u)
    return {
        "id": u.id,
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "date_joined": u.date_joined.isoformat(),
        "bio": profile.bio,
        "display_title": profile.display_title,
        "avatar": profile.avatar.url if profile.avatar else None,
        "social_links": profile.social_links,
        "study_language": profile.study_language,
    }


@router.put("/profile/update")
def update_profile(request, first_name: str = "", last_name: str = "", bio: str = "", display_title: str = ""):
    """Update current user's profile."""
    from core.models import UserProfile
    u = request.user
    if first_name:
        u.first_name = first_name
    if last_name:
        u.last_name = last_name
    u.save()

    profile = UserProfile.get_or_create_for_user(u)
    if bio:
        profile.bio = bio
    if display_title:
        profile.display_title = display_title
    profile.save()
    return {"success": True}


# ── Settings ──────────────────────────────────────────────

@router.get("/settings")
def get_settings(request):
    """Get user study settings."""
    from vocab.models import UserStudySettings
    settings, _ = UserStudySettings.objects.get_or_create(user=request.user)
    return {
        "new_cards_per_day": settings.new_cards_per_day,
        "reviews_per_day": settings.reviews_per_day,
        "english_voice": settings.english_voice_preference,
    }


@router.put("/settings")
def update_settings(request, new_cards_per_day: int = 20, reviews_per_day: int = 200, english_voice: str = "us"):
    """Update user study settings."""
    from vocab.models import UserStudySettings
    settings, _ = UserStudySettings.objects.get_or_create(user=request.user)
    settings.new_cards_per_day = new_cards_per_day
    settings.reviews_per_day = reviews_per_day
    settings.english_voice_preference = english_voice
    settings.save()
    return {"success": True}
