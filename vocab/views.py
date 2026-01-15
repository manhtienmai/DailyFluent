import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from django.views.decorators.http import require_POST

from .models import Vocabulary, FixedPhrase, FsrsCardState, UserStudySettings, EnglishVocabulary
from .fsrs_bridge import (
    create_new_card_state, 
    review_card,
    is_learning_card,
    should_requeue_in_session,
    get_card_state,
    preview_intervals,
    get_interval_display,
    CARD_STATE_LEARNING,
    CARD_STATE_RELEARNING,
    CARD_STATE_REVIEW,
    LEARNING_THRESHOLD_MINUTES,
)


def get_or_create_study_settings(user):
    """Get or create study settings for user."""
    settings, _ = UserStudySettings.objects.get_or_create(user=user)
    settings.reset_daily_counts_if_needed()
    return settings


def _build_vocab_queue(user):
    """
    Build Anki-like queue (learning -> review -> new) for a user.
    Shared between flashcard mode and typing mode to keep 1 SRS state per card.
    """
    now = timezone.now()
    study_settings = get_or_create_study_settings(user)

    learning_threshold = now + timedelta(minutes=LEARNING_THRESHOLD_MINUTES)

    # === Fetch all user states ===
    all_user_states = FsrsCardState.objects.filter(
        user=user,
        vocab__is_active=True,
    ).select_related("vocab")

    # === 1. LEARNING / RELEARNING (highest priority) ===
    learning_states = []
    for state in all_user_states.filter(due__lte=learning_threshold):
        if is_learning_card(state.card_json):
            learning_states.append(state)
    learning_states.sort(key=lambda s: s.due)

    # === 2. REVIEW (graduated & due) ===
    review_states = []
    remaining_reviews = study_settings.remaining_reviews()
    if remaining_reviews > 0:
        for state in all_user_states.filter(due__lte=now).order_by("due"):
            if state in learning_states:
                continue
            if not is_learning_card(state.card_json):
                review_states.append(state)
                if len(review_states) >= remaining_reviews:
                    break

    # === 3. NEW (no FsrsCardState yet) ===
    new_states = []
    remaining_new = study_settings.remaining_new()
    if remaining_new > 0:
        existing_vocab_ids = FsrsCardState.objects.filter(
            user=user
        ).values_list("vocab_id", flat=True)

        new_vocab_qs = (
            Vocabulary.objects
            .filter(is_active=True)
            .exclude(id__in=existing_vocab_ids)
            .order_by("created_at")[:remaining_new]
        )

        for vocab in new_vocab_qs:
            card = create_new_card_state()
            state = FsrsCardState.objects.create(
                user=user,
                vocab=vocab,
                card_json=card.to_dict(),
                due=card.due,
            )
            new_states.append(state)

    states = learning_states + review_states + new_states

    stats = {
        "learning_count": len(learning_states),
        "review_count": len(review_states),
        "new_count": len(new_states),
        "total": len(states),
        "daily_new_limit": study_settings.new_cards_per_day,
        "daily_new_done": study_settings.new_cards_today,
        "daily_review_limit": study_settings.reviews_per_day,
        "daily_review_done": study_settings.reviews_today,
    }

    return states, stats


def _pagination_items(paginator, current_page: int, window: int = 2):
    """
    Build a compact page list with ellipses (None) for UI.
    Example: [1, None, 4, 5, 6, None, 20]
    """
    total = paginator.num_pages
    if total <= 9:
        return list(range(1, total + 1))

    items = [1]
    start = max(2, current_page - window)
    end = min(total - 1, current_page + window)

    if start > 2:
        items.append(None)

    for n in range(start, end + 1):
        items.append(n)

    if end < total - 1:
        items.append(None)

    items.append(total)
    return items


@login_required
def vocab_list(request):
    """
    Trang danh sách từ vựng (dùng để xem và chuyển sang flashcard).
    """
    # Sort by insertion/created order (newest -> oldest)
    qs = Vocabulary.objects.filter(is_active=True)

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(jp_kana__icontains=q) | Q(jp_kanji__icontains=q))

    qs = qs.order_by("-created_at", "-id")
    total_count = qs.count()

    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(page_number)
    page_items = _pagination_items(paginator, page_obj.number)
    qs_params = request.GET.copy()
    qs_params.pop("page", None)
    base_qs = qs_params.urlencode()

    # AJAX pagination: return HTML fragments for table + pagination
    if request.GET.get("partial") == "1":
        rows_html = render_to_string("vocab/partials/vocab_list_rows.html", {"words": page_obj})
        range_text = f"Hiển thị {page_obj.start_index()}-{page_obj.end_index()} / {total_count}"
        pagination_html = render_to_string("vocab/partials/vocab_list_pagination.html", {
            "page_obj": page_obj,
            "page_items": page_items,
            "base_qs": base_qs,
            "range_text": range_text,
        })
        return JsonResponse({
            "rows_html": rows_html,
            "pagination_html": pagination_html,
            "range_text": range_text,
        })

    return render(request, "vocab/list.html", {
        "words": page_obj,  # keep template loop unchanged; Page is iterable
        "page_obj": page_obj,
        "paginator": paginator,
        "total_count": total_count,
        "page_items": page_items,
        "q": q,
        "base_qs": base_qs,
    })


@login_required
def phrase_list(request):
    """
    Trang danh sách cụm từ cố định.
    """
    qs = FixedPhrase.objects.filter(is_active=True)
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(jp_text__icontains=q) | Q(jp_kana__icontains=q))

    qs = qs.order_by("-created_at", "-id")
    total_count = qs.count()

    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(page_number)
    page_items = _pagination_items(paginator, page_obj.number)
    qs_params = request.GET.copy()
    qs_params.pop("page", None)
    base_qs = qs_params.urlencode()

    return render(request, "vocab/phrase_list.html", {
        "phrases": page_obj,
        "page_obj": page_obj,
        "page_items": page_items,
        "total_count": total_count,
        "q": q,
        "base_qs": base_qs,
    })


@login_required
def english_list(request):
    """
    Danh sách từ vựng tiếng Anh (basic list + search + pagination).
    """
    qs = EnglishVocabulary.objects.filter(is_active=True)

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(en_word__icontains=q)
            | Q(phonetic__icontains=q)
            | Q(vi_meaning__icontains=q)
            | Q(en_definition__icontains=q)
        )

    qs = qs.order_by("en_word", "id")
    total_count = qs.count()

    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(page_number)
    page_items = _pagination_items(paginator, page_obj.number)
    qs_params = request.GET.copy()
    qs_params.pop("page", None)
    base_qs = qs_params.urlencode()

    return render(request, "vocab/english_list.html", {
        "words": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "total_count": total_count,
        "page_items": page_items,
        "q": q,
        "base_qs": base_qs,
    })


@login_required
def flashcard_session(request):
    """
    Tạo một session flashcard cho user - Anki-style:
    
    Queue order (giống Anki):
    1. Learning cards (đang học, interval ngắn < 20 phút)
    2. Review cards (đến hạn ôn tập)
    3. New cards (từ mới chưa học)
    
    Daily limits:
    - new_cards_per_day: giới hạn từ mới
    - reviews_per_day: giới hạn ôn tập
    """
    states, stats = _build_vocab_queue(request.user)

    # Giới hạn mỗi lần học flashcard tối đa 20 thẻ để phiên ngắn gọn
    states = states[:20]

    # Build card data with intervals preview
    cards_data = []
    for state in states:
        intervals = preview_intervals(state.card_json)
        card_state = get_card_state(state.card_json)
        
        cards_data.append({
            "state_id": state.id,
            "vocab_id": state.vocab.id,
            "jp_kana": state.vocab.jp_kana,
            "jp_kanji": state.vocab.jp_kanji or "",
            "sino_vi": state.vocab.sino_vi or "",
            "vi_meaning": state.vocab.vi_meaning,
            "example_jp": state.vocab.example_jp or "",
            "example_vi": state.vocab.example_vi or "",
            "card_state": card_state,  # 0=new, 1=learning, 2=review, 3=relearning
            "intervals": intervals,  # {"again": "1m", "good": "10m", ...}
        })
    
    return render(request, "vocab/flashcards.html", {
        "states": states,
        # Must be valid JSON for JSON.parse() in the template (double quotes, etc.)
        "cards_data_json": json.dumps(cards_data),
        "stats": stats,
    })


