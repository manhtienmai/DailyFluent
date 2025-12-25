from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    ExamTemplate,
    ExamAttempt,
    QuestionAnswer,
    QuestionType,
    ExamBook,
    ExamLevel,
    ExamGroupType,
)


def build_mondai_groups(questions):
    """
    Gom câu hỏi theo mondai, và trong mỗi group:
      - is_dokkai: có câu nào gắn passage không
      - passage_groups: list { passage, questions } cho các câu dokkai
      - non_passage_questions: list câu không có passage (moji/goi/bunpou...)
    `questions` giả định đã được order theo (mondai, order_in_mondai, order, id).
    """
    groups = []

    current_mondai = None
    current_questions = []

    for q in questions:
        mondai = q.mondai or ""
        if current_mondai is None:
            current_mondai = mondai

        if mondai != current_mondai:
            groups.append({"mondai": current_mondai, "questions": current_questions})
            current_mondai = mondai
            current_questions = []

        current_questions.append(q)

    if current_questions:
        groups.append({"mondai": current_mondai, "questions": current_questions})

    # Bổ sung thông tin dokkai / passage
    for g in groups:
        qs = g["questions"]
        has_passage = any(q.passage_id for q in qs)
        g["is_dokkai"] = has_passage

        passage_groups = []
        non_passage = []

        if has_passage:
            passage_map = {}
            for q in qs:
                if q.passage_id:
                    p = q.passage
                    if p.id not in passage_map:
                        passage_map[p.id] = {"passage": p, "questions": []}
                    passage_map[p.id]["questions"].append(q)
                else:
                    non_passage.append(q)

            passage_groups = sorted(
                passage_map.values(),
                key=lambda item: (item["passage"].order, item["passage"].id),
            )
        else:
            non_passage = qs

        g["passage_groups"] = passage_groups
        g["non_passage_questions"] = non_passage

    return groups


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

    # Lấy tất cả câu hỏi (cả moji/bunpou lẫn dokkai), kèm passage nếu có
    questions = (
        template.questions
        .select_related("passage")
        .order_by("mondai", "order_in_mondai", "order", "id")
    )

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

    # Build nhóm Mondai, trong đó mỗi nhóm biết phần dokkai / thường
    mondai_groups = build_mondai_groups(questions)

    # Để không phải sửa chỗ khác, vẫn truyền 'session' và 'template_obj'
    return render(
        request,
        "exam/exam_take.html",
        {
            "session": attempt,        # ExamAttempt
            "template_obj": template,
            "questions": questions,    # để đếm số câu ở header
            "mondai_groups": mondai_groups,
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
    selected_level = request.GET.get("level")          # 'N2', 'N3'...
    search_query = request.GET.get("q", "").strip()    # text search

    qs = ExamBook.objects.filter(is_active=True)

    # filter theo level
    valid_levels = [code for code, _ in ExamLevel.choices]
    if selected_level in valid_levels:
        qs = qs.filter(level=selected_level)

    # filter theo tên sách (nếu có gõ)
    if search_query:
        qs = qs.filter(title__icontains=search_query)

    books = qs.prefetch_related("tests").order_by("level", "title")

    context = {
        "books": books,
        "levels": valid_levels,
        "selected_level": selected_level,
        "search_query": search_query,
    }
    return render(request, "exam/book_list.html", context)


def book_detail(request, slug):
    """
    Trang chi tiết 1 Book:
    - Thông tin sách
    - Luyện theo dạng câu (pattern / mondai)
    - Học theo ngày (Day 01 → Day 30)
    - Đề lẻ / MOGI
    Đồng thời, gắn kèm attempt gần nhất của user cho từng bài test.
    """
    book = get_object_or_404(ExamBook, slug=slug, is_active=True)

    # Các attempt đã nộp của user hiện tại (nếu đã login)
    if request.user.is_authenticated:
        user_attempts_qs = (
            ExamAttempt.objects
            .filter(
                user=request.user,
                status=ExamAttempt.Status.SUBMITTED,
            )
            .order_by("-submitted_at")   # mới nhất trước
        )
    else:
        user_attempts_qs = ExamAttempt.objects.none()

    # Lấy toàn bộ bài test của sách + prefetch questions & attempts của user
    tests_qs = (
        book.tests
        .filter(is_active=True)
        .order_by("group_type", "lesson_index", "id")
        .prefetch_related(
            "questions",
            Prefetch(
                "attempts",
                queryset=user_attempts_qs,
                to_attr="user_attempts",   # => mỗi t sẽ có t.user_attempts = [attempt, ...]
            ),
        )
    )

    tests = list(tests_qs)

    # Chia theo group_type
    day_tests = [t for t in tests if t.group_type == ExamGroupType.BY_DAY]
    pattern_tests = [t for t in tests if t.group_type == ExamGroupType.BY_PATTERN]
    standalone_tests = [t for t in tests if t.group_type == ExamGroupType.STANDALONE]

    # Gom pattern thành group (Dạng 01, 02...)
    pattern_dict = {}
    for t in pattern_tests:
        key = t.lesson_index or 0
        group = pattern_dict.setdefault(
            key,
            {
                "lesson_index": key,
                "title": "",
                "tests": [],
            },
        )
        if not group["title"]:
            group["title"] = t.subtitle or t.title
        group["tests"].append(t)

    pattern_groups = sorted(
        pattern_dict.values(),
        key=lambda g: g["lesson_index"],
    )

    tests_total = len(tests)
    first_day_test = day_tests[0] if day_tests else None
    first_any_test = first_day_test or (tests[0] if tests else None)

    context = {
        "book": book,
        "tests_total": tests_total,
        "pattern_groups": pattern_groups,
        "day_tests": day_tests,
        "standalone_tests": standalone_tests,
        "first_day_test": first_day_test,
        "first_any_test": first_any_test,
    }
    return render(request, "exam/book_detail.html", context)
