# core/views.py
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from streak.models import StreakStat, DailyActivity
from vocab.models import UserStudySettings

from .models import Course, Lesson, Section


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


def course_list(request):
    courses = Course.objects.filter(is_active=True).order_by("order", "title")
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, course_slug: str):
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    sections = (
        Section.objects.filter(course=course, is_active=True)
        .prefetch_related("lessons")
        .order_by("order", "title")
    )
    # Pick first lesson to show on the right by default (if any)
    first_lesson = (
        Lesson.objects.filter(section__course=course, is_active=True)
        .select_related("section", "section__course")
        .order_by("section__order", "order", "title")
        .first()
    )

    return render(request, "courses/course_detail.html", {
        "course": course,
        "sections": sections,
        "active_section": None,
        "active_lesson": None,
        "lesson": first_lesson,
    })


def lesson_detail(request, course_slug: str, lesson_slug: str):
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    lesson = get_object_or_404(
        Lesson.objects.select_related("section", "section__course"),
        slug=lesson_slug,
        section__course=course,
        is_active=True,
    )
    sections = (
        Section.objects.filter(course=course, is_active=True)
        .prefetch_related("lessons")
        .order_by("order", "title")
    )
    return render(request, "courses/course_lesson.html", {
        "course": course,
        "sections": sections,
        "active_section": lesson.section,
        "active_lesson": lesson,
        "lesson": lesson,
    })
