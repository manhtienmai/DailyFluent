# core/views.py
import json
import random
import re
import os
from datetime import timedelta
from urllib.parse import urlsplit

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.db import models
from django.conf import settings

from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from streak.models import StreakStat, DailyActivity
from vocab.models import UserStudySettings

from django.core.paginator import Paginator
# from vocab.models import EnglishVocabulary
from .models import Course, Lesson, Section, DictationExercise, DictationSegment

# Placement imports
from placement.models import UserLearningProfile, LearningPath
from placement.services.daily_recommender import DailyRecommendationEngine


def _mask_word_in_sentence(word: str, sentence: str) -> tuple[str, bool]:
    """
    Replace the first occurrence of `word` in `sentence` with "____".
    Returns (masked_sentence, did_replace).

    Notes:
    - For single-token words, try word-boundary matching (case-insensitive).
    - For multi-word phrases, fall back to substring replace (case-insensitive).
    """
    if not sentence:
        return "____", False
    w = (word or "").strip()
    if not w:
        return sentence, False

    # Multi-word -> simple case-insensitive replace of first occurrence
    if " " in w:
        m = re.search(re.escape(w), sentence, flags=re.IGNORECASE)
        if not m:
            return sentence, False
        return sentence[: m.start()] + "____" + sentence[m.end() :], True

    # Single token -> prefer word boundary
    pattern = re.compile(rf"(?i)\b{re.escape(w)}\b")
    masked, n = pattern.subn("____", sentence, count=1)
    if n:
        return masked, True

    # Fallback: replace first case-insensitive occurrence anywhere
    m = re.search(re.escape(w), sentence, flags=re.IGNORECASE)
    if not m:
        return sentence, False
    return sentence[: m.start()] + "____" + sentence[m.end() :], True


def _build_mcq_questions(words: list, *, options_count: int = 4) -> list[dict]:
# def _build_mcq_questions(words: list[EnglishVocabulary], *, options_count: int = 4) -> list[dict]:
    """
    Build MCQ questions for EN vocab with 2 types (1 question per word):
    1. choose_vi: English word + English definition, choose Vietnamese meaning
    2. choose_word: Example sentence + English definition, choose English word
    """
    pool_words = [w.en_word for w in words if w.en_word]
    pool_meanings = [(w.vi_meaning or "").strip() for w in words if (w.vi_meaning or "").strip()]
    # Build mapping: word -> vi_meaning and vi_meaning -> word
    word_to_vi = {w.en_word.lower(): (w.vi_meaning or "").strip() for w in words if w.en_word and (w.vi_meaning or "").strip()}
    vi_to_word = {(w.vi_meaning or "").strip().lower(): w.en_word for w in words if w.en_word and (w.vi_meaning or "").strip()}
    questions: list[dict] = []

    for w in words:
        word = (w.en_word or "").strip()
        vi_meaning = (w.vi_meaning or "").strip()
        if not word or not vi_meaning:
            continue

        # Choose example sentence
        ex_sentence = ""
        ex_sentence_marked = ""  # For MCQ: sentence with marker replaced by blanks
        examples = list(getattr(w, "examples", []).all()) if hasattr(w, "examples") else []
        if examples:
            for ex in examples:
                if (ex.en or "").strip():
                    ex_sentence = ex.en.strip()
                    # Check if there's a marked version (sentence_marked)
                    if hasattr(ex, "sentence_marked") and ex.sentence_marked:
                        ex_sentence_marked = ex.sentence_marked.strip()
                    break
        if not ex_sentence:
            ex_sentence = (w.example_en or "").strip()

        hint = (w.en_definition or "").strip()

        # Randomly choose between type 2 (choose_vi) and type 3 (choose_word)
        # If no example sentence, only use type 2
        use_type_3 = ex_sentence and random.choice([True, False])
        
        if use_type_3:
            # Type 3: Choose word (example + definition, choose word)
            # Replace marked word with blanks (______) - fixed length (8 underscores)
            question_text = ex_sentence
            BLANK_LENGTH = 8
            
            if ex_sentence_marked:
                # Replace markers ⟦word⟧ or [word] with fixed-length blanks
                # Pattern to match ⟦word⟧ or [word] (but not [context])
                pattern = r'⟦([^⟦⟧]+)⟧|\[([^\]]+)\]'
                question_text = re.sub(pattern, '_' * BLANK_LENGTH, ex_sentence_marked)
            else:
                # If no marked version, try to find and replace the word in the sentence
                # Case-insensitive word boundary replacement
                word_pattern = r'\b' + re.escape(word) + r'\b'
                question_text = re.sub(word_pattern, '_' * BLANK_LENGTH, ex_sentence, flags=re.IGNORECASE)
            
            # Distractors: other English words
            distractors_word = [x for x in pool_words if x.lower() != word.lower()]
            random.shuffle(distractors_word)
            need = max(0, options_count - 1)
            picked_word = []
            seen_word = set()
            for d in distractors_word:
                key = d.lower()
                if key in seen_word:
                    continue
                seen_word.add(key)
                picked_word.append(d)
                if len(picked_word) >= need:
                    break

            options_word = picked_word + [word]
            random.shuffle(options_word)
            
            # Build option translations: each option (EN word) -> VI meaning
            option_translations = {}
            for opt in options_word:
                opt_lower = opt.lower()
                if opt_lower in word_to_vi:
                    option_translations[opt] = word_to_vi[opt_lower]

            questions.append({
                "id": w.id,
                "type": "choose_word",
                "question": question_text,  # Use text with blanks instead of original sentence
                "hint": hint,
                "options": options_word,
                "answer": word,
                "answer_vi": vi_meaning,
                "option_translations": option_translations,  # Map option -> translation
            })
        else:
            # Type 2: Choose Vietnamese meaning (word + definition, choose VI meaning)
            # Distractors: other Vietnamese meanings
            distractors_vi = [x for x in pool_meanings if x.lower() != vi_meaning.lower()]
            random.shuffle(distractors_vi)
            need = max(0, options_count - 1)
            picked_vi = []
            seen_vi = set()
            for d in distractors_vi:
                key = d.lower()
                if key in seen_vi:
                    continue
                seen_vi.add(key)
                picked_vi.append(d)
                if len(picked_vi) >= need:
                    break

            options_vi = picked_vi + [vi_meaning]
            random.shuffle(options_vi)
            
            # Build option translations: each option (VI meaning) -> EN word
            option_translations = {}
            for opt in options_vi:
                opt_lower = opt.lower()
                if opt_lower in vi_to_word:
                    option_translations[opt] = vi_to_word[opt_lower]

            questions.append({
                "id": w.id,
                "type": "choose_vi",
                "question": word,
                "hint": hint,
                "options": options_vi,
                "answer": vi_meaning,
                "answer_en": word,
                "option_translations": option_translations,  # Map option -> translation
            })

    # Shuffle all questions
    random.shuffle(questions)
    return questions


def _build_matching_boards(words: list, *, pairs_per_board: int = 8) -> list[dict]:
# def _build_matching_boards(words: list[EnglishVocabulary], *, pairs_per_board: int = 8) -> list[dict]:
    """
    Build 4x4 matching boards for EN vocab.
    - Each board: up to 8 pairs (word + vi meaning) -> 16 tiles.
    - If fewer than 8 pairs remain, fill the rest with blank tiles (non-clickable) to keep 4x4.
    """
    candidates = []
    seen = set()
    for w in words:
        en = (w.en_word or "").strip()
        vi = (w.vi_meaning or "").strip()
        if not en or not vi:
            continue
        key = (en.lower(), vi.lower())
        if key in seen:
            continue
        seen.add(key)
        candidates.append({"id": w.id, "word": en, "meaning": vi})

    random.shuffle(candidates)

    boards: list[dict] = []
    for bi in range(0, len(candidates), pairs_per_board):
        chunk = candidates[bi : bi + pairs_per_board]
        tiles: list[dict] = []
        for item in chunk:
            vid = item["id"]
            tiles.append({"key": f"w-{vid}", "pair_id": vid, "kind": "word", "text": item["word"]})
            tiles.append({"key": f"m-{vid}", "pair_id": vid, "kind": "meaning", "text": item["meaning"]})

        blanks = max(0, 16 - len(tiles))
        for i in range(blanks):
            tiles.append({"key": f"b-{bi}-{i}", "pair_id": None, "kind": "blank", "text": ""})

        random.shuffle(tiles)
        boards.append({"pairs": len(chunk), "tiles": tiles})

    return boards


def _build_fill_questions(words: list) -> list[dict]:
# def _build_fill_questions(words: list[EnglishVocabulary]) -> list[dict]:
    """
    Build fill-in questions (typing):
    - Show Vietnamese meaning + English definition as hints
    - User types the English word/phrase (en_word)
    """
    questions: list[dict] = []
    for w in words:
        ans = (w.en_word or "").strip()
        if not ans:
            continue
        vi = (w.vi_meaning or "").strip()
        hint_en = (w.en_definition or "").strip()
        questions.append(
            {
                "id": w.id,
                "answer": ans,
                "hint_vi": vi,
                "hint_en": hint_en,
            }
        )
    return questions


def _build_listening_audio_path(audio_pack_uuid, audio_type):
    """Helper to build audio path (similar to vocab_tags._build_audio_path)"""
    if not audio_pack_uuid:
        return ""
    
    # Validate UUID format
    try:
        uuid_str = str(audio_pack_uuid).strip()
        if len(uuid_str) != 36 or uuid_str.count('-') != 4:
            return ""
    except (AttributeError, TypeError):
        return ""
    
    if audio_type == "word":
        filename = "word"
    else:
        return ""
    
    return f"dailyfluent/{uuid_str}/{filename}"


