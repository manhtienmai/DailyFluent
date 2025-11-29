from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    ExamTemplate,
    ExamAttempt,
    QuestionAnswer,
    QuestionType,
    ExamBook,
)


@login_required
def exam_list(request):
    selected_level = request.GET.get("level") or ""

    templates = ExamTemplate.objects.filter(is_active=True)
    if selected_level:
        templates = templates.filter(level=selected_level)

    levels = ["N5", "N4", "N3", "N2", "N1"]

    return render(
        request,
        "exam/exam_list.html",
        {
            "templates": templates,
            "selected_level": selected_level,
            "levels": levels,
        },
    )


@login_required
def start_exam(request, slug):
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True)

    attempt = ExamAttempt.objects.create(
        user=request.user,
        template=template,
        total_questions=template.questions.count(),
    )
    return redirect("exam:take_exam", session_id=attempt.id)


@login_required
def take_exam(request, session_id):
    attempt = get_object_or_404(
        ExamAttempt,
        id=session_id,
        user=request.user,
    )
    template = attempt.template

    questions = template.questions.order_by("order")

    if request.method == "POST" and attempt.status != ExamAttempt.Status.SUBMITTED:
        correct = 0

        for q in questions:
            field_name = f"q{q.id}"
            raw_value = request.POST.get(field_name)

            raw_answer = {}
            is_correct = False

            if q.question_type == QuestionType.MCQ:
                # Giá trị gửi lên là key của lựa chọn (VD: "1", "2", "3", "4")
                selected_key = (raw_value or "").strip()
                raw_answer = {"selected_key": selected_key}
                is_correct = bool(selected_key) and (selected_key == q.correct_answer)

            else:
                # TODO: các loại câu khác (ORDER, FILL...) sẽ xử lý sau
                # tạm thời coi là sai hết để không vỡ flow
                raw_answer = {"value": raw_value}

            QuestionAnswer.objects.update_or_create(
                attempt=attempt,
                question=q,
                defaults={
                    "raw_answer": raw_answer,
                    "is_correct": is_correct,
                },
            )

            if is_correct:
                correct += 1

        attempt.correct_count = correct
        attempt.total_questions = questions.count()
        attempt.status = ExamAttempt.Status.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.save()
        return redirect("exam:exam_result", session_id=attempt.id)

    # Để không phải sửa template, vẫn truyền context key là "session"
    return render(
        request,
        "exam/exam_take.html",
        {
            "session": attempt,        # ExamAttempt
            "template_obj": template,
            "questions": questions,
        },
    )


@login_required
def exam_result(request, session_id):
    attempt = get_object_or_404(
        ExamAttempt,
        id=session_id,
        user=request.user,
        status=ExamAttempt.Status.SUBMITTED,
    )
    template = attempt.template

    answers = list(
        attempt.answers.select_related("question").order_by(
            "question__mondai", "question__order_in_mondai", "question_id"
        )
    )

    # thống kê theo mondai (giống code cũ)
    stats_by_mondai = {}
    for ans in answers:
        key = ans.question.mondai or "01"
        bucket = stats_by_mondai.setdefault(key, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if ans.is_correct:
            bucket["correct"] += 1

    wrong_count = attempt.total_questions - attempt.correct_count

    return render(
        request,
        "exam/exam_result.html",
        {
            "session": attempt,       # vẫn dùng key 'session' cho template cũ
            "template_obj": template,
            "answers": answers,
            "stats_by_mondai": stats_by_mondai,
            "wrong_count": wrong_count,
        },
    )

def book_list(request):
    """
    Trang hiển thị danh sách Book và các bài test (ExamTemplate) thuộc từng Book.
    """
    # Prefetch template cho mỗi book để tránh N+1 query
    books = (
        ExamBook.objects
        .all()
        .prefetch_related("examtemplate_set")  # dùng tên default của FK
        .order_by("title")
    )

    context = {
        "books": books,
    }
    return render(request, "exam/book_list.html", context)