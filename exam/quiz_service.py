"""
Quiz Service — Shared business logic for all quiz types (Strategy Pattern).

Follows SOLID principles:
- SRP: Separates DB query logic from API routing
- OCP: New quiz type = new QuizTypeConfig, no code duplication
- DRY: Single source of truth for question serialization, listing, pagination

Usage:
    from exam.quiz_service import QuizService, USAGE_CONFIG, BUNPOU_CONFIG

    templates = QuizService.list_templates(USAGE_CONFIG, level="N2")
    detail = QuizService.get_detail("some-slug")
    questions = QuizService.get_all_questions(BUNPOU_CONFIG, level="N3", page=1)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Strategy: Quiz Type Configuration ────────────────────────

@dataclass(frozen=True)
class QuizTypeConfig:
    """
    Defines how to filter ExamTemplates for a specific quiz type.
    Each quiz type provides its own filter kwargs (Strategy Pattern).
    """
    quiz_type: str
    filter_kwargs: Dict[str, Any] = field(default_factory=dict)


# Pre-defined configs for each quiz type
USAGE_CONFIG = QuizTypeConfig(
    quiz_type="usage",
    filter_kwargs={"main_question_type": "USAGE"},
)

BUNPOU_CONFIG = QuizTypeConfig(
    quiz_type="bunpou",
    filter_kwargs={"category": "BUN"},
)


# ── Service Layer ────────────────────────────────────────────

class QuizService:
    """
    Single Responsibility: handles all quiz-related DB queries and serialization.
    API endpoints delegate to this service.
    """

    @staticmethod
    def serialize_question(
        q,
        idx: Optional[int] = None,
        template=None,
    ) -> dict:
        """
        Serialize an ExamQuestion to a dict.
        DRY: single source of truth for question serialization.

        Args:
            q: ExamQuestion instance
            idx: Optional 1-based index (for all-questions views with `num`)
            template: Optional ExamTemplate (for all-questions views with template info)
        """
        choices = q.data.get("choices", []) if q.data else []
        result = {
            "id": q.id,
            "text": q.text,
            "text_vi": q.text_vi,
            "choices": choices,
            "correct_answer": q.correct_answer,
            "explanation_json": q.explanation_json or {},
        }
        if idx is not None:
            result["num"] = idx
        if template is not None:
            result["template_title"] = template.title
            result["template_slug"] = template.slug
            result["level"] = template.level
            result["book_title"] = template.book.title if template.book else None
        return result

    @staticmethod
    def list_templates(config: QuizTypeConfig, level: str = "") -> List[dict]:
        """
        List quiz templates filtered by type and optional JLPT level.

        Returns list of template summary dicts.
        """
        from exam.models import ExamTemplate
        from django.db.models import Count

        qs = ExamTemplate.objects.filter(
            is_active=True, **config.filter_kwargs
        ).select_related("book").annotate(q_count=Count("questions"))

        if level:
            qs = qs.filter(level=level)

        return [
            {
                "id": t.id,
                "title": t.title,
                "slug": t.slug,
                "level": t.level,
                "question_count": t.q_count,
                "book_title": t.book.title if t.book else None,
            }
            for t in qs.order_by("-id")
        ]

    @staticmethod
    def get_detail(slug: str) -> dict:
        """
        Get quiz template detail with full questions.
        Already type-agnostic (just fetches by slug).
        """
        from exam.models import ExamTemplate

        t = ExamTemplate.objects.select_related("book").prefetch_related(
            "questions"
        ).get(slug=slug, is_active=True)

        questions = [
            QuizService.serialize_question(q)
            for q in t.questions.all().order_by("order")
        ]

        return {
            "id": t.id,
            "title": t.title,
            "slug": t.slug,
            "level": t.level,
            "question_count": len(questions),
            "book": {"id": t.book.id, "title": t.book.title} if t.book else None,
            "questions": questions,
        }

    @staticmethod
    def get_all_questions(
        config: QuizTypeConfig,
        level: str = "",
        page: int = 1,
        page_size: int = 9999,
    ) -> dict:
        """
        Get all questions across templates for the grid UI, with pagination.
        """
        from exam.models import ExamTemplate

        qs = ExamTemplate.objects.filter(
            is_active=True, **config.filter_kwargs
        ).select_related("book").prefetch_related("questions").order_by("id")

        if level:
            qs = qs.filter(level=level)

        all_questions = []
        idx = 1
        for t in qs:
            for q in t.questions.all().order_by("order"):
                all_questions.append(
                    QuizService.serialize_question(q, idx=idx, template=t)
                )
                idx += 1

        # Paginate
        total = len(all_questions)
        page_size = min(page_size, 200)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "questions": all_questions[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