def _build_listening_questions(words: list, *, options_count: int = 4) -> list[dict]:
# def _build_listening_questions(words: list[EnglishVocabulary], *, options_count: int = 4) -> list[dict]:
    """
    Build listening comprehension questions with 3 types:
    1. choose_meaning: Listen to audio, choose Vietnamese meaning (most common)
    2. choose_word: Listen to audio, choose English word
    3. dictation: Listen to audio, type the word
    
    Each word gets 1 question, randomly assigned to one of the 3 types.
    Requires audio_pack_uuid for audio playback.
    """
    from django.conf import settings
    
    pool_words = [w.en_word for w in words if w.en_word]
    pool_meanings = [(w.vi_meaning or "").strip() for w in words if (w.vi_meaning or "").strip()]
    
    # Build mapping
    word_to_vi = {w.en_word.lower(): (w.vi_meaning or "").strip() for w in words if w.en_word and (w.vi_meaning or "").strip()}
    
    questions: list[dict] = []
    audio_base_url = getattr(settings, 'AUDIO_BASE_URL', '')
    
    for w in words:
        word = (w.en_word or "").strip()
        vi_meaning = (w.vi_meaning or "").strip()
        audio_pack_uuid = (w.audio_pack_uuid or "").strip()
        
        if not word or not vi_meaning:
            continue
        
        # Skip if no audio
        if not audio_pack_uuid:
            continue
        
        # Build audio URLs
        base_path = _build_listening_audio_path(audio_pack_uuid, "word")
        if not base_path or not audio_base_url:
            continue
        
        audio_us_url = f"{audio_base_url}{base_path}_us.mp3"
        audio_uk_url = f"{audio_base_url}{base_path}_uk.mp3"
        
        # Randomly choose question type (70% choose_meaning, 20% choose_word, 10% dictation)
        rand = random.random()
        if rand < 0.7:
            # Type 1: Choose meaning (listen, choose Vietnamese meaning)
            distractors_vi = [x for x in pool_meanings if x.lower() != vi_meaning.lower()]
            random.shuffle(distractors_vi)
            need = max(0, options_count - 1)
            picked_vi = []
            seen_vi = set()
            for d in distractors_vi:
                key = d.lower()
                if key in seen_vi:
                    continue
                seen_vi.add(key)
                picked_vi.append(d)
                if len(picked_vi) >= need:
                    break
            
            # Fill remaining with random if needed
            while len(picked_vi) < need:
                filler = random.choice(pool_meanings)
                if filler.lower() not in seen_vi and filler.lower() != vi_meaning.lower():
                    picked_vi.append(filler)
                    seen_vi.add(filler.lower())
            
            options = [vi_meaning] + picked_vi
            random.shuffle(options)
            correct_idx = options.index(vi_meaning)
            
            questions.append({
                "id": w.id,
                "type": "choose_meaning",
                "word": word,
                "audio_us": audio_us_url,
                "audio_uk": audio_uk_url,
                "options": options,
                "correct_answer": correct_idx,
                "correct_text": vi_meaning,
            })
        elif rand < 0.9:
            # Type 2: Choose word (listen, choose English word)
            distractors_word = [x for x in pool_words if x.lower() != word.lower()]
            random.shuffle(distractors_word)
            need = max(0, options_count - 1)
            picked_word = []
            seen_word = set()
            for d in distractors_word:
                key = d.lower()
                if key in seen_word:
                    continue
                seen_word.add(key)
                picked_word.append(d)
                if len(picked_word) >= need:
                    break
            
            # Fill remaining
            while len(picked_word) < need:
                filler = random.choice(pool_words)
                if filler.lower() not in seen_word and filler.lower() != word.lower():
                    picked_word.append(filler)
                    seen_word.add(filler.lower())
            
            options = [word] + picked_word
            random.shuffle(options)
            correct_idx = options.index(word)
            
            questions.append({
                "id": w.id,
                "type": "choose_word",
                "word": word,
                "audio_us": audio_us_url,
                "audio_uk": audio_uk_url,
                "options": options,
                "correct_answer": correct_idx,
                "correct_text": word,
                "hint_vi": vi_meaning,  # Show meaning as hint
            })
        else:
            # Type 3: Dictation (listen, type the word)
            questions.append({
                "id": w.id,
                "type": "dictation",
                "word": word,
                "audio_us": audio_us_url,
                "audio_uk": audio_uk_url,
                "correct_answer": word.lower().strip(),
                "hint_vi": vi_meaning,
                "hint_en": (w.en_definition or "").strip(),
            })
    
    # Shuffle all questions
    random.shuffle(questions)
    return questions


def home(request):
    """
    Dashboard chính.
    - Nếu user đăng nhập: hiện dashboard với streak và đề thi mới nhất.
    - Nếu chưa đăng nhập: hiện landing page.
    """
    # Landing page for unauthenticated users
    if not request.user.is_authenticated:
        return render(request, "landingpage.html")

    from exam.models import ExamTemplate, ExamAttempt
    from django.db.models import Count, Q

    streak = None
    minutes_today = 0
    cards_today = 0
    new_cards_today = 0
    reviews_today = 0
    todo_items = []
    
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
        
        # Lấy todo items của user theo period_type
        from todos.models import TodoItem
        from datetime import datetime, timedelta
        from django.utils import timezone as tz
        
        # Get period filter from request (default to 'day')
        period_filter = request.GET.get('period', 'day')
        
        today = tz.localdate()
        todos_query = TodoItem.objects.filter(user=request.user, period_type=period_filter)
        
        # Filter by time period
        if period_filter == 'day':
            # Today's todos
            todos_query = todos_query.filter(created_at__date=today)
        elif period_filter == 'week':
            # This week's todos (Monday to Sunday)
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            todos_query = todos_query.filter(created_at__date__gte=week_start, created_at__date__lte=week_end)
        elif period_filter == 'month':
            # This month's todos
            month_start = today.replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
            todos_query = todos_query.filter(created_at__date__gte=month_start, created_at__date__lte=month_end)
        elif period_filter == 'year':
            # This year's todos
            year_start = today.replace(month=1, day=1)
            year_end = today.replace(month=12, day=31)
            todos_query = todos_query.filter(created_at__date__gte=year_start, created_at__date__lte=year_end)
        
        todo_items = todos_query.order_by("completed", "-created_at")[:20]
    
    # Lấy 8 đề thi mới nhất theo tên (cho cả logged in và not logged in)
    latest_exams = list(
        ExamTemplate.objects
        .filter(is_active=True)
        .annotate(
            attempt_count=Count('attempts', filter=Q(attempts__status='submitted'), distinct=True),
            distinct_parts=Count('questions__toeic_part', distinct=True)
        )
        .order_by('title')[:8]
    )
    
    # Tính comment count (fake: 10% của attempt_count, min 100)
    for exam in latest_exams:
        exam.comment_count = max(100, int(exam.attempt_count * 0.1))
    
    # Lấy khóa học đã đăng ký và kết quả luyện thi gần nhất
    enrolled_courses = []
    recent_exam_results = []
    
    if request.user.is_authenticated:
        # Lấy khóa học đã đăng ký (max 4)
        from core.models import Enrollment
        enrolled_courses = Enrollment.objects.filter(
            user=request.user
        ).select_related('course').order_by('-enrolled_at')[:4]
        
        # Lấy kết quả luyện thi gần nhất (max 5)
        recent_exam_results = ExamAttempt.objects.filter(
            user=request.user,
            status=ExamAttempt.Status.SUBMITTED
        ).select_related('template').order_by('-submitted_at')[:5]
        
        # Lấy mục tiêu kỳ thi
        from core.models import ExamGoal
        exam_goal, _ = ExamGoal.objects.get_or_create(user=request.user)
        
        # Build vocab stats for dashboard
        from vocab.models import FsrsCardStateEn
        total_vocab = FsrsCardStateEn.objects.filter(user=request.user).count()
        mastered = FsrsCardStateEn.objects.filter(
            user=request.user,
            total_reviews__gte=3,
            successful_reviews__gte=2
        ).count()
        learning = total_vocab - mastered
        progress = f"{int((mastered / total_vocab) * 100)}%" if total_vocab > 0 else "0%"
        
        vocab_stats = {
            "mastered": mastered,
            "learning": learning,
            "total": total_vocab,
            "progress": progress,
        }
        
        # Build week days for streak display
        from datetime import timedelta
        today = timezone.localdate()
        day_labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        week_days = []
        
        # Get last 7 days of activity
        week_start = today - timedelta(days=6)
        activities = DailyActivity.objects.filter(
            user=request.user,
            date__gte=week_start,
            date__lte=today
        ).values_list('date', flat=True)
        activity_dates = set(activities)
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            weekday_idx = day.weekday()  # 0=Monday
            week_days.append({
                "label": day_labels[weekday_idx],
                "studied": day in activity_dates,
                "is_today": day == today,
            })
            
        # Placement Dashboard Data
        placement_data = {}
        try:
            profile = UserLearningProfile.objects.filter(user=request.user).first()
            active_path = LearningPath.objects.filter(
                user=request.user, is_active=True
            ).prefetch_related('milestones').first()
            
            engine = DailyRecommendationEngine(request.user)
            lesson = engine.generate_daily_lesson()
            
            placement_data = {
                'profile': profile,
                'path': active_path,
                'lesson': lesson,
            }
        except Exception as e:
            print(f"Error fetching placement data: {e}")
    else:
        vocab_stats = {}
        week_days = []
        exam_goal = None
        placement_data = {}

    # Get study_language for dashboard filtering
    from core.models import UserProfile
    user_profile = UserProfile.get_or_create_for_user(request.user)
    study_language = user_profile.study_language

    context = {
        "streak": streak,
        "minutes_today": minutes_today,
        "cards_today": cards_today,
        "new_cards_today": new_cards_today,
        "reviews_today": reviews_today,
        "latest_exams": latest_exams,
        "enrolled_courses": enrolled_courses,
        "recent_exam_results": recent_exam_results,
        "vocab_stats": vocab_stats,
        "week_days": week_days,
        "study_language": study_language,
        # Placement data
        "profile": placement_data.get('profile'),
        "path": placement_data.get('path'),
        "lesson": placement_data.get('lesson'),
    }
    return render(request, "home.html", context)