@login_required
def typing_review(request):
    """
    Mode gõ Hiragana: sử dụng chung SRS state (FSRS) với flashcard.
    """
    states, stats = _build_vocab_queue(request.user)

    cards_data = []
    for state in states:
        cards_data.append({
            "state_id": state.id,
            "vocab_id": state.vocab.id,
            "kanji": state.vocab.jp_kanji or "",
            "hiragana": state.vocab.jp_kana,
            "sino_vi": state.vocab.sino_vi or "",
            "meaning": state.vocab.vi_meaning,
            "total_reviews": state.total_reviews,
            "card_state": get_card_state(state.card_json),
        })

    return render(request, "vocab/type_review.html", {
        "cards_data_json": json.dumps(cards_data),
        "stats": stats,
        "total_count": len(cards_data),
    })


@login_required
def vocab_detail(request, vocab_id: int):
    """
    Read-only word detail page.
    Open this in a new tab from flashcard/typing so the SRS flow is not interrupted.
    """
    qs = Vocabulary.objects.all()
    if not request.user.is_staff:
        qs = qs.filter(is_active=True)

    vocab = get_object_or_404(qs, id=vocab_id)

    examples = list(vocab.examples.all().order_by("order", "id").values("jp", "vi"))
    if not examples and (vocab.example_jp or vocab.example_vi):
        # Backwards-compatible: split legacy example fields into a list
        jp_lines = [s.strip() for s in (vocab.example_jp or "").splitlines() if s.strip()]
        vi_lines = [s.strip() for s in (vocab.example_vi or "").splitlines() if s.strip()]
        n = max(len(jp_lines), len(vi_lines), 1)
        for i in range(n):
            examples.append({
                "jp": jp_lines[i] if i < len(jp_lines) else "",
                "vi": vi_lines[i] if i < len(vi_lines) else "",
            })

    return render(request, "vocab/detail.html", {
        "vocab": vocab,
        "examples": examples,
    })

@login_required
def vocab_progress(request):
    """
    Trang xem tiến độ học từ vựng của user.
    Sử dụng FSRS state để phân loại card chính xác hơn.
    """
    user = request.user
    states = (
        FsrsCardState.objects
        .filter(user=user, vocab__is_active=True)
        .select_related("vocab")
        .order_by("due")
    )

    total_cards = states.count()
    
    # Phân loại theo FSRS state thay vì đếm reviews
    new_cards = 0
    learning_cards = 0
    review_cards = 0
    
    for s in states:
        card_state = get_card_state(s.card_json)
        if s.total_reviews == 0:
            new_cards += 1
        elif card_state in (CARD_STATE_LEARNING, CARD_STATE_RELEARNING):
            learning_cards += 1
        else:
            review_cards += 1
    
    # Mature = đã review nhiều lần và có stability cao
    mature_cards = states.filter(total_reviews__gte=5, successful_reviews__gte=3).count()

    avg_progress = 0
    if total_cards > 0:
        avg_progress = int(sum(s.progress_percent for s in states) / total_cards)

    # Memory quality: how many reviewed cards are above a recall threshold (70%)
    reviewed_states = [s for s in states if s.total_reviews > 0]
    memory_percent = 0
    avg_retention = 0
    if reviewed_states:
        remembered = sum(1 for s in reviewed_states if s.progress_percent >= 70)
        memory_percent = int(remembered * 100 / len(reviewed_states))
        avg_retention = int(sum(s.progress_percent for s in reviewed_states) / len(reviewed_states))

    today = timezone.localdate()
    cards_info = []
    for s in states:
        d = s.due.date()
        delta_days = (d - today).days
        if delta_days < 0:
            due_label = f"Quá hạn {-delta_days} ngày"
            due_status = "overdue"
        elif delta_days == 0:
            due_label = "Hôm nay"
            due_status = "today"
        else:
            due_label = f"Còn {delta_days} ngày"
            due_status = "future"

        cards_info.append({
            "state": s,
            "vocab": s.vocab,
            "progress": s.progress_percent,
            "due_label": due_label,
            "due_status": due_status,
            "card_state": get_card_state(s.card_json),
        })

    # Get study settings
    study_settings = get_or_create_study_settings(user)

    context = {
        "cards_info": cards_info,
        "summary": {
            "total": total_cards,
            "new": new_cards,
            "learning": learning_cards,
            "review": review_cards,
            "mature": mature_cards,
            "avg_progress": avg_progress,
            "memory_percent": memory_percent,
            "avg_retention": avg_retention,
        },
        "study_settings": study_settings,
    }
    return render(request, "vocab/progress.html", context)


