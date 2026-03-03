"""Grammar API — points, exercises, books, flashcards (FSRS)."""

from ninja import Router, Schema
from typing import List, Optional

router = Router()


# ── FSRS Flashcard Endpoints ─────────────────────────────────

@router.get("/flashcards")
def grammar_flashcards(request, level: str = None):
    """Get grammar flashcard session (FSRS-based)."""
    from grammar.grammar_fsrs_service import GrammarFsrsService
    cards, stats = GrammarFsrsService.get_flashcard_session(
        user=request.user,
        level=level,
    )
    return {"cards": cards, "stats": stats}


class GradeInput(Schema):
    grammar_point_id: int
    rating: str  # again, hard, good, easy


@router.post("/flashcards/grade")
def grammar_flashcard_grade(request, payload: GradeInput):
    """Grade a grammar flashcard."""
    from grammar.grammar_fsrs_service import GrammarFsrsService
    result = GrammarFsrsService.grade_card(
        user=request.user,
        grammar_point_id=payload.grammar_point_id,
        rating=payload.rating,
    )
    if not result.get('success'):
        return {"error": result.get('error', 'Unknown error')}
    return result


@router.get("", response=list)
@router.get("/points", response=list)
def list_grammar(request, level: str = None, book_slug: str = None):
    """List grammar points, optionally filtered."""
    from grammar.models import GrammarPoint
    qs = GrammarPoint.objects.filter(is_active=True)
    if level:
        qs = qs.filter(level=level)
    if book_slug:
        qs = qs.filter(book__slug=book_slug)
    return [
        {
            "id": g.id,
            "title": g.title,
            "slug": g.slug,
            "level": g.level,
            "meaning": g.meaning_vi,
            "structure": g.formation,
            "order": g.order,
            "example_count": g.structured_examples.count(),
        }
        for g in qs.prefetch_related("structured_examples")
    ]


@router.get("/books", response=list)
def list_books(request, level: str = None):
    """List grammar books."""
    from grammar.models import GrammarBook
    qs = GrammarBook.objects.filter(is_active=True)
    if level:
        qs = qs.filter(level=level)
    return [
        {
            "id": b.id,
            "title": b.title,
            "slug": b.slug,
            "level": b.level,
            "description": b.description,
            "cover_image": b.cover_image.url if b.cover_image else None,
            "point_count": b.grammar_points.filter(is_active=True).count(),
        }
        for b in qs.prefetch_related("grammar_points")
    ]


@router.get("/books/{slug}")
def book_detail(request, slug: str):
    """Get grammar book detail with points."""
    from grammar.models import GrammarBook
    b = GrammarBook.objects.prefetch_related("grammar_points__structured_examples").get(slug=slug)
    points = [
        {
            "id": g.id,
            "title": g.title,
            "slug": g.slug,
            "level": g.level,
            "meaning": g.meaning_vi,
            "structure": g.formation,
            "order": g.order,
            "example_count": g.structured_examples.count(),
        }
        for g in b.grammar_points.filter(is_active=True)
    ]
    return {
        "id": b.id,
        "title": b.title,
        "slug": b.slug,
        "level": b.level,
        "description": b.description,
        "cover_image": b.cover_image.url if b.cover_image else None,
        "points": points,
    }