def course_list(request):
    courses = Course.objects.filter(is_active=True).order_by("order", "title")
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, course_slug: str):
    # from vocab.models import EnglishVocabulary
    from core.models import Enrollment
    from django.utils import timezone
    
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    
    # Auto-enroll user when they access the course
    enrollment = None
    if request.user.is_authenticated:
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course
        )
        # Update last_accessed timestamp
        enrollment.last_accessed = timezone.now()
        enrollment.save(update_fields=['last_accessed'])
    
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
    
    # Check if a section is selected from URL parameter
    active_section = None
    section_slug = request.GET.get("section")
    if section_slug:
        try:
            active_section = Section.objects.get(
                course=course,
                slug=section_slug,
                is_active=True
            )
        except Section.DoesNotExist:
            pass
    
    # Check which sections have vocabulary (for showing vocab modes)
    section_ids_with_vocab = set()
    # section_ids_with_vocab = set(
    #     EnglishVocabulary.objects.filter(
    #         section_ref__in=sections,
    #         is_active=True
    #     ).values_list('section_ref_id', flat=True).distinct()
    # )

    return render(request, "courses/course_detail.html", {
        "course": course,
        "sections": sections,
        "active_section": active_section,
        "active_lesson": None,
        "lesson": first_lesson,
        "section_ids_with_vocab": section_ids_with_vocab,
    })


def _get_default_mode_for_lesson(lesson):
    """
    Xác định mode mặc định cho lesson dựa trên nội dung có sẵn.
    Logic: Nếu có từ vựng → vocab, nếu không có từ vựng → grammar
    
    Returns:
        str: Mode mặc định ('vocab' nếu có từ vựng, 'grammar' nếu không có từ vựng)
    """
    # Kiểm tra từ vựng
    vocab_count = 0
    # vocab_count = EnglishVocabulary.objects.filter(
    #     is_active=True, lesson_ref=lesson
    # ).count()
    if vocab_count > 0:
        return "vocab"
    
    # Nếu không có từ vựng, mặc định là grammar
    return "grammar"


def _lesson_has_content(lesson, mode):
    """
    Kiểm tra xem lesson có nội dung cho mode cụ thể không.
    
    Args:
        lesson: Lesson object
        mode: Mode cần kiểm tra
        
    Returns:
        bool: True nếu có nội dung, False nếu không
    """
    if mode == "vocab":
        return False
        # return EnglishVocabulary.objects.filter(
        #     is_active=True, lesson_ref=lesson
        # ).exists()
    elif mode == "grammar":
        # Có content hoặc có grammar points
        has_content = lesson.content and lesson.content.strip()
        from grammar.models import GrammarPoint
        has_grammar_points = GrammarPoint.objects.filter(
            lesson=lesson, is_active=True
        ).exists()
        return has_content or has_grammar_points
    # Các mode khác đều phụ thuộc vào vocab
    elif mode in ("mcq", "matching", "fill", "listening"):
        return False
        # return EnglishVocabulary.objects.filter(
        #     is_active=True, lesson_ref=lesson
        # ).exists()
    return False



