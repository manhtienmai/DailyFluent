"""
Bridge giữa Django và thư viện py-fsrs.
- Lưu state của từng card (Vocabulary) cho từng user
- Dùng Scheduler.review_card để tính lịch ôn tiếp theo
- Anki-like session management với learning queue
"""

import json
from datetime import timedelta
from django.utils import timezone

from fsrs import Card, Rating, Scheduler, State

# Khởi tạo scheduler toàn cục với cấu hình khuyến nghị cho học ngôn ngữ
# 👉 LƯU Ý: learning_steps / relearning_steps dùng timedelta, KHÔNG dùng số int
scheduler = Scheduler(
    # Tăng retention để lịch ôn "chặt" hơn (dễ nhớ hơn, nhưng sẽ ôn nhiều hơn).
    # 0.92 là mức cân bằng; nếu muốn "chắc bài" hơn nữa có thể thử 0.95.
    desired_retention=0.92,
    learning_steps=(timedelta(minutes=1), timedelta(minutes=10)),
    relearning_steps=(timedelta(minutes=10),),
    # Tắt fuzzing để interval hiển thị ổn định (giống Anki-style hơn).
    # Lưu ý: fuzzing giúp giảm "dồn lịch" (bunching) giữa các thẻ, nhưng có thể gây
    # cảm giác khó hiểu khi người học thấy interval trên nút thay đổi liên tục.
    enable_fuzzing=False,
)

# Card states - matching FSRS State enum
CARD_STATE_NEW = 0        # State.New - chưa học bao giờ
CARD_STATE_LEARNING = 1   # State.Learning - đang học (intervals ngắn, cùng session)
CARD_STATE_REVIEW = 2     # State.Review - đã graduated, review bình thường
CARD_STATE_RELEARNING = 3 # State.Relearning - quên, đang học lại

# Threshold: nếu due trong vòng X phút thì coi là "learning" cần show lại trong session
LEARNING_THRESHOLD_MINUTES = 20


def create_new_card_state() -> Card:
    """
    Tạo một Card mới trong FSRS.
    Card mới sẽ due ngay lập tức (now tại UTC).
    """
    return Card()


from .utils import card_data_to_dict

def get_card_state(card_json) -> int:
    """
    Lấy state hiện tại của card.
    Returns: 0=New, 1=Learning, 2=Review, 3=Relearning
    """
    card_data = card_data_to_dict(card_json)
    return card_data.get('state', CARD_STATE_NEW)


def is_learning_card(card_json) -> bool:
    """
    Check xem card có đang trong trạng thái learning/relearning không.
    Những card này cần được show lại trong cùng session.
    """
    state = get_card_state(card_json)
    return state in (CARD_STATE_LEARNING, CARD_STATE_RELEARNING)


def should_requeue_in_session(card_json, due_dt) -> bool:
    """
    Quyết định xem card có nên được thêm lại vào session hiện tại không.
    
    Logic giống Anki:
    - Nếu card đang Learning hoặc Relearning VÀ due trong vòng 20 phút
      → nên show lại trong session
    - Nếu card đã Review (graduated) → không show lại, đợi ngày mai
    """
    state = get_card_state(card_json)
    
    # Chỉ requeue nếu đang trong learning/relearning
    if state not in (CARD_STATE_LEARNING, CARD_STATE_RELEARNING):
        return False
    
    # Check xem due có trong threshold không
    now = timezone.now()
    minutes_until_due = (due_dt - now).total_seconds() / 60
    
    return minutes_until_due <= LEARNING_THRESHOLD_MINUTES


def get_interval_display(card_json, due_dt) -> str:
    """
    Tạo chuỗi hiển thị interval cho UI (giống Anki).
    VD: "1m", "10m", "1d", "4d"
    """
    now = timezone.now()
    delta = due_dt - now
    total_seconds = delta.total_seconds()
    
    if total_seconds < 0:
        return "now"
    elif total_seconds < 60:
        return f"{int(total_seconds)}s"
    elif total_seconds < 3600:
        return f"{int(total_seconds / 60)}m"
    elif total_seconds < 86400:
        return f"{int(total_seconds / 3600)}h"
    else:
        days = total_seconds / 86400
        if days < 30:
            return f"{int(days)}d"
        elif days < 365:
            return f"{int(days / 30)}mo"
        else:
            return f"{days / 365:.1f}y"


def _deserialize_card(card_json) -> Card:
    """Deserialize card_data (dict or str) into an FSRS Card object."""
    if isinstance(card_json, Card):
        return card_json
    if isinstance(card_json, str):
        return Card.from_json(card_json)
    return Card.from_json(json.dumps(card_json))


def review_card(card_json, rating_key: str):
    """
    Chấm điểm 1 card với FSRS.

    Args:
        card_json: card data (dict, JSON string, or Card object)
        rating_key: "again" | "hard" | "good" | "easy"

    Returns:
        tuple: (new_card_data: dict, review_log_data: dict, due_datetime)
    """
    card = _deserialize_card(card_json)

    rating_map = {
        "again": Rating.Again,
        "hard": Rating.Hard,
        "good": Rating.Good,
        "easy": Rating.Easy,
    }
    rating = rating_map.get(rating_key, Rating.Good)

    updated_card, review_log = scheduler.review_card(card, rating)

    # Always return dict (compatible with Django JSONField)
    new_card_data = json.loads(updated_card.to_json())
    review_log_data = json.loads(review_log.to_json())
    due_dt = updated_card.due

    return new_card_data, review_log_data, due_dt


def preview_intervals(card_json) -> dict:
    """
    Preview các interval cho mỗi rating option.
    Dùng để hiển thị trên nút grade giống Anki: "Again (1m)" "Good (10m)" "Easy (4d)"

    Returns:
        dict: {"again": "1m", "hard": "6m", "good": "10m", "easy": "4d"}
    """
    card = _deserialize_card(card_json)

    result = {}
    for rating_key, rating_enum in [
        ("again", Rating.Again),
        ("hard", Rating.Hard),
        ("good", Rating.Good),
        ("easy", Rating.Easy),
    ]:
        preview_card, _ = scheduler.review_card(card, rating_enum)
        result[rating_key] = get_interval_display(None, preview_card.due)

    return result