@login_required
def study_status(request):
    """
    Trang liệt kê các từ: chưa học, đang học, đang ôn, đã thuộc (mature).
    """
    user = request.user

    states = (
        FsrsCardState.objects
        .filter(user=user, vocab__is_active=True)
        .select_related("vocab")
    )

    learning_states = []
    review_states = []
    mature_states = []

    for s in states:
        card_state = get_card_state(s.card_json)
        if s.total_reviews == 0:
            # sẽ gom vào "chưa học" thông qua vocab thiếu state
            continue
        elif card_state in (CARD_STATE_LEARNING, CARD_STATE_RELEARNING):
            learning_states.append(s)
        else:
            # review hoặc graduated
            if s.total_reviews >= 5 and s.successful_reviews >= 3:
                mature_states.append(s)
            else:
                review_states.append(s)

    # Vocab chưa có FsrsCardState => chưa học
    existing_vocab_ids = states.values_list("vocab_id", flat=True)
    not_started = Vocabulary.objects.filter(
        is_active=True
    ).exclude(id__in=existing_vocab_ids).order_by("-created_at")[:200]

    context = {
        "learning_states": learning_states,
        "review_states": review_states,
        "mature_states": mature_states,
        "not_started": not_started,
    }
    return render(request, "vocab/study_status.html", context)


@login_required
@require_POST
def flashcard_grade(request):
    """
    API chấm điểm 1 card - Anki-style với re-queue support.
    
    Returns JSON:
    - status: "ok"
    - requeue: true/false - card có cần show lại trong session không
    - requeue_delay_ms: milliseconds đợi trước khi show lại
    - new_intervals: preview intervals cho lần tiếp
    - card_state: trạng thái mới của card (0-3)
    """
    state_id = request.POST.get("state_id")
    rating_key = request.POST.get("rating")
    is_new_card = request.POST.get("is_new") == "true"

    if not state_id or rating_key not in ("again", "hard", "good", "easy"):
        return HttpResponseBadRequest("Invalid data")

    try:
        state = FsrsCardState.objects.select_related("vocab").get(
            id=state_id,
            user=request.user,
        )
    except FsrsCardState.DoesNotExist:
        return HttpResponseBadRequest("State not found")

    # Gọi FSRS để review
    new_card_json, _review_log_json, due_dt = review_card(
        state.card_json,
        rating_key,
    )

    # Cập nhật state
    state.card_json = new_card_json
    state.due = due_dt
    state.last_reviewed = timezone.now()

    # Cập nhật thống kê
    state.total_reviews += 1
    if rating_key in ("good", "easy"):
        state.successful_reviews += 1
    state.last_rating = rating_key

    state.save()
    
    # Update daily counters
    study_settings = get_or_create_study_settings(request.user)
    if is_new_card and state.total_reviews == 1:
        # First review of a new card
        study_settings.new_cards_today += 1
        study_settings.save(update_fields=['new_cards_today'])
    else:
        study_settings.reviews_today += 1
        study_settings.save(update_fields=['reviews_today'])
    
    # === ANKI-LIKE RE-QUEUE LOGIC ===
    # Check if card should be shown again in this session
    should_requeue = should_requeue_in_session(new_card_json, due_dt)
    
    # Calculate delay before showing again (in milliseconds)
    requeue_delay_ms = 0
    if should_requeue:
        now = timezone.now()
        delay_seconds = max(0, (due_dt - now).total_seconds())
        requeue_delay_ms = int(delay_seconds * 1000)
        # Minimum 1 second delay để tránh show quá nhanh
        requeue_delay_ms = max(1000, requeue_delay_ms)
    
    # Preview new intervals for next review
    new_intervals = preview_intervals(new_card_json)
    card_state = get_card_state(new_card_json)

    return JsonResponse({
        "status": "ok",
        "requeue": should_requeue,
        "requeue_delay_ms": requeue_delay_ms,
        "new_intervals": new_intervals,
        "card_state": card_state,
        "due_display": get_interval_display(new_card_json, due_dt),
    })