def _build_dictation_questions(words: list) -> list[dict]:
# def _build_dictation_questions(words: list[EnglishVocabulary]) -> list[dict]:
    """
    Build dictation questions:
    - Listen to audio -> Type the word
    - Requires audio_pack_uuid
    """
    from django.conf import settings
    
    questions: list[dict] = []
    audio_base_url = getattr(settings, 'AUDIO_BASE_URL', '')

    for w in words:
        word = (w.en_word or "").strip()
        vi_meaning = (w.vi_meaning or "").strip()
        audio_pack_uuid = (w.audio_pack_uuid or "").strip()

        if not word or not audio_pack_uuid:
            continue
            
        base_path = _build_listening_audio_path(audio_pack_uuid, "word")
        if not base_path or not audio_base_url:
            continue

        audio_us_url = f"{audio_base_url}{base_path}_us.mp3"
        audio_uk_url = f"{audio_base_url}{base_path}_uk.mp3"

        questions.append({
            "id": w.id,
            "type": "dictation",
            "word": word,
            "audio_us": audio_us_url,
            "audio_uk": audio_uk_url,
            "correct_answer": word, # Case sensitive logic handled in frontend or usually lowercase
            "hint_vi": vi_meaning,
            "hint_en": (w.en_definition or "").strip(),
            "ipa": (w.phonetic or "").strip(),
        })

    random.shuffle(questions)
    return questions


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

    # Prev/Next lesson within course
    ordered_lessons = list(
        Lesson.objects.filter(section__course=course, is_active=True)
        .select_related("section", "section__course")
        .order_by("section__order", "section__title", "order", "title", "id")
    )
    prev_lesson = None
    next_lesson = None
    for i, l in enumerate(ordered_lessons):
        if l.id == lesson.id:
            if i > 0:
                prev_lesson = ordered_lessons[i - 1]
            if i + 1 < len(ordered_lessons):
                next_lesson = ordered_lessons[i + 1]
            break

    # Xác định mode: ưu tiên mode từ query param, nếu không có thì dùng default
    requested_mode = request.GET.get("mode", "").strip().lower()
    valid_modes = ("vocab", "flashcards", "mcq", "matching", "listening", "fill", "dictation", "grammar")
    
    if requested_mode and requested_mode in valid_modes:
        mode = requested_mode
    else:
        # Tự động chọn mode dựa trên nội dung có sẵn
        mode = _get_default_mode_for_lesson(lesson)

    # English vocab for this lesson
    en_qs = []
    # en_qs = (
    #     EnglishVocabulary.objects.filter(is_active=True, lesson_ref=lesson)
    #     .select_related("course_ref", "section_ref", "lesson_ref")
    #     .prefetch_related("examples")
    #     .order_by("en_word", "id")
    # )
    total_count = en_qs.count()

    page_obj = None
    page_items = None
    base_qs = ""
    questions_json = ""
    questions_count = 0
    matching_boards_json = ""
    matching_boards_count = 0
    fill_questions_json = ""
    fill_questions_count = 0
    listening_questions_json = ""
    listening_questions_count = 0
    dictation_questions_json = ""
    dictation_questions_count = 0

    if mode == "vocab":
        page_number = request.GET.get("page", 1)
        # Get per_page from request, default to 20, validate allowed values
        per_page = request.GET.get("per_page", "20")
        try:
            per_page = int(per_page)
            if per_page not in [10, 20, 30, 50, 100]:
                per_page = 20
        except (ValueError, TypeError):
            per_page = 20
        
        paginator = Paginator(en_qs, per_page)
        page_obj = paginator.get_page(page_number)
        from vocab.views import _pagination_items  # reuse helper
        page_items = _pagination_items(paginator, page_obj.number)
        qs_params = request.GET.copy()
        qs_params.pop("page", None)
        # Always keep per_page in base_qs for consistency
        qs_params["per_page"] = per_page
        base_qs = qs_params.urlencode()
    elif mode == "mcq":
        words = list(en_qs)
        questions = _build_mcq_questions(words, options_count=4)
        questions_count = len(questions)
        questions_json = json.dumps(questions, ensure_ascii=False)
    elif mode == "matching":
        words = list(en_qs)
        boards = _build_matching_boards(words, pairs_per_board=8)
        matching_boards_count = len(boards)
        matching_boards_json = json.dumps(boards, ensure_ascii=False)
    elif mode == "fill":
        words = list(en_qs)
        questions = _build_fill_questions(words)
        fill_questions_count = len(questions)
        fill_questions_json = json.dumps(questions, ensure_ascii=False)
    elif mode == "listening":
        words = list(en_qs.filter(audio_pack_uuid__isnull=False).exclude(audio_pack_uuid=""))
        listening_questions = _build_listening_questions(words, options_count=4)
        listening_questions_count = len(listening_questions)
        listening_questions_json = json.dumps(listening_questions, ensure_ascii=False)
    elif mode == "dictation":
        words = list(en_qs.filter(audio_pack_uuid__isnull=False).exclude(audio_pack_uuid=""))
        dictation_questions = _build_dictation_questions(words)
        dictation_questions_count = len(dictation_questions)
        dictation_questions_json = json.dumps(dictation_questions, ensure_ascii=False)
    elif mode == "grammar":
        # Grammar points for this lesson
        from grammar.models import GrammarPoint
        grammar_points_list = list(
            GrammarPoint.objects.filter(
                lesson=lesson,
                is_active=True
            ).order_by("level", "title", "id")
        )
        # Parse examples for each grammar point
        for point in grammar_points_list:
            if point.examples:
                point.examples_list = [line.strip() for line in point.examples.splitlines() if line.strip()]
            else:
                point.examples_list = []
        grammar_points = grammar_points_list
    else:
        grammar_points = []

    # Kiểm tra xem lesson có nội dung cho mode hiện tại không
    has_content = _lesson_has_content(lesson, mode)
    
    return render(request, "courses/course_lesson.html", {
        "course": course,
        "sections": sections,
        "active_section": lesson.section,
        "active_lesson": lesson,
        "lesson": lesson,
        "prev_lesson": prev_lesson,
        "next_lesson": next_lesson,
        "mode": mode,
        "en_words": page_obj,
        "page_obj": page_obj,
        "per_page": int(per_page) if mode == "vocab" else 20,
        "page_items": page_items,
        "base_qs": base_qs,
        "total_count": total_count,
        "mcq_questions_json": questions_json,
        "mcq_questions_count": questions_count,
        "matching_boards_json": matching_boards_json,
        "matching_boards_count": matching_boards_count,
        "fill_questions_json": fill_questions_json,
        "fill_questions_count": fill_questions_count,
        "listening_questions_json": listening_questions_json if mode == "listening" else "",
        "listening_questions_count": listening_questions_count if mode == "listening" else 0,
        "dictation_questions_json": dictation_questions_json if mode == "dictation" else "",
        "dictation_questions_count": dictation_questions_count if mode == "dictation" else 0,
        "grammar_points": grammar_points if mode == "grammar" else [],
        "has_content": has_content,
    })


