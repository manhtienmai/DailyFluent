from ninja import Router, Schema
from typing import List, Optional
from django.shortcuts import get_object_or_404

from common.models import QuizResult

router = Router()


# ── Schemas ────────────────────────────────────────────────

class AnswerDetail(Schema):
    q: int
    selected: int
    correct: int
    is_correct: bool


class QuizResultIn(Schema):
    quiz_type: str
    quiz_id: str
    total_questions: int
    correct_count: int
    score: float
    answers_detail: List[AnswerDetail]


class QuizResultOut(Schema):
    id: int
    quiz_type: str
    quiz_id: str
    total_questions: int
    correct_count: int
    score: float
    answers_detail: list
    completed_at: str


# ── Endpoints ──────────────────────────────────────────────

@router.post("/quiz-results", response=QuizResultOut)
def submit_quiz_result(request, payload: QuizResultIn):
    """Submit kết quả bài tập."""
    result = QuizResult.objects.create(
        user=request.user,
        quiz_type=payload.quiz_type,
        quiz_id=payload.quiz_id,
        total_questions=payload.total_questions,
        correct_count=payload.correct_count,
        score=payload.score,
        answers_detail=[a.dict() for a in payload.answers_detail],
    )
    return _to_out(result)


@router.get("/quiz-results", response=List[QuizResultOut])
def list_quiz_results(request, quiz_type: Optional[str] = None, quiz_id: Optional[str] = None):
    """Lấy lịch sử làm bài. Filter bằng quiz_type và/hoặc quiz_id."""
    qs = QuizResult.objects.filter(user=request.user)
    if quiz_type:
        qs = qs.filter(quiz_type=quiz_type)
    if quiz_id:
        qs = qs.filter(quiz_id=quiz_id)
    return [_to_out(r) for r in qs[:20]]


@router.get("/quiz-results/latest", response={200: QuizResultOut, 404: dict})
def latest_quiz_result(request, quiz_type: str, quiz_id: str):
    """Kết quả gần nhất cho 1 quiz cụ thể."""
    result = (
        QuizResult.objects
        .filter(user=request.user, quiz_type=quiz_type, quiz_id=quiz_id)
        .first()
    )
    if not result:
        return 404, {"detail": "No result found"}
    return 200, _to_out(result)


# ── Helpers ────────────────────────────────────────────────

def _to_out(r: QuizResult) -> dict:
    return {
        "id": r.id,
        "quiz_type": r.quiz_type,
        "quiz_id": r.quiz_id,
        "total_questions": r.total_questions,
        "correct_count": r.correct_count,
        "score": r.score,
        "answers_detail": r.answers_detail,
        "completed_at": r.completed_at.isoformat() if r.completed_at else "",
    }
