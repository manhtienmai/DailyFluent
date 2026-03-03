"""
Exam Service — business logic for exam sessions and answer-saving.

Follows SOLID principles:
- SRP: Separates answer/session logic from API routing
- DRY: Unifies choukai_save_answer + quiz_save_answer into one method
"""


class AnswerService:
    """
    Unified answer-saving logic for all exam types.

    Previously duplicated in:
      - exam/api.py → choukai_save_answer (line 129)
      - exam/api.py → quiz_save_answer (line 658)
      - exam/views.py → choukai_save_answer (line 746)
    """

    @staticmethod
    def save_single_answer(user, question_id, selected_key, mode="quiz"):
        """
        Save a single answer to an exam question.
        Creates or reuses an in-progress attempt for the question's template.

        Args:
            user: The user saving the answer
            question_id: ID of the ExamQuestion
            selected_key: The selected answer key (e.g. "1", "2", "3", "4")
            mode: Attempt mode tag (e.g. "quiz", "choukai")

        Returns:
            dict with success status, correctness, and attempt stats
        """
        from exam.models import ExamQuestion, ExamAttempt, QuestionAnswer
        from django.db.models import Count, Q

        question = ExamQuestion.objects.get(pk=question_id)
        template = question.template

        # Get or create in-progress attempt
        attempt, _ = ExamAttempt.objects.get_or_create(
            user=user,
            template=template,
            status="in_progress",
            defaults={
                "total_questions": template.questions.count(),
                "data": {"mode": mode},
            },
        )

        is_correct = str(selected_key) == str(question.correct_answer)

        # Save/update answer
        QuestionAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "raw_answer": {"selected_key": str(selected_key)},
                "is_correct": is_correct,
            },
        )

        # Update attempt stats in bulk (efficient)
        agg = attempt.answers.aggregate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
        )
        ExamAttempt.objects.filter(pk=attempt.pk).update(
            total_questions=agg["total"],
            correct_count=agg["correct"],
        )

        return {
            "ok": True,
            "is_correct": is_correct,
            "attempt_id": attempt.id,
            "answered": agg["total"],
            "correct": agg["correct"],
            "total": template.questions.count(),
        }


class ExamSessionService:
    """
    Manages the exam attempt lifecycle:
    start → detail → submit → result → progress.
    """

    @staticmethod
    def start_attempt(user, template_slug):
        """Start a new exam attempt and return questions."""
        from exam.models import ExamTemplate, ExamAttempt

        template = ExamTemplate.objects.get(slug=template_slug)
        attempt = ExamAttempt.objects.create(
            user=user,
            template=template,
            total_questions=template.total_questions,
        )
        questions = template.questions.all()
        return {
            "attempt_id": attempt.id,
            "template_title": template.title,
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "text_vi": q.text_vi,
                    "question_type": q.question_type,
                    "choices": q.mcq_choices,
                    "tokens": q.sentence_tokens,
                    "audio": q.audio.url if q.audio else "",
                    "image": q.image.url if q.image else "",
                }
                for q in questions
            ],
        }

    @staticmethod
    def get_attempt_detail(user, attempt_id):
        """Get attempt with its questions."""
        from exam.models import ExamAttempt
        from ninja.errors import HttpError

        try:
            attempt = ExamAttempt.objects.select_related("template").get(
                id=attempt_id, user=user
            )
        except ExamAttempt.DoesNotExist:
            raise HttpError(404, "Attempt not found")

        questions = attempt.template.questions.all()
        return {
            "attempt_id": attempt.id,
            "template_title": attempt.template.title,
            "status": attempt.status,
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "question_type": q.question_type,
                    "choices": q.mcq_choices,
                }
                for q in questions
            ],
        }

    @staticmethod
    def submit_attempt(user, attempt_id, answers_dict):
        """
        Submit all answers for an attempt at once.

        Args:
            answers_dict: {question_id_str: selected_key_str}
        """
        from exam.models import ExamAttempt, QuestionAnswer
        from django.utils import timezone
        from ninja.errors import HttpError

        try:
            attempt = ExamAttempt.objects.select_related("template").get(
                id=attempt_id, user=user
            )
        except ExamAttempt.DoesNotExist:
            raise HttpError(404, "Attempt not found")

        questions = attempt.template.questions.all()
        correct = 0
        answer_objects = []
        for q in questions:
            user_ans = answers_dict.get(str(q.id), "")
            is_correct = str(user_ans) == str(q.correct_answer)
            if is_correct:
                correct += 1
            answer_objects.append(
                QuestionAnswer(
                    attempt=attempt,
                    question=q,
                    raw_answer={"selected_key": user_ans},
                    is_correct=is_correct,
                )
            )

        QuestionAnswer.objects.bulk_create(answer_objects)

        attempt.correct_count = correct
        attempt.status = "submitted"
        attempt.submitted_at = timezone.now()
        attempt.save()

        return {
            "attempt_id": attempt.id,
            "score": attempt.score_percent,
            "correct": correct,
            "total": attempt.total_questions,
            "rating": attempt.rating_label,
        }

    @staticmethod
    def get_result(user, attempt_id):
        """Get detailed results for a completed attempt."""
        from exam.models import ExamAttempt
        from ninja.errors import HttpError

        try:
            attempt = ExamAttempt.objects.select_related("template").get(
                id=attempt_id, user=user
            )
        except ExamAttempt.DoesNotExist:
            raise HttpError(404, "Attempt not found")

        answers = attempt.answers.select_related("question").all()
        return {
            "attempt_id": attempt.id,
            "template_title": attempt.template.title,
            "score": attempt.score_percent,
            "rating": attempt.rating_label,
            "total": attempt.total_questions,
            "correct": attempt.correct_count,
            "answers": [
                {
                    "question_id": a.question.id,
                    "question_text": a.question.text,
                    "question_text_vi": a.question.text_vi,
                    "selected": a.raw_answer.get("selected_key", ""),
                    "correct": a.question.correct_answer,
                    "is_correct": a.is_correct,
                    "explanation_vi": a.question.explanation_vi,
                    "explanation_json": a.question.explanation_json or {},
                    "choices": (
                        a.question.data.get("choices", [])
                        if a.question.data
                        else []
                    ),
                }
                for a in answers
            ],
        }

    @staticmethod
    def get_progress(user, quiz_type):
        """Get user's quiz progress for a specific quiz type."""
        from exam.models import ExamAttempt
        from django.db.models import Max, Count
        from ninja.errors import HttpError

        CATEGORY_MAP = {
            "usage": "USAGE",
            "bunpou": "BUN",
            "dokkai": "DOKKAI",
            "mojigoi": "MOJI",
            "choukai": "CHOUKAI",
        }
        category = CATEGORY_MAP.get(quiz_type)
        if not category:
            raise HttpError(400, f"Unknown quiz type: {quiz_type}")

        # Get latest attempt per template in one query
        latest_ids = (
            ExamAttempt.objects.filter(
                user=user,
                template__category=category,
            )
            .values("template_id")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )

        attempts = (
            ExamAttempt.objects.filter(id__in=latest_ids)
            .select_related("template")
            .annotate(_answered=Count("answers"))
            .order_by("-started_at")
        )

        results = [
            {
                "template_slug": att.template.slug,
                "template_title": att.template.title,
                "status": att.status,
                "answered": att._answered,
                "correct": att.correct_count or 0,
                "total": att.total_questions or 0,
                "started_at": (
                    att.started_at.isoformat() if att.started_at else None
                ),
            }
            for att in attempts
        ]

        return {"quiz_type": quiz_type, "templates": results}