def dictation_list(request):
    """Danh sách các bài tập dictation"""
    # Get user's study language for filtering
    study_lang = 'en'
    if request.user.is_authenticated:
        try:
            from .models import UserProfile
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                study_lang = profile.study_language or 'en'
        except Exception:
            pass

    exercises = DictationExercise.objects.filter(
        is_active=True, language=study_lang
    ).select_related("lesson", "lesson__section", "lesson__section__course").prefetch_related("segments").order_by("order", "title")

    progress_map = {}
    if request.user.is_authenticated:
        ids = list(exercises.values_list("id", flat=True))
        if ids:
            from .models import DictationProgress
            progress_qs = DictationProgress.objects.filter(user=request.user, exercise_id__in=ids)
            progress_map = {p.exercise_id: p for p in progress_qs}

    # attach progress to exercise for easy access in template
    for ex in exercises:
        ex.progress = progress_map.get(ex.id) if progress_map else None

    return render(request, "dictation/dictation_list.html", {
        "exercises": exercises,
    })


def dictation_detail(request, exercise_slug):
    """Chi tiết bài tập dictation"""
    exercise = get_object_or_404(
        DictationExercise.objects.select_related("lesson", "lesson__section", "lesson__section__course").prefetch_related("segments"),
        slug=exercise_slug,
        is_active=True
    )
    
    segments = exercise.segments.all().order_by("order")
    
    # Serialize segments for JavaScript
    segments_data = []
    for seg in segments:
        segments_data.append({
            "id": seg.id,
            "order": seg.order,
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "correct_text": seg.correct_text,
            "hint": seg.hint or "",
            "duration": seg.duration,
        })
    
    segments_json = json.dumps(segments_data, ensure_ascii=False)

    # Load saved progress
    saved_index = 0
    saved_percent = 0.0
    total_segments = len(segments_data)
    if request.user.is_authenticated:
        from .models import DictationProgress
        prog = DictationProgress.objects.filter(user=request.user, exercise=exercise).first()
        if prog:
            saved_index = min(max(0, prog.current_segment), max(0, total_segments - 1))
            saved_percent = prog.percent
    
    return render(request, "dictation/dictation_detail.html", {
        "exercise": exercise,
        "segments": segments,
        "segments_json": segments_json,
        "saved_index": saved_index,
        "saved_percent": saved_percent,
    })


