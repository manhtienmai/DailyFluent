import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator

from .models import (
    GrammarBook,
    GrammarPoint,
    GrammarLevel,
    GrammarExample,
    GrammarExerciseSet,
    GrammarQuestion,
    UserGrammarProgress,
    GrammarAttempt,
    GrammarQuestionAnswer,
)


LEVEL_ORDER = ["N5", "N4", "N3", "N2", "N1"]

LEVEL_COLORS = {
    "N5": "green",
    "N4": "teal",
    "N3": "blue",
    "N2": "purple",
    "N1": "amber",
}


def _get_user_progress(user, grammar_point):
    if user.is_authenticated:
        try:
            return UserGrammarProgress.objects.get(user=user, grammar_point=grammar_point)
        except UserGrammarProgress.DoesNotExist:
            pass
    return None


def _mark_studied(user, grammar_point):
    if user.is_authenticated:
        progress, created = UserGrammarProgress.objects.get_or_create(
            user=user, grammar_point=grammar_point
        )
        if not progress.studied_at:
            progress.studied_at = timezone.now()
            progress.save(update_fields=["studied_at"])
        return progress
    return None


def grammar_home(request):
    active_level = request.GET.get("level", "").upper()
    if active_level not in dict(GrammarLevel.choices):
        active_level = ""

    points_qs = GrammarPoint.objects.filter(is_active=True).select_related("book")
    if active_level:
        points_qs = points_qs.filter(level=active_level)

    # Get user progress for authenticated users
    progress_map = {}
    if request.user.is_authenticated:
        progresses = UserGrammarProgress.objects.filter(
            user=request.user,
            grammar_point__in=points_qs
        ).values("grammar_point_id", "best_score", "studied_at")
        progress_map = {p["grammar_point_id"]: p for p in progresses}

    return render(request, "grammar/home.html", {
        "points": points_qs,
        "active_level": active_level,
        "levels": LEVEL_ORDER,
        "level_colors": LEVEL_COLORS,
        "progress_map": progress_map,
    })


def grammar_level_detail(request, level):
    points = GrammarPoint.objects.filter(is_active=True, level=level).select_related("book")
    paginator = Paginator(points, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "grammar/home.html", {
        "points": page,
        "active_level": level,
        "levels": LEVEL_ORDER,
        "level_colors": LEVEL_COLORS,
        "progress_map": {},
    })


def grammar_book_list(request):
    books = GrammarBook.objects.filter(is_active=True)
    books_by_level = {}
    for lv in LEVEL_ORDER:
        lv_books = books.filter(level=lv)
        if lv_books.exists():
            books_by_level[lv] = lv_books
    return render(request, "grammar/book_list.html", {
        "books": books,
        "books_by_level": books_by_level,
        "levels": LEVEL_ORDER,
        "level_colors": LEVEL_COLORS,
    })


def grammar_book_detail(request, slug):
    book = get_object_or_404(GrammarBook, slug=slug, is_active=True)
    points = book.grammar_points.filter(is_active=True).order_by("order", "title")
    exercise_sets = book.exercise_sets.filter(is_active=True)
    return render(request, "grammar/book_detail.html", {
        "book": book,
        "points": points,
        "exercise_sets": exercise_sets,
        "level_colors": LEVEL_COLORS,
    })


def grammar_point_detail(request, slug):
    point = get_object_or_404(GrammarPoint, slug=slug, is_active=True)
    examples = point.structured_examples.all()
    old_examples = [line.strip() for line in (point.examples or "").splitlines() if line.strip()]
    exercise_sets = point.exercise_sets.filter(is_active=True)

    # Pick first set for embedded preview (up to 5 questions)
    embedded_questions = []
    if exercise_sets.exists():
        first_set = exercise_sets.first()
        embedded_questions = list(first_set.questions.all()[:5])

    # Related grammar points
    related = GrammarPoint.objects.filter(
        is_active=True, level=point.level
    ).exclude(pk=point.pk)[:6]

    # Prev / Next navigation
    same_level = GrammarPoint.objects.filter(is_active=True, level=point.level).order_by("order", "title")
    ids = list(same_level.values_list("id", flat=True))
    try:
        idx = ids.index(point.pk)
        prev_point = same_level[idx - 1] if idx > 0 else None
        next_point = same_level[idx + 1] if idx < len(ids) - 1 else None
    except ValueError:
        prev_point = next_point = None

    progress = _mark_studied(request.user, point)

    return render(request, "grammar/point_detail.html", {
        "point": point,
        "examples": examples,
        "old_examples": old_examples,
        "exercise_sets": exercise_sets,
        "embedded_questions": embedded_questions,
        "related": related,
        "prev_point": prev_point,
        "next_point": next_point,
        "progress": progress,
        "level_colors": LEVEL_COLORS,
    })