@login_required
def vocab_games(request):
    """
    Trang trung tâm trò chơi từ vựng - hiển thị các game học từ vựng.
    """
    user = request.user
    
    # Lấy thống kê SRS
    study_settings = get_or_create_study_settings(user)
    states, stats = _build_vocab_queue(user)
    
    # Đếm từ sẵn sàng để học
    ready_count = stats.get('total', 0)
    
    # Danh sách các game
    games = [
        {
            "id": "flashcard",
            "name": "Flashcard",
            "description": "Lật thẻ học từ vựng",
            "icon": "cards",
            "color": "#6366F1",  # Indigo
            "url": "vocab:flashcards",
            "coins": 5,
        },
        {
            "id": "quiz",
            "name": "Trắc nghiệm",
            "description": "Chọn đáp án đúng",
            "icon": "quiz",
            "color": "#F97316",  # Orange
            "url": "vocab:flashcards",  # Link to flashcards for now
            "coins": 10,
        },
        {
            "id": "match",
            "name": "Nối từ với nghĩa",
            "description": "Ghép đôi từ vựng và nghĩa",
            "icon": "match",
            "color": "#10B981",  # Green
            "url": "vocab:flashcards",
            "coins": 10,
        },
        {
            "id": "typing",
            "name": "Gõ từ vựng",
            "description": "Nhìn nghĩa và gõ từ tiếng...",
            "icon": "typing",
            "color": "#EC4899",  # Pink
            "url": "vocab:typing",
            "coins": 10,
        },
        {
            "id": "listen",
            "name": "Nghe viết",
            "description": "Nghe phát âm và viết từ",
            "icon": "headphones",
            "color": "#14B8A6",  # Teal
            "url": "vocab:flashcards",
            "coins": 15,
        },
        {
            "id": "mixed",
            "name": "Tổng hợp",
            "description": "Random trắc nghiệm...",
            "icon": "shuffle",
            "color": "#F43F5E",  # Rose
            "url": "vocab:flashcards",
            "coins": 20,
            "hot": True,
        },
    ]
    
    context = {
        "games": games,
        "ready_count": ready_count,
        "stats": stats,
        "study_settings": study_settings,
    }
    return render(request, "vocab/games.html", context)


