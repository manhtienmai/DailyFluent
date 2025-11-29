from fsrs import Scheduler, Card, Rating

# Scheduler dùng chung
scheduler = Scheduler()

RATING_MAP = {
    "again": Rating.Again,   # quên / rất khó
    "hard": Rating.Hard,     # khó
    "good": Rating.Good,     # nhớ được
    "easy": Rating.Easy,     # rất dễ
}


def create_new_card_state() -> Card:
    """
    Tạo Card mới cho một từ lần đầu gặp.
    """
    return Card()


def review_card(card_json: str, rating_key: str):
    """
    card_json: chuỗi JSON (Card.to_json())
    rating_key: 'again' / 'hard' / 'good' / 'easy'

    Trả về:
      - new_card_json (string)
      - review_log_json (string)
      - due_dt (datetime, new_card.due)
    """
    rating = RATING_MAP[rating_key]
    card = Card.from_json(card_json)         # card_json là string
    new_card, review_log = scheduler.review_card(card, rating)

    return new_card.to_json(), review_log.to_json(), new_card.due