def _grammar_detail_data(request, slug: str):
    """Shared logic for grammar point detail."""
    from grammar.models import GrammarPoint
    try:
        g = GrammarPoint.objects.prefetch_related(
            "structured_examples", "exercise_sets"
        ).get(slug=slug, is_active=True)
    except GrammarPoint.DoesNotExist:
        # Try lookup by ID (for hash-based slugs like gp-7196 → try id=7196 won't work,
        # so just re-raise)
        raise

    examples = [
        {
            "id": e.id,
            "sentence_jp": e.sentence_jp,
            "sentence_vi": e.sentence_vi,
            "highlighted_jp": e.highlighted_jp(),
            "order": e.order,
        }
        for e in g.structured_examples.all()
    ]
    exercise_sets = [
        {"id": s.id, "title": s.title, "slug": s.slug, "question_count": s.question_count}
        for s in g.exercise_sets.filter(is_active=True)
    ]

    # Parse old examples text field into list
    old_examples = [line.strip() for line in (g.examples or "").split("\n") if line.strip()] if g.examples else []

    # Related points (same level)
    related = [
        {"slug": rp.slug, "title": rp.title, "meaning_vi": rp.meaning_vi}
        for rp in GrammarPoint.objects.filter(level=g.level, is_active=True)
            .exclude(pk=g.pk)[:8]
    ]

    # Prev / Next navigation
    siblings = list(
        GrammarPoint.objects.filter(level=g.level, is_active=True)
        .order_by("order", "title")
        .values_list("slug", "title")
    )
    slugs_list = [s[0] for s in siblings]
    idx = slugs_list.index(g.slug) if g.slug in slugs_list else -1
    prev_slug = siblings[idx - 1][0] if idx > 0 else None
    prev_title = siblings[idx - 1][1] if idx > 0 else None
    next_slug = siblings[idx + 1][0] if 0 <= idx < len(siblings) - 1 else None
    next_title = siblings[idx + 1][1] if 0 <= idx < len(siblings) - 1 else None

    # Best score
    best_score = None
    if hasattr(request, 'user') and request.user.is_authenticated:
        from grammar.models import GrammarAttempt
        best = GrammarAttempt.objects.filter(
            user=request.user,
            exercise_set__grammar_point=g,
        ).order_by("-score").first()
        if best and best.total > 0:
            best_score = round(best.score / best.total * 100)

    return {
        "id": g.id,
        "title": g.title,
        "slug": g.slug,
        "level": g.level,
        "reading": g.reading,
        "meaning_vi": g.meaning_vi,
        "formation": g.formation,
        "summary": g.summary,
        "explanation": g.explanation,
        "details": g.details,
        "notes": g.notes,
        "book_title": g.book.title if g.book else "",
        "book_slug": g.book.slug if g.book else "",
        "examples": examples,
        "old_examples": old_examples,
        "exercise_sets": exercise_sets,
        "related": related,
        "prev_slug": prev_slug,
        "prev_title": prev_title,
        "next_slug": next_slug,
        "next_title": next_title,
        "best_score": best_score,
    }


@router.get("/points/{slug}")
def grammar_point_detail(request, slug: str):
    """Get grammar point detail (SEO-friendly URL)."""
    return _grammar_detail_data(request, slug)


@router.get("/{slug}")
def grammar_detail(request, slug: str):
    """Get grammar point detail."""
    return _grammar_detail_data(request, slug)



@router.get("/exercise/{slug}")
def exercise_detail(request, slug: str):
    """Get exercise questions."""
    from grammar.models import GrammarExerciseSet
    s = GrammarExerciseSet.objects.prefetch_related("questions").get(slug=slug, is_active=True)
    questions = [
        {
            "id": q.id,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "choices": q.choices or [],
            # SENTENCE_ORDER fields
            "sentence_prefix": q.sentence_prefix,
            "sentence_suffix": q.sentence_suffix,
            "tokens": q.tokens or [],
            "star_position": q.star_position,
            "order": q.order,
        }
        for q in s.questions.all()
    ]
    return {
        "id": s.id,
        "title": s.title,
        "slug": s.slug,
        "level": s.level,
        "grammar_point": s.grammar_point.title if s.grammar_point else None,
        "questions": questions,
    }


@router.post("/exercise/{slug}/submit")
def submit_exercise(request, slug: str, answers: dict):
    """Submit exercise answers and get results."""
    from grammar.models import GrammarExerciseSet, GrammarAttempt, GrammarQuestionAnswer
    s = GrammarExerciseSet.objects.prefetch_related("questions").get(slug=slug)

    correct_count = 0
    results = []
    for q in s.questions.all():
        user_answer = answers.get(str(q.id), "")
        if q.question_type == "MCQ":
            is_correct = str(user_answer) == str(q.correct_answer)
        else:
            # SENTENCE_ORDER: user sends list of indices
            is_correct = user_answer == q.correct_order
        if is_correct:
            correct_count += 1
        results.append({
            "question_id": q.id,
            "user_answer": user_answer,
            "correct_answer": q.correct_answer if q.question_type == "MCQ" else q.correct_order,
            "is_correct": is_correct,
            "explanation_jp": q.explanation_jp,
            "explanation_vi": q.explanation_vi,
        })

    # Save attempt
    total = len(results)
    attempt = GrammarAttempt.objects.create(
        user=request.user,
        exercise_set=s,
        score=correct_count,
        total=total,
    )
    for r in results:
        q_id = r["question_id"]
        from grammar.models import GrammarQuestion
        q = GrammarQuestion.objects.get(id=q_id)
        GrammarQuestionAnswer.objects.create(
            attempt=attempt,
            question=q,
            user_answer=r["user_answer"],
            is_correct=r["is_correct"],
        )

    return {
        "attempt_id": attempt.id,
        "total": total,
        "correct": correct_count,
        "score": round(correct_count / max(total, 1) * 100),
        "results": results,
    }