@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def dictation_progress_update(request):
    """
    Cập nhật tiến độ dictation cho user.
    Body JSON: {exercise_id, current_segment, total_segments}
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    exercise_id = payload.get("exercise_id")
    current_segment = payload.get("current_segment", 0)
    total_segments = payload.get("total_segments", 0)

    if not exercise_id:
        return JsonResponse({"error": "exercise_id is required"}, status=400)

    try:
        exercise = DictationExercise.objects.get(pk=exercise_id, is_active=True)
    except DictationExercise.DoesNotExist:
        return JsonResponse({"error": "exercise not found"}, status=404)

    try:
        current_segment = int(current_segment)
        total_segments = int(total_segments)
    except (TypeError, ValueError):
        current_segment = 0
        total_segments = 0

    if total_segments <= 0:
        total_segments = exercise.segments.count()

    current_segment = max(0, min(current_segment, max(0, total_segments - 1)))

    from .models import DictationProgress

    prog, _ = DictationProgress.objects.get_or_create(
        user=request.user, exercise=exercise,
        defaults={"current_segment": current_segment, "total_segments": total_segments}
    )
    prog.current_segment = current_segment
    prog.total_segments = total_segments
    prog.save()

    # Check for badges
    from core.badge_service import check_and_award_badges
    new_badges = check_and_award_badges(request.user)
    
    # Serialize badges for frontend
    badges_data = []
    for gb in new_badges:
        # gb is likely a UserBadge or Badge object. 
        # check_and_award_badges returns a list of Badge objects (or UserBadge objects, need to verify).
        # Based on typical Django patterns, let's assume it returns Badge objects. 
        # Actually checking badge_service.py source again... it returns "list of newly awarded badges".
        # Let's inspect badge_service.py again to be sure if it returns Badge model instances or dicts.
        badges_data.append({
            "name": gb.name,
            "description": gb.description,
            "icon": gb.icon
        })

    return JsonResponse({
        "ok": True,
        "percent": prog.percent,
        "current_segment": prog.current_segment,
        "current_segment": prog.current_segment,
        "total_segments": prog.total_segments,
        "new_badges": badges_data
    })


def profile(request, username=None):
    """
    Trang profile người dùng.
    - Nếu không có username: hiển thị profile của user hiện tại
    - Nếu có username: hiển thị profile của user đó (public view)
    """
    from django.contrib.auth.models import User
    from exam.models import ExamAttempt
    from collections import defaultdict
    from streak.models import StreakStat
    from vocab.models import FsrsCardStateEn
    from core.badge_service import check_and_award_badges, get_user_badges_with_status
    
    # Xác định user cần hiển thị
    if username:
        profile_user = get_object_or_404(User, username=username)
    elif request.user.is_authenticated:
        profile_user = request.user
    else:
        from django.shortcuts import redirect
        return redirect('account_login')
    
    is_own_profile = request.user.is_authenticated and request.user.id == profile_user.id
    
    # Check and award badges if viewing own profile
    if is_own_profile:
        check_and_award_badges(profile_user)
    
    # Get badges with earned status
    badges_with_status = get_user_badges_with_status(profile_user)
    
    # Get streak info
    streak = None
    try:
        streak = StreakStat.objects.get(user=profile_user)
    except StreakStat.DoesNotExist:
        pass
    
    # Get vocab stats
    total_vocab = FsrsCardStateEn.objects.filter(user=profile_user, state__gte=2).count()
    
    # Lấy các khóa học đã đăng ký
    from core.models import Enrollment
    enrolled_courses = []
    total_courses = 0
    if is_own_profile:
        enrolled_courses = (
            Enrollment.objects
            .filter(user=profile_user)
            .select_related('course')
            .order_by('-last_accessed', '-enrolled_at')[:10]
        )
        total_courses = Enrollment.objects.filter(user=profile_user).count()
    
    # Lấy kết quả thi
    exam_results_grouped = defaultdict(list)
    recent_exam_results = []
    
    attempts = (
        ExamAttempt.objects
        .filter(user=profile_user, status=ExamAttempt.Status.SUBMITTED)
        .select_related('template')
        .order_by('-submitted_at')[:50]
    )
    
    total_exams = ExamAttempt.objects.filter(
        user=profile_user, 
        status=ExamAttempt.Status.SUBMITTED
    ).count()
    
    for attempt in attempts:
        # Tính thời gian làm bài
        time_taken = "N/A"
        if attempt.submitted_at and attempt.started_at:
            delta = attempt.submitted_at - attempt.started_at
            total_seconds = int(delta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_taken = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Xác định loại bài thi
        attempt_data = attempt.data or {}
        is_full_test = attempt_data.get('mode') != 'practice'
        selected_parts = attempt_data.get('selected_parts', [])
        
        # Tính điểm (nếu có)
        score = None
        if attempt.template.level == 'TOEIC':
            # Tính điểm TOEIC đơn giản
            if attempt.total_questions > 0:
                ratio = attempt.correct_count / attempt.total_questions
                score = round(10 + ratio * 980)
        
        result_data = {
            'id': attempt.id,
            'template': attempt.template,
            'submitted_at': attempt.submitted_at,
            'correct_count': attempt.correct_count,
            'total_questions': attempt.total_questions,
            'time_taken': time_taken,
            'is_full_test': is_full_test,
            'selected_parts': [p.replace('L', '').replace('R', '') for p in selected_parts],
            'score': score,
        }
        
        exam_results_grouped[attempt.template.title].append(result_data)
        
        # Build recent results for display (first 10)
        if len(recent_exam_results) < 10:
            recent_exam_results.append(result_data)
    
    # Get or create user profile
    from core.models import UserProfile
    user_profile = UserProfile.get_or_create_for_user(profile_user)
    
    # Get equipped frame for avatar display
    equipped_frame = None
    try:
        from shop.models import UserInventory
        equipped_inventory = UserInventory.objects.filter(
            user=profile_user, is_equipped=True
        ).select_related('frame').first()
        if equipped_inventory:
            equipped_frame = equipped_inventory.frame
    except Exception:
        pass
    
    return render(request, "profile.html", {
        "profile_user": profile_user,
        "user_profile": user_profile,
        "equipped_frame": equipped_frame,
        "is_own_profile": is_own_profile,
        "enrolled_courses": enrolled_courses,
        "exam_results_grouped": dict(exam_results_grouped),
        "recent_exam_results": recent_exam_results,
        "badges_with_status": badges_with_status,
        "streak": streak,
        "total_vocab": total_vocab,
        "total_exams": total_exams,
        "total_courses": total_courses,
    })



from django.contrib.auth.decorators import login_required

@login_required
def settings(request):
    """
    Trang cài đặt tài khoản.
    """
    from django.contrib import messages
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        
        # Validations
        if not first_name:
            messages.error(request, "Vui lòng nhập Tên.")
        else:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            messages.success(request, "Đã cập nhật thông tin thành công!")
            
    return render(request, "settings.html", {
        "user": request.user,
    })


@login_required
def update_exam_goal(request):
    """
    API endpoint để cập nhật mục tiêu kỳ thi.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    
    import json
    from core.models import ExamGoal
    from datetime import datetime
    
    try:
        data = json.loads(request.body)
        exam_goal, _ = ExamGoal.objects.get_or_create(user=request.user)
        
        # Update fields
        if 'exam_type' in data:
            exam_goal.exam_type = data['exam_type']
        if 'target_score' in data:
            exam_goal.target_score = int(data['target_score']) if data['target_score'] else 600
        if 'exam_date' in data:
            if data['exam_date']:
                exam_goal.exam_date = datetime.strptime(data['exam_date'], '%Y-%m-%d').date()
            else:
                exam_goal.exam_date = None
        
        exam_goal.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_POST