def _build_english_vocab_queue(user):
    """
    Build Anki-like queue for English vocabulary.
    Similar to _build_vocab_queue but uses EnglishVocabulary and FsrsCardStateEn.
    """
    from .models import EnglishVocabulary, FsrsCardStateEn
    
    now = timezone.now()
    study_settings = get_or_create_study_settings(user)
    learning_threshold = now + timedelta(minutes=LEARNING_THRESHOLD_MINUTES)

    # Fetch all user states for English
    all_user_states = FsrsCardStateEn.objects.filter(
        user=user,
        vocab__is_active=True,
    ).select_related("vocab")

    # 1. LEARNING / RELEARNING (highest priority)
    learning_states = []
    for state in all_user_states.filter(due__lte=learning_threshold):
        if is_learning_card(state.card_json):
            learning_states.append(state)
    learning_states.sort(key=lambda s: s.due)

    # 2. REVIEW (graduated & due)
    review_states = []
    remaining_reviews = study_settings.remaining_reviews()
    if remaining_reviews > 0:
        for state in all_user_states.filter(due__lte=now).order_by("due"):
            if state in learning_states:
                continue
            if not is_learning_card(state.card_json):
                review_states.append(state)
                if len(review_states) >= remaining_reviews:
                    break

    # 3. NEW (no FsrsCardStateEn yet)
    new_states = []
    remaining_new = study_settings.remaining_new()
    if remaining_new > 0:
        existing_vocab_ids = FsrsCardStateEn.objects.filter(
            user=user
        ).values_list("vocab_id", flat=True)

        new_vocab_qs = (
            EnglishVocabulary.objects
            .filter(is_active=True)
            .exclude(id__in=existing_vocab_ids)
            .order_by("import_order", "id")[:remaining_new]
        )

        for vocab in new_vocab_qs:
            card = create_new_card_state()
            state = FsrsCardStateEn.objects.create(
                user=user,
                vocab=vocab,
                card_json=card.to_dict(),
                due=card.due,
            )
            new_states.append(state)

    states = learning_states + review_states + new_states

    stats = {
        "learning_count": len(learning_states),
        "review_count": len(review_states),
        "new_count": len(new_states),
        "total": len(states),
        "daily_new_limit": study_settings.new_cards_per_day,
        "daily_new_done": study_settings.new_cards_today,
        "daily_review_limit": study_settings.reviews_per_day,
        "daily_review_done": study_settings.reviews_today,
    }

    return states, stats


@login_required
def english_flashcard_session(request):
    """
    Flashcard session for English vocabulary - Anki-style with FSRS.
    """
    states, stats = _build_english_vocab_queue(request.user)

    # Limit to 20 cards per session
    states = states[:20]

    # Build card data with intervals preview
    cards_data = []
    for state in states:
        intervals = preview_intervals(state.card_json)
        card_state = get_card_state(state.card_json)
        
        # Get first example if available
        example = state.vocab.examples.first()
        
        cards_data.append({
            "state_id": state.id,
            "vocab_id": state.vocab.id,
            "en_word": state.vocab.en_word,
            "phonetic": state.vocab.phonetic or "",
            "vi_meaning": state.vocab.vi_meaning,
            "en_definition": state.vocab.en_definition or "",
            "example_en": example.en if example else (state.vocab.example_en or ""),
            "example_vi": example.vi if example else (state.vocab.example_vi or ""),
            "card_state": card_state,
            "intervals": intervals,
        })
    
    return render(request, "vocab/english_flashcards.html", {
        "states": states,
        "cards_data_json": json.dumps(cards_data),
        "stats": stats,
    })


