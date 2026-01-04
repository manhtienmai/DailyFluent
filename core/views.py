# core/views.py
import json
import random
import re

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import models
from streak.models import StreakStat, DailyActivity
from vocab.models import UserStudySettings

from django.core.paginator import Paginator
from vocab.models import EnglishVocabulary
from .models import Course, Lesson, Section, DictationExercise, DictationSegment


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


def _build_mcq_questions(words: list[EnglishVocabulary], *, options_count: int = 4) -> list[dict]:
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


def _build_matching_boards(words: list[EnglishVocabulary], *, pairs_per_board: int = 8) -> list[dict]:
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


def _build_fill_questions(words: list[EnglishVocabulary]) -> list[dict]:
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


def _build_listening_questions(words: list[EnglishVocabulary], *, options_count: int = 4) -> list[dict]:
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
    - Nếu chưa đăng nhập: hiện landing page với đề thi mới nhất.
    """
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
    
    # Lấy 10 đề thi mới nhất với số lượng người đã làm (cho cả logged in và not logged in)
    latest_exams = list(
        ExamTemplate.objects
        .filter(is_active=True)
        .annotate(
            attempt_count=Count('attempts', filter=Q(attempts__status='submitted'), distinct=True),
            distinct_parts=Count('questions__toeic_part', distinct=True)
        )
        .order_by('-created_at', '-id')[:10]
    )
    
    # Tính comment count (fake: 10% của attempt_count, min 100)
    for exam in latest_exams:
        exam.comment_count = max(100, int(exam.attempt_count * 0.1))

    context = {
        "streak": streak,
        "minutes_today": minutes_today,
        "cards_today": cards_today,
        "new_cards_today": new_cards_today,
        "reviews_today": reviews_today,
        "latest_exams": latest_exams,
        "todo_items": todo_items,
    }
    return render(request, "home.html", context)


def course_list(request):
    courses = Course.objects.filter(is_active=True).order_by("order", "title")
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, course_slug: str):
    from vocab.models import EnglishVocabulary
    
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
    section_ids_with_vocab = set(
        EnglishVocabulary.objects.filter(
            section_ref__in=sections,
            is_active=True
        ).values_list('section_ref_id', flat=True).distinct()
    )

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
    vocab_count = EnglishVocabulary.objects.filter(
        is_active=True, lesson_ref=lesson
    ).count()
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
        return EnglishVocabulary.objects.filter(
            is_active=True, lesson_ref=lesson
        ).exists()
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
        return EnglishVocabulary.objects.filter(
            is_active=True, lesson_ref=lesson
        ).exists()
    return False



def _build_dictation_questions(words: list[EnglishVocabulary]) -> list[dict]:
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
    en_qs = (
        EnglishVocabulary.objects.filter(is_active=True, lesson_ref=lesson)
        .select_related("course_ref", "section_ref", "lesson_ref")
        .prefetch_related("examples")
        .order_by("en_word", "id")
    )
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
    exercises = DictationExercise.objects.filter(is_active=True).select_related("lesson", "lesson__section", "lesson__section__course").prefetch_related("segments").order_by("order", "title")
    
    # Group by lesson if needed
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
    
    return render(request, "dictation/dictation_detail.html", {
        "exercise": exercise,
        "segments": segments,
        "segments_json": segments_json,
    })
