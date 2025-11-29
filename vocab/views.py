from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from django.views.decorators.http import require_POST

from .models import Vocabulary, FsrsCardState
from .fsrs_bridge import create_new_card_state, review_card


@login_required
def vocab_list(request):
    """
    Trang danh sách từ vựng (dùng để xem và chuyển sang flashcard).
    """
    words = Vocabulary.objects.filter(is_active=True).order_by("jp_kana")
    return render(request, "vocab/list.html", {"words": words})


@login_required
def flashcard_session(request):
    """
    Tạo một session flashcard cho user:
      - Lấy các card đến hạn (due <= now)
      - Bổ sung một số card mới (chưa có state) nếu chưa đủ số lượng
    """
    user = request.user
    now = timezone.now()
    max_cards = 20

    # Card đã có state và đến hạn
    due_states_qs = (
        FsrsCardState.objects
        .filter(user=user, due__lte=now, vocab__is_active=True)
        .select_related("vocab")
        .order_by("due")
    )
    due_states = list(due_states_qs[:max_cards])

    # Nếu chưa đủ, bổ sung card mới
    states = due_states.copy()
    remaining = max_cards - len(states)
    if remaining > 0:
        existing_vocab_ids = FsrsCardState.objects.filter(
            user=user
        ).values_list("vocab_id", flat=True)

        new_vocab_qs = (
            Vocabulary.objects
            .filter(is_active=True)
            .exclude(id__in=existing_vocab_ids)
            .order_by("created_at")[:remaining]
        )

        for vocab in new_vocab_qs:
            card = create_new_card_state()
            card_json = card.to_json()
            due_dt = card.due

            state = FsrsCardState.objects.create(
                user=user,
                vocab=vocab,
                card_json=card_json,
                due=due_dt,
            )
            states.append(state)

    return render(request, "vocab/flashcards.html", {
        "states": states,
    })

@login_required
def vocab_progress(request):
    """
    Trang xem tiến độ học từ vựng của user.
    """
    user = request.user
    states = (
        FsrsCardState.objects
        .filter(user=user, vocab__is_active=True)
        .select_related("vocab")
        .order_by("due")
    )

    total_cards = states.count()
    new_cards = states.filter(total_reviews=0).count()
    learning_cards = states.filter(total_reviews__gt=0, total_reviews__lt=5).count()
    mature_cards = states.filter(total_reviews__gte=5, successful_reviews__gte=3).count()

    avg_progress = 0
    if total_cards > 0:
        avg_progress = int(sum(s.progress_percent for s in states) / total_cards)

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
        })

    context = {
        "cards_info": cards_info,
        "summary": {
            "total": total_cards,
            "new": new_cards,
            "learning": learning_cards,
            "mature": mature_cards,
            "avg_progress": avg_progress,
        },
    }
    return render(request, "vocab/progress.html", context)




@login_required
@require_POST
def flashcard_grade(request):
    """
    API chấm điểm 1 card:
      - nhận state_id + rating ("again"/"hard"/"good"/"easy")
      - dùng FSRS cập nhật state + due mới
    """
    state_id = request.POST.get("state_id")
    rating_key = request.POST.get("rating")

    if not state_id or rating_key not in ("again", "hard", "good", "easy"):
        return HttpResponseBadRequest("Invalid data")

    try:
        state = FsrsCardState.objects.select_related("vocab").get(
            id=state_id,
            user=request.user,
        )
    except FsrsCardState.DoesNotExist:
        return HttpResponseBadRequest("State not found")

    # Gọi FSRS, giờ trả thêm due_dt
    new_card_json, _review_log_json, due_dt = review_card(
        state.card_json,
        rating_key,
    )

    state.card_json = new_card_json   # string
    state.due = due_dt                # datetime UTC từ FSRS
    state.last_reviewed = timezone.now()

    # Cập nhật thống kê
    state.total_reviews += 1
    if rating_key in ("good", "easy"):
        state.successful_reviews += 1
    state.last_rating = rating_key

    state.save()

    return JsonResponse({"status": "ok"})