@login_required
@require_POST
def english_flashcard_grade(request):
    """
    API grading for English flashcard - same logic as Japanese.
    """
    from .models import FsrsCardStateEn
    
    state_id = request.POST.get("state_id")
    rating_key = request.POST.get("rating")
    is_new_card = request.POST.get("is_new") == "true"

    if not state_id or rating_key not in ("again", "hard", "good", "easy"):
        return HttpResponseBadRequest("Invalid data")

    try:
        state = FsrsCardStateEn.objects.select_related("vocab").get(
            id=state_id,
            user=request.user,
        )
    except FsrsCardStateEn.DoesNotExist:
        return HttpResponseBadRequest("State not found")

    # Review with FSRS
    new_card_json, _review_log_json, due_dt = review_card(
        state.card_json,
        rating_key,
    )

    # Update state
    state.card_json = new_card_json
    state.due = due_dt
    state.last_reviewed = timezone.now()

    # Update stats
    state.total_reviews += 1
    if rating_key in ("good", "easy"):
        state.successful_reviews += 1
    state.last_rating = rating_key
    state.save()
    
    # Update daily counters
    study_settings = get_or_create_study_settings(request.user)
    if is_new_card and state.total_reviews == 1:
        study_settings.new_cards_today += 1
        study_settings.save(update_fields=['new_cards_today'])
    else:
        study_settings.reviews_today += 1
        study_settings.save(update_fields=['reviews_today'])
    
    # Requeue logic
    should_requeue = should_requeue_in_session(new_card_json, due_dt)
    
    requeue_delay_ms = 0
    if should_requeue:
        now = timezone.now()
        delay_seconds = max(0, (due_dt - now).total_seconds())
        requeue_delay_ms = int(delay_seconds * 1000)
        requeue_delay_ms = max(1000, requeue_delay_ms)
    
    new_intervals = preview_intervals(new_card_json)
    card_state = get_card_state(new_card_json)

    return JsonResponse({
        "status": "ok",
        "requeue": should_requeue,
        "requeue_delay_ms": requeue_delay_ms,
        "new_intervals": new_intervals,
        "card_state": card_state,
        "due_display": get_interval_display(new_card_json, due_dt),
    })


# ========================================
# Standalone Vocabulary Games
# ========================================

def _get_game_vocabulary(user, count=20):
    """
    Get vocabulary for games - using English vocabulary from user's SRS queue.
    Returns list of EnglishVocabulary objects.
    """
    from .models import EnglishVocabulary, FsrsCardStateEn
    
    # First try to get from user's SRS queue (words they're learning)
    user_vocab_ids = FsrsCardStateEn.objects.filter(
        user=user,
        vocab__is_active=True,
    ).values_list("vocab_id", flat=True)[:count * 2]  # Get extra for variety
    
    vocab_list = list(EnglishVocabulary.objects.filter(
        id__in=user_vocab_ids,
        is_active=True,
    ).order_by("?")[:count])  # Random order
    
    # If not enough, supplement with random active vocabulary
    if len(vocab_list) < count:
        existing_ids = [v.id for v in vocab_list]
        additional = EnglishVocabulary.objects.filter(
            is_active=True,
        ).exclude(id__in=existing_ids).order_by("?")[:count - len(vocab_list)]
        vocab_list.extend(additional)
    
    return vocab_list


def _generate_mcq_wrong_options(correct_word, all_vocab, count=3):
    """Generate wrong options for MCQ from vocabulary pool."""
    import random
    wrong = [v for v in all_vocab if v.en_word.lower() != correct_word.lower()]
    random.shuffle(wrong)
    return wrong[:count]


@login_required
def game_mcq(request):
    """
    Multiple Choice Quiz - Show meaning, choose correct word.
    """
    import random
    
    vocab_list = _get_game_vocabulary(request.user, count=15)
    
    if not vocab_list:
        return render(request, "vocab/games/mcq.html", {"questions": []})
    
    # Generate MCQ questions
    questions = []
    for vocab in vocab_list:
        # Get wrong options from pool
        wrong_options = _generate_mcq_wrong_options(vocab.en_word, vocab_list, count=3)
        
        options = [vocab.en_word] + [w.en_word for w in wrong_options]
        random.shuffle(options)
        
        questions.append({
            "id": vocab.id,
            "question": vocab.vi_meaning,
            "hint": vocab.en_definition or "",
            "answer": vocab.en_word,
            "options": options,
            "phonetic": vocab.phonetic or "",
        })
    
    return render(request, "vocab/games/mcq.html", {
        "questions": questions,
        "questions_json": json.dumps(questions),
        "total_count": len(questions),
    })