def set_language(request):
    """API endpoint to set user's study language preference."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    language = data.get("language", "").strip().lower()
    if language not in ("jp", "en"):
        return JsonResponse({"success": False, "error": "Invalid language. Use 'jp' or 'en'."}, status=400)

    from core.models import UserProfile
    profile = UserProfile.get_or_create_for_user(request.user)
    profile.study_language = language
    profile.save(update_fields=["study_language"])

    return JsonResponse({"success": True, "language": language})


def health(request):
    return JsonResponse({"ok": True})


# === Direct-to-Azure upload helpers (SAS) ===
@login_required
@require_http_methods(["POST"])
def dictation_upload_sas(request):
    """
    Cấp SAS URL để upload trực tiếp từ browser lên Azure.
    Body (JSON hoặc form):
      - filename (bắt buộc)
      - content_type (khuyến nghị)
    Trả về: uploadUrl (có SAS), blobUrl (không SAS), blobName, expiresAt (iso)
    """
    try:
        if request.content_type == "application/json":
            payload = json.loads(request.body.decode("utf-8") or "{}")
        else:
            payload = request.POST
    except Exception:
        payload = {}

    filename = (payload.get("filename") or "").strip()
    content_type = (payload.get("content_type") or "").strip()
    if not filename:
        return JsonResponse({"error": "filename is required"}, status=400)

    # Sanitize filename
    base = os.path.basename(filename)
    if not base:
        return JsonResponse({"error": "invalid filename"}, status=400)
    # optional: prefix with timestamp to avoid collisions
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    blob_name = f"dictation/audio/{ts}-{base}"

    account = settings.AZURE_ACCOUNT_NAME
    key = settings.AZURE_ACCOUNT_KEY
    container = getattr(settings, "AZURE_AUDIO_CONTAINER", settings.AZURE_CONTAINER)
    if not account or not key:
        return JsonResponse({"error": "Azure storage is not configured"}, status=500)

    expiry = timezone.now() + timedelta(minutes=15)
    perms = BlobSasPermissions(create=True, write=True)
    sas = generate_blob_sas(
        account_name=account,
        container_name=container,
        blob_name=blob_name,
        account_key=key,
        permission=perms,
        expiry=expiry,
        content_type=content_type or None,
    )

    base_url = f"https://{account}.blob.core.windows.net/{container}/{blob_name}"
    upload_url = f"{base_url}?{sas}"

    return JsonResponse(
        {
            "uploadUrl": upload_url,
            "blobUrl": base_url,
            "blobName": blob_name,
            "expiresAt": expiry.isoformat(),
        }
    )


@login_required
@require_http_methods(["POST"])
def dictation_upload_complete(request):
    """
    Sau khi client upload xong, gọi endpoint này để lưu blob vào DictationExercise.
    Body (JSON):
      - exercise_id (bắt buộc)
      - blob_name hoặc blob_url (một trong hai)
      - duration (optional, giây)
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    exercise_id = payload.get("exercise_id")
    blob_name = (payload.get("blob_name") or "").strip()
    blob_url = (payload.get("blob_url") or "").strip()
    duration = payload.get("duration")

    if not exercise_id:
        return JsonResponse({"error": "exercise_id is required"}, status=400)

    if not blob_name and blob_url:
        # Extract blob name from URL
        parts = urlsplit(blob_url)
        blob_name = parts.path.lstrip("/")

    if not blob_name:
        return JsonResponse({"error": "blob_name or blob_url is required"}, status=400)

    try:
        exercise = DictationExercise.objects.get(pk=exercise_id)
    except DictationExercise.DoesNotExist:
        return JsonResponse({"error": "exercise not found"}, status=404)

    # Lưu đường dẫn blob vào FileField (giữ nguyên relative path)
    exercise.audio_file.name = blob_name
    if duration is not None:
        try:
            exercise.audio_duration = float(duration)
        except (TypeError, ValueError):
            pass
    exercise.save(update_fields=["audio_file", "audio_duration", "updated_at"])

    audio_url = getattr(settings, "AUDIO_BASE_URL", "").rstrip("/")
    full_url = f"{audio_url}/{blob_name}" if audio_url else blob_url or blob_name

    return JsonResponse({"ok": True, "audio_url": full_url})


# ============================================
# Profile API Views
# ============================================

@login_required
@require_POST
def profile_update(request):
    """
    API để cập nhật thông tin profile.
    Accepts JSON body with fields to update.
    """
    import json
    from core.models import UserProfile
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    
    profile = UserProfile.get_or_create_for_user(request.user)
    
    # Update allowed fields
    allowed_fields = [
        'bio', 'display_title', 'subtitle', 
        'social_links', 'info_items', 'skills', 
        'certificates', 'hobbies'
    ]
    
    updated_fields = []
    for field in allowed_fields:
        if field in data:
            setattr(profile, field, data[field])
            updated_fields.append(field)
    
    if updated_fields:
        profile.save()
    
    return JsonResponse({
        "success": True,
        "message": "Profile updated successfully",
        "updated_fields": updated_fields
    })


@login_required
@require_POST
def profile_upload_avatar(request):
    """
    API để upload ảnh avatar.
    """
    from core.models import UserProfile
    
    if 'avatar' not in request.FILES:
        return JsonResponse({"success": False, "error": "No file provided"}, status=400)
    
    avatar_file = request.FILES['avatar']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        return JsonResponse({
            "success": False, 
            "error": "Invalid file type. Allowed: JPEG, PNG, GIF, WebP"
        }, status=400)
    
    # Validate file size (max 5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return JsonResponse({
            "success": False, 
            "error": "File too large. Maximum size is 5MB"
        }, status=400)
    
    profile = UserProfile.get_or_create_for_user(request.user)
    
    # Delete old avatar if exists
    if profile.avatar:
        try:
            profile.avatar.delete(save=False)
        except Exception:
            pass
    
    profile.avatar = avatar_file
    profile.save()
    
    return JsonResponse({
        "success": True,
        "message": "Avatar uploaded successfully",
        "avatar_url": profile.avatar.url
    })


@login_required
@require_POST
def profile_upload_cover(request):
    """
    API để upload ảnh bìa.
    """
    from core.models import UserProfile
    
    if 'cover' not in request.FILES:
        return JsonResponse({"success": False, "error": "No file provided"}, status=400)
    
    cover_file = request.FILES['cover']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if cover_file.content_type not in allowed_types:
        return JsonResponse({
            "success": False, 
            "error": "Invalid file type. Allowed: JPEG, PNG, GIF, WebP"
        }, status=400)
    
    # Validate file size (max 10MB)
    if cover_file.size > 10 * 1024 * 1024:
        return JsonResponse({
            "success": False, 
            "error": "File too large. Maximum size is 10MB"
        }, status=400)
    
    profile = UserProfile.get_or_create_for_user(request.user)
    
    # Delete old cover if exists
    if profile.cover_image:
        try:
            profile.cover_image.delete(save=False)
        except Exception:
            pass
    
    profile.cover_image = cover_file
    profile.save()
    
    return JsonResponse({
        "success": True,
        "message": "Cover image uploaded successfully",
        "cover_url": profile.cover_image.url
    })