def grammar_exercise(request, slug):
    exercise_set = get_object_or_404(GrammarExerciseSet, slug=slug, is_active=True)
    questions = list(exercise_set.questions.all().order_by("order"))

    # Serialize questions to JSON for Alpine.js
    questions_json = []
    for q in questions:
        qdata = {
            "id": q.pk,
            "type": q.question_type,
            "order": q.order,
            "question_text": q.question_text,
            "explanation_jp": q.explanation_jp,
            "explanation_vi": q.explanation_vi,
        }
        if q.question_type == GrammarQuestion.MCQ:
            qdata["choices"] = q.choices or []
            qdata["correct_answer"] = q.correct_answer
        else:  # SENTENCE_ORDER
            qdata["sentence_prefix"] = q.sentence_prefix
            qdata["sentence_suffix"] = q.sentence_suffix
            qdata["tokens"] = q.tokens or []
            qdata["correct_order"] = q.correct_order or []
            qdata["star_position"] = q.star_position
        questions_json.append(qdata)

    return render(request, "grammar/exercise.html", {
        "exercise_set": exercise_set,
        "questions": questions,
        "questions_json": json.dumps(questions_json, ensure_ascii=False),
        "level_colors": LEVEL_COLORS,
    })


# ─── API Endpoints ────────────────────────────────────────────────────────────

@require_POST
def api_check_answer(request):
    try:
        data = json.loads(request.body)
        question_id = data.get("question_id")
        user_answer = data.get("user_answer")

        question = GrammarQuestion.objects.get(pk=question_id)

        if question.question_type == GrammarQuestion.MCQ:
            is_correct = str(user_answer) == str(question.correct_answer)
        else:  # SENTENCE_ORDER
            # user_answer is [idx0, idx1, idx2, idx3] — token indices placed in box 1,2,3,4
            is_correct = user_answer == question.correct_order

        return JsonResponse({
            "is_correct": is_correct,
            "correct_answer": question.correct_answer if question.question_type == GrammarQuestion.MCQ else question.correct_order,
            "star_answer": question.get_star_answer(),
            "explanation_jp": question.explanation_jp,
            "explanation_vi": question.explanation_vi,
        })
    except (GrammarQuestion.DoesNotExist, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_POST
def api_submit_exercise(request):
    try:
        data = json.loads(request.body)
        exercise_set_id = data.get("exercise_set_id")
        answers = data.get("answers", [])  # [{question_id, user_answer, is_correct}]

        exercise_set = GrammarExerciseSet.objects.get(pk=exercise_set_id)
        score = sum(1 for a in answers if a.get("is_correct"))
        total = len(answers)

        attempt = None
        if request.user.is_authenticated:
            attempt = GrammarAttempt.objects.create(
                user=request.user,
                exercise_set=exercise_set,
                score=score,
                total=total,
            )

            for ans in answers:
                try:
                    q = GrammarQuestion.objects.get(pk=ans["question_id"])
                    GrammarQuestionAnswer.objects.create(
                        attempt=attempt,
                        question=q,
                        user_answer=ans["user_answer"],
                        is_correct=ans["is_correct"],
                    )
                except GrammarQuestion.DoesNotExist:
                    pass

            # Update UserGrammarProgress if linked to a grammar point
            if exercise_set.grammar_point:
                pct = round(score / total * 100) if total else 0
                progress, _ = UserGrammarProgress.objects.get_or_create(
                    user=request.user,
                    grammar_point=exercise_set.grammar_point,
                )
                if pct > progress.best_score:
                    progress.best_score = pct
                progress.last_practiced = timezone.now()
                progress.save()

        return JsonResponse({
            "success": True,
            "score": score,
            "total": total,
            "percentage": round(score / total * 100) if total else 0,
            "attempt_id": attempt.pk if attempt else None,
        })
    except (GrammarExerciseSet.DoesNotExist, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)


# ─── Legacy views (kept for backward compat) ──────────────────────────────────

def grammar_list(request):
    return grammar_home(request)


def grammar_detail(request, slug):
    return grammar_point_detail(request, slug)