@login_required
def game_matching(request):
    """
    Matching Game - Match words with meanings.
    """
    import random
    
    vocab_list = _get_game_vocabulary(request.user, count=8)  # 8 pairs = 16 tiles
    
    if not vocab_list:
        return render(request, "vocab/games/matching.html", {"pairs": []})
    
    # Generate matching pairs
    pairs = []
    for i, vocab in enumerate(vocab_list):
        pairs.append({
            "id": vocab.id,
            "word": vocab.en_word,
            "meaning": vocab.vi_meaning,
            "pair_id": i,
        })
    
    # Create tiles
    tiles = []
    for pair in pairs:
        tiles.append({"text": pair["word"], "pair_id": pair["pair_id"], "type": "word"})
        tiles.append({"text": pair["meaning"], "pair_id": pair["pair_id"], "type": "meaning"})
    
    random.shuffle(tiles)
    
    return render(request, "vocab/games/matching.html", {
        "pairs": pairs,
        "tiles": tiles,
        "tiles_json": json.dumps(tiles),
        "total_pairs": len(pairs),
    })


@login_required
def game_listening(request):
    """
    Listening Game - Listen to pronunciation and choose correct word.
    """
    import random
    from .models import EnglishVocabulary
    
    # Get vocabulary with audio
    vocab_with_audio = EnglishVocabulary.objects.filter(
        is_active=True,
    ).exclude(audio_pack_uuid="").exclude(audio_pack_uuid__isnull=True).order_by("?")[:15]
    
    vocab_list = list(vocab_with_audio)
    
    if not vocab_list:
        return render(request, "vocab/games/listening.html", {"questions": []})
    
    # Generate listening questions
    questions = []
    for vocab in vocab_list:
        # Get wrong options
        wrong_options = _generate_mcq_wrong_options(vocab.en_word, vocab_list, count=3)
        
        options = [vocab.en_word] + [w.en_word for w in wrong_options]
        random.shuffle(options)
        
        questions.append({
            "id": vocab.id,
            "answer": vocab.en_word,
            "options": options,
            "phonetic": vocab.phonetic or "",
            "meaning": vocab.vi_meaning,
            "audio_pack_uuid": vocab.audio_pack_uuid,
        })
    
    return render(request, "vocab/games/listening.html", {
        "questions": questions,
        "questions_json": json.dumps(questions),
        "total_count": len(questions),
    })


@login_required
def game_fill(request):
    """
    Fill Game - See meaning (or definition), type the word.
    """
    vocab_list = _get_game_vocabulary(request.user, count=15)
    
    if not vocab_list:
        return render(request, "vocab/games/fill.html", {"questions": []})
    
    questions = []
    for vocab in vocab_list:
        questions.append({
            "id": vocab.id,
            "meaning": vocab.vi_meaning,
            "definition": vocab.en_definition or "",
            "answer": vocab.en_word.lower().strip(),
            "display_answer": vocab.en_word,
            "phonetic": vocab.phonetic or "",
        })
    
    return render(request, "vocab/games/fill.html", {
        "questions": questions,
        "questions_json": json.dumps(questions),
        "total_count": len(questions),
    })


@login_required
def game_dictation(request):
    """
    Dictation Game - Listen to audio and type the word.
    """
    from .models import EnglishVocabulary
    
    # Get vocabulary with audio
    vocab_with_audio = EnglishVocabulary.objects.filter(
        is_active=True,
    ).exclude(audio_pack_uuid="").exclude(audio_pack_uuid__isnull=True).order_by("?")[:15]
    
    vocab_list = list(vocab_with_audio)
    
    if not vocab_list:
        return render(request, "vocab/games/dictation.html", {"questions": []})
    
    questions = []
    for vocab in vocab_list:
        questions.append({
            "id": vocab.id,
            "answer": vocab.en_word.lower().strip(),
            "display_answer": vocab.en_word,
            "phonetic": vocab.phonetic or "",
            "meaning": vocab.vi_meaning,
            "audio_pack_uuid": vocab.audio_pack_uuid,
        })
    
    return render(request, "vocab/games/dictation.html", {
        "questions": questions,
        "questions_json": json.dumps(questions),
        "total_count": len(questions),
    })