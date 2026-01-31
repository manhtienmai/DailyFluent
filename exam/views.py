from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
import json

from .models import (
    ExamTemplate,
    ExamAttempt,
    QuestionAnswer,
    QuestionType,
    ExamBook,
    ExamLevel,
    ExamCategory,
    ExamGroupType,
    TOEICPart,
    ListeningConversation,
    ReadingPassage,
    ExamComment,
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


def exam_list(request):
    from django.db.models import Count, Q
    from django.core.paginator import Paginator
    
    selected_level = request.GET.get("level") or ""

    templates = ExamTemplate.objects.filter(is_active=True).annotate(
        attempt_count=Count('attempts', filter=Q(attempts__status=ExamAttempt.Status.SUBMITTED))
    ).order_by('title')
    
    if selected_level:
        templates = templates.filter(level=selected_level)

    levels = ["TOEIC", "N5", "N4", "N3", "N2", "N1"]

    # Pagination - 12 items per page
    paginator = Paginator(templates, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "exam/exam_list.html",
        {
            "templates": page_obj,
            "page_obj": page_obj,
            "total_exams": paginator.count,
            "selected_level": selected_level,
            "levels": levels,
        },
    )


@login_required
def toeic_list(request):
    """Danh sách đề thi TOEIC"""
    from django.db.models import Count, Q
    
    templates = ExamTemplate.objects.filter(
        is_active=True,
        level=ExamLevel.TOEIC
    ).annotate(
        attempt_count=Count('attempts', filter=Q(attempts__status=ExamAttempt.Status.SUBMITTED))
    ).prefetch_related('questions').order_by("-created_at")
    
    # Tính số phần thi cho mỗi template
    for template in templates:
        distinct_parts = template.questions.exclude(toeic_part="").values_list('toeic_part', flat=True).distinct()
        template.parts_count = len(list(distinct_parts))
        if template.category == ExamCategory.TOEIC_FULL and template.parts_count == 0:
            template.parts_count = 7  # Full test thường có 7 phần
    
    # Phân loại theo category
    full_tests = templates.filter(category=ExamCategory.TOEIC_FULL)
    listening_tests = templates.filter(category=ExamCategory.LISTENING)
    reading_tests = templates.filter(category=ExamCategory.READING)
    
    return render(
        request,
        "exam/toeic_list.html",
        {
            "templates": templates,
            "full_tests": full_tests,
            "listening_tests": listening_tests,
            "reading_tests": reading_tests,
        },
    )


def exam_detail(request, slug):
    """
    Trang chi tiết đề thi: cho phép chọn chế độ luyện tập (tùy chọn part) hoặc làm full test.
    Xử lý cả GET (hiển thị) và POST (thêm comment).
    """
    from django.db.models import Count, Q
    from django.contrib import messages
    
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True)
    
    # Xử lý POST: thêm comment mới
    if request.method == "POST" and request.user.is_authenticated:
        action = request.POST.get('action')
        if action == 'add_comment':
            content = request.POST.get('content', '').strip()
            if content and len(content) <= 2000:
                ExamComment.objects.create(
                    template=template,
                    user=request.user,
                    content=content,
                )
                messages.success(request, "Đã thêm bình luận thành công!")
            else:
                messages.error(request, "Nội dung bình luận không hợp lệ (tối đa 2000 ký tự).")
            return redirect('exam:exam_detail', slug=slug)
    
    # Lấy thông tin thống kê
    attempt_count = ExamAttempt.objects.filter(
        template=template,
        status=ExamAttempt.Status.SUBMITTED
    ).count()
    
    # Lấy số comment thực tế
    comment_count = ExamComment.objects.filter(template=template, is_active=True).count()
    
    # Lấy danh sách comments (mới nhất trước, tối đa 50)
    comments = ExamComment.objects.filter(
        template=template,
        is_active=True
    ).select_related('user').order_by('-created_at')[:50]
    
    # Nếu là TOEIC, lấy danh sách các part có trong đề thi (chỉ hiển thị part, không hiển thị từng passage/conversation)
    parts_list = []
    if template.level == ExamLevel.TOEIC:
        # Lấy các part có trong đề thi
        distinct_parts = (
            template.questions
            .exclude(toeic_part="")
            .values_list('toeic_part', flat=True)
            .distinct()
            .order_by('toeic_part')
        )
        
        # Chỉ group theo part code, không group theo conversation/passage
        for part_code in distinct_parts:
            part_questions = template.questions.filter(toeic_part=part_code)
            parts_list.append({
                'part': part_code,
                'part_display': dict(TOEICPart.choices).get(part_code, part_code),
                'question_count': part_questions.count(),
                'questions': part_questions,
            })
    
    context = {
        'template': template,
        'attempt_count': attempt_count,
        'comment_count': comment_count,
        'comments': comments,
        'parts_list': parts_list,
    }
    return render(request, 'exam/exam_detail.html', context)


@login_required
def start_exam(request, slug):
    """
    Bắt đầu làm bài thi với các options:
    - mode: 'practice' hoặc 'full_test'
    - selected_parts: danh sách các part được chọn (chỉ cho practice mode)
    - time_limit: thời gian giới hạn (phút), None nếu không giới hạn
    """
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True)
    
    mode = request.POST.get('mode', 'full_test')  # 'practice' or 'full_test'
    selected_parts = request.POST.getlist('selected_parts')  # List of part codes
    time_limit = request.POST.get('time_limit', '')  # Minutes, empty = unlimited
    
    # Parse time_limit
    time_limit_minutes = None
    if time_limit and time_limit.strip():
        try:
            time_limit_minutes = int(time_limit)
            if time_limit_minutes < 0:
                time_limit_minutes = None
        except (ValueError, TypeError):
            time_limit_minutes = None
    
    # Lấy questions dựa trên mode và selected_parts
    if mode == 'practice' and selected_parts:
        # Practice mode: chỉ lấy questions của các part được chọn
        questions = template.questions.filter(toeic_part__in=selected_parts)
    else:
        # Full test: lấy tất cả questions
        questions = template.questions.all()
    
    # Tạo attempt
    attempt = ExamAttempt.objects.create(
        user=request.user,
        template=template,
        total_questions=questions.count(),
    )
    
    # Lưu mode và time_limit vào attempt data
    attempt.data = {
        'mode': mode,
        'selected_parts': selected_parts if mode == 'practice' else [],
        'time_limit_minutes': time_limit_minutes,
    }
    attempt.save()
    
    # Nếu là TOEIC, redirect đến TOEIC view
    if template.level == ExamLevel.TOEIC:
        return redirect("exam:take_toeic_exam", session_id=attempt.id)
    
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
        
        # Check for badges
        from core.badge_service import check_and_award_badges
        new_badges = check_and_award_badges(request.user)
        
        if new_badges:
            badges_data = []
            for gb in new_badges:
                badges_data.append({
                    "name": gb.name,
                    "description": gb.description,
                    "icon": gb.icon
                })
            request.session['new_badges'] = badges_data

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
            "question__toeic_part", "question__order", "question_id"
        )
    )

    # Tính thời gian hoàn thành
    time_taken = None
    if attempt.submitted_at and attempt.started_at:
        delta = attempt.submitted_at - attempt.started_at
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        time_taken = f"{hours}:{minutes:02d}:{seconds:02d}"

    wrong_count = attempt.total_questions - attempt.correct_count
    skipped_count = attempt.total_questions - len(answers)

    # Thống kê cho TOEIC
    toeic_stats = {}
    if template.level == ExamLevel.TOEIC:
        # Tính điểm TOEIC (tham khảo, không cần quá chính xác)
        # Listening: 5-495, Reading: 5-495
        listening_correct = 0
        listening_total = 0
        reading_correct = 0
        reading_total = 0
        
        # Thống kê theo part và sub-type
        stats_by_part = {}
        for ans in answers:
            q = ans.question
            part = q.toeic_part or ""
            
            if part.startswith("L"):
                listening_total += 1
                if ans.is_correct:
                    listening_correct += 1
            elif part.startswith("R"):
                reading_total += 1
                if ans.is_correct:
                    reading_correct += 1
            
            if part:
                # Phân loại sub-type
                sub_type = get_question_sub_type(q, part)
                key = f"{part}_{sub_type}"
                
                if key not in stats_by_part:
                    stats_by_part[key] = {
                        "part": part,
                        "sub_type": sub_type,
                        "correct": 0,
                        "wrong": 0,
                        "skipped": 0,
                        "total": 0,
                        "questions": []
                    }
                stats_by_part[key]["total"] += 1
                if ans.is_correct:
                    stats_by_part[key]["correct"] += 1
                elif ans.raw_answer.get("selected_key"):
                    stats_by_part[key]["wrong"] += 1
                else:
                    stats_by_part[key]["skipped"] += 1
                stats_by_part[key]["questions"].append({
                    "id": q.id,
                    "order": q.order,
                    "is_correct": ans.is_correct,
                    "selected": ans.raw_answer.get("selected_key", ""),
                })
        
        # Tính điểm TOEIC (công thức đơn giản)
        # Listening: 5 + (correct/total) * 490
        # Reading: 5 + (correct/total) * 490
        listening_score = 0
        reading_score = 0
        if listening_total > 0:
            listening_score = round(5 + (listening_correct / listening_total) * 490)
        if reading_total > 0:
            reading_score = round(5 + (reading_correct / reading_total) * 490)
        
        total_score = listening_score + reading_score
        
        toeic_stats = {
            "listening": {
                "correct": listening_correct,
                "total": listening_total,
                "score": listening_score,
            },
            "reading": {
                "correct": reading_correct,
                "total": reading_total,
                "score": reading_score,
            },
            "total_score": total_score,
            "stats_by_part": stats_by_part,
        }
    
    # Thống kê theo mondai (cho JLPT)
    stats_by_mondai = {}
    for ans in answers:
        key = ans.question.mondai or "01"
        bucket = stats_by_mondai.setdefault(key, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if ans.is_correct:
            bucket["correct"] += 1

    # Serialize answers for JavaScript
    import json
    answers_json = []
    for ans in answers:
        q = ans.question
        answer_data = {
            "id": ans.id,
            "question": {
                "id": q.id,
                "order": q.order,
                "toeic_part": q.toeic_part or "",
                "text": q.text or "",
                "question_type": q.question_type,
                "correct_answer": q.correct_answer or "",
                "explanation_vi": q.explanation_vi or "",
                "image": q.image.url if q.image else None,
                "audio": q.audio.url if q.audio else None,
                "mcq_choices": q.mcq_choices if q.question_type == QuestionType.MCQ else [],
            },
            "is_correct": ans.is_correct,
            "raw_answer": ans.raw_answer or {},
        }
        answers_json.append(answer_data)

    return render(
        request,
        "exam/exam_result.html",
        {
            "session": attempt,
            "template_obj": template,
            "answers": answers,
            "answers_json": json.dumps(answers_json),
            "stats_by_mondai": stats_by_mondai,
            "wrong_count": wrong_count,
            "skipped_count": skipped_count,
            "time_taken": time_taken,
            "toeic_stats_json": json.dumps(toeic_stats),
            "new_badges": request.session.pop('new_badges', []),
        },
    )


@login_required
def exam_result_question_detail(request, session_id, question_id):
    """API endpoint để lấy chi tiết câu hỏi trong exam result"""
    from django.http import JsonResponse
    
    attempt = get_object_or_404(
        ExamAttempt,
        id=session_id,
        user=request.user,
        status=ExamAttempt.Status.SUBMITTED,
    )
    
    answer = get_object_or_404(
        attempt.answers,
        question_id=question_id,
    )
    
    q = answer.question
    
    # Get sub_type for tags
    part = q.toeic_part or ""
    sub_type = get_question_sub_type(q, part)
    
    # Get topic from conversation metadata if exists
    topic = None
    if q.listening_conversation and hasattr(q.listening_conversation, 'metadata') and q.listening_conversation.metadata:
        topic = q.listening_conversation.metadata.get("topic")
    
    # Build response data
    data = {
        "question": {
            "id": q.id,
            "order": q.order,
            "toeic_part": q.toeic_part or "",
            "text": q.text or "",
            "text_vi": q.text_vi if hasattr(q, 'text_vi') else "",
            "question_type": q.question_type,
            "correct_answer": q.correct_answer or "",
            "explanation_vi": q.explanation_vi or "",
            "image": q.image.url if q.image else None,
            "audio": q.audio.url if q.audio else None,
            "audio_transcript": q.audio_transcript if hasattr(q, 'audio_transcript') else "",
            "audio_transcript_vi": q.audio_transcript_vi if hasattr(q, 'audio_transcript_vi') else "",
            "transcript_data": q.transcript_data if hasattr(q, 'transcript_data') else {},
            "mcq_choices": q.mcq_choices if q.question_type == QuestionType.MCQ else [],
            "sub_type": sub_type,
        },
        "answer": {
            "is_correct": answer.is_correct,
            "selected_key": answer.raw_answer.get("selected_key", ""),
        },
        "topic": topic,
    }
    
    # Add passage/conversation data if exists
    if q.passage:
        data["passage"] = {
            "id": q.passage.id,
            "title": q.passage.title or "",
            "content": q.passage.content or "",
            "image": q.passage.image.url if q.passage.image else None,
        }
    
    if q.listening_conversation:
        data["conversation"] = {
            "id": q.listening_conversation.id,
            "audio": q.listening_conversation.audio.url if q.listening_conversation.audio else None,
            "image": q.listening_conversation.image.url if q.listening_conversation.image else None,
            "transcript": q.listening_conversation.transcript or "",
            "transcript_vi": q.listening_conversation.transcript_vi if hasattr(q.listening_conversation, 'transcript_vi') else "",
            "transcript_data": q.listening_conversation.transcript_data if hasattr(q.listening_conversation, 'transcript_data') else {},
        }
    
    return JsonResponse(data)


@login_required
def redo_wrong_questions(request, session_id):
    """
    Tạo một attempt mới chỉ với các câu sai từ attempt trước.
    Không tính thời gian (unlimited time).
    """
    if request.method != "POST":
        return redirect("exam:exam_result", session_id=session_id)
    
    # Lấy attempt gốc
    original_attempt = get_object_or_404(
        ExamAttempt,
        id=session_id,
        user=request.user,
        status=ExamAttempt.Status.SUBMITTED,
    )
    
    # Lấy danh sách question IDs từ form
    question_ids = request.POST.getlist('question_ids')
    if not question_ids:
        return redirect("exam:exam_result", session_id=session_id)
    
    # Chuyển đổi sang int
    question_ids = [int(qid) for qid in question_ids if qid.isdigit()]
    
    # Lấy các questions
    questions = original_attempt.template.questions.filter(id__in=question_ids)
    
    if not questions.exists():
        return redirect("exam:exam_result", session_id=session_id)
    
    # Tạo attempt mới
    new_attempt = ExamAttempt.objects.create(
        user=request.user,
        template=original_attempt.template,
        total_questions=questions.count(),
        data={
            'mode': 'redo_wrong',
            'original_attempt_id': original_attempt.id,
            'question_ids': list(question_ids),
            'time_limit_minutes': None,  # No time limit
        }
    )
    
    # Redirect đến trang làm bài
    if original_attempt.template.level == ExamLevel.TOEIC:
        return redirect("exam:take_toeic_exam", session_id=new_attempt.id)
    return redirect("exam:take_exam", session_id=new_attempt.id)


def get_question_sub_type(question, part):
    """
    Phân loại sub-type cho câu hỏi TOEIC.
    Ví dụ: Part 1 có "Tranh tả người" và "Tranh tả vật"
    """
    if part == "L1":
        # Part 1: Phân loại dựa trên image hoặc tạm thời random
        # Có thể mở rộng sau với ML hoặc manual tagging
        # Tạm thời: phân loại dựa trên order (chẵn/lẻ) hoặc image
        if question.image:
            # Có thể phân tích image sau, tạm thời random
            return "people" if (question.order or 0) % 2 == 0 else "objects"
        return "people" if (question.order or 0) % 2 == 0 else "objects"
    elif part == "L3":
        # Part 3: Có thể phân loại theo conversation
        return "conversation"
    elif part == "L4":
        # Part 4: Có thể phân loại theo talk type
        return "short_talk"
    elif part == "R6":
        # Part 6: Có thể phân loại theo passage
        return "text_completion"
    elif part == "R7":
        # Part 7: Có thể phân loại theo passage type
        return "reading_comprehension"
    else:
        return "general"


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


@login_required
def take_toeic_exam(request, session_id):
    """
    View riêng cho TOEIC exam với layout đặc biệt:
    - Part 1-5: MCQ bình thường
    - Part 6-7: Split screen (image passage + questions)
    """
    attempt = get_object_or_404(
        ExamAttempt,
        id=session_id,
        user=request.user,
    )
    template = attempt.template

    # Kiểm tra xem có phải TOEIC không
    if template.level != ExamLevel.TOEIC:
        # Nếu không phải TOEIC, redirect về view cũ
        return redirect("exam:take_exam", session_id=session_id)

    # Lấy questions dựa trên attempt data (nếu là practice mode với selected_parts)
    attempt_data = getattr(attempt, 'data', None) or {}
    selected_parts = attempt_data.get('selected_parts', [])
    redo_question_ids = attempt_data.get('question_ids', [])  # For redo_wrong mode
    
    if redo_question_ids:
        # Redo wrong mode: chỉ lấy các câu sai cần làm lại
        questions = (
            template.questions
            .filter(id__in=redo_question_ids)
            .select_related("passage", "listening_conversation", "listening_conversation__template")
            .prefetch_related("listening_conversation__questions")
            .order_by("toeic_part", "order", "id")
        )
    elif selected_parts:
        # Practice mode: chỉ lấy questions của các part được chọn
        questions = (
            template.questions
            .filter(toeic_part__in=selected_parts)
            .select_related("passage", "listening_conversation", "listening_conversation__template")
            .prefetch_related("listening_conversation__questions")
            .order_by("toeic_part", "order", "id")
        )
    else:
        # Full test: lấy tất cả questions
        questions = (
            template.questions
            .select_related("passage", "listening_conversation", "listening_conversation__template")
            .prefetch_related("listening_conversation__questions")
            .order_by("toeic_part", "order", "id")
        )
    
    # Prefetch passage images to support multi-image passages (TOEIC R6/R7)
    questions = questions.prefetch_related("passage__images")

    # Xử lý submit
    if request.method == "POST" and attempt.status != ExamAttempt.Status.SUBMITTED:
        correct = 0

        for q in questions:
            field_name = f"q{q.id}"
            raw_value = request.POST.get(field_name)

            raw_answer = {}
            is_correct = False

            if q.question_type == QuestionType.MCQ:
                selected_key = (raw_value or "").strip()
                raw_answer = {"selected_key": selected_key}
                is_correct = bool(selected_key) and (selected_key == q.correct_answer)

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
        
        # Check for badges
        from core.badge_service import check_and_award_badges
        new_badges = check_and_award_badges(request.user)
        
        if new_badges:
            badges_data = []
            for gb in new_badges:
                badges_data.append({
                    "name": gb.name,
                    "description": gb.description,
                    "icon": gb.icon
                })
            request.session['new_badges'] = badges_data
            
        return redirect("exam:exam_result", session_id=attempt.id)

    # Lấy passages cho Part 6, 7
    passages = (
        template.passages
        .select_related()
        .order_by("order", "id")
    )
    
    # Group questions theo TOEIC part
    parts_data = {}
    for q in questions:
        part = q.toeic_part or ""
        if part not in parts_data:
            parts_data[part] = {
                "part": part,
                "part_display": q.get_toeic_part_display() if part else "Unknown",
                "questions": [],
                "conversations": {},  # Cho Part 3, 4
                "passages": {},  # Cho Part 6, 7
            }
        
        # Thêm flag để kiểm tra xem text có ý nghĩa không (không phải là instruction mẫu)
        q.has_meaningful_text = bool(q.text) and not (
            q.text.startswith("Select the best option to fill") or
            q.text.startswith("Select the best sentence to") or
            q.text.startswith("Select the best answer")
        )
        
        parts_data[part]["questions"].append(q)
        
        # Group theo conversation (Part 3, 4)
        if q.listening_conversation:
            conv = q.listening_conversation
            conv_key = f"{conv.toeic_part}_{conv.order}"
            if conv_key not in parts_data[part]["conversations"]:
                # Refresh conversation from DB to ensure image field is up-to-date
                # Only refresh once per conversation, not for every question
                conv.refresh_from_db()
                parts_data[part]["conversations"][conv_key] = {
                    "conversation": conv,
                    "questions": [],
                }
            parts_data[part]["conversations"][conv_key]["questions"].append(q)
        
        # Group theo passage (Part 6, 7)
        if q.passage:
            passage = q.passage
            passage_key = f"{passage.order}"
            if passage_key not in parts_data[part]["passages"]:
                parts_data[part]["passages"][passage_key] = {
                    "passage": passage,
                    "questions": [],
                }
            parts_data[part]["passages"][passage_key]["questions"].append(q)
    
    # Sắp xếp questions trong mỗi part theo order
    for part_data in parts_data.values():
        part_data["questions"].sort(key=lambda q: (q.order, q.id))
        # Sắp xếp conversations
        for conv_data in part_data["conversations"].values():
            conv_data["questions"].sort(key=lambda q: (q.order, q.id))
        # Sắp xếp passages
        for passage_data in part_data["passages"].values():
            passage_data["questions"].sort(key=lambda q: (q.order, q.id))

    # Sắp xếp parts theo thứ tự: L1, L2, L3, L4, R5, R6, R7
    part_order = [TOEICPart.LISTENING_1, TOEICPart.LISTENING_2, TOEICPart.LISTENING_3,
                  TOEICPart.LISTENING_4, TOEICPart.READING_5, TOEICPart.READING_6, TOEICPart.READING_7]
    parts_list = []
    for part_code in part_order:
        if part_code in parts_data:
            parts_list.append(parts_data[part_code])

    # Tính thời gian
    is_listening = any(p["part"] in [TOEICPart.LISTENING_1, TOEICPart.LISTENING_2, 
                                     TOEICPart.LISTENING_3, TOEICPart.LISTENING_4] 
                      for p in parts_list)
    is_reading = any(p["part"] in [TOEICPart.READING_5, TOEICPart.READING_6, TOEICPart.READING_7] 
                    for p in parts_list)
    
    # Check if this is redo_wrong mode
    is_redo_mode = attempt_data.get('mode') == 'redo_wrong'
    
    # Tính thời gian (0 for redo mode = no timer)
    if is_redo_mode:
        total_minutes = 0  # No timer for redo mode
    elif template.is_full_toeic:
        # Full test: có cả listening và reading
        total_minutes = (template.listening_time_limit_minutes or 45) + (template.reading_time_limit_minutes or 75)
    elif is_listening:
        total_minutes = template.listening_time_limit_minutes or template.time_limit_minutes or 45
    elif is_reading:
        total_minutes = template.reading_time_limit_minutes or template.time_limit_minutes or 75
    else:
        total_minutes = template.time_limit_minutes or 120

    # Serialize parts_list for JavaScript (bao gồm audio URLs)
    parts_list_json = []
    for part_data in parts_list:
        part_json = {
            "part": part_data["part"],
            "part_display": part_data["part_display"],
            "question_count": len(part_data["questions"]),
        }
        
        # Thêm audio URLs cho Listening parts
        if part_data["part"] in [TOEICPart.LISTENING_1, TOEICPart.LISTENING_2]:
            # Part 1, 2: Audio từ từng question
            audio_urls = []
            for q in part_data["questions"]:
                if q.audio:
                    audio_urls.append({
                        "question_id": q.id,
                        "url": q.audio.url,
                    })
            part_json["audio_urls"] = audio_urls
        elif part_data["part"] in [TOEICPart.LISTENING_3, TOEICPart.LISTENING_4]:
            # Part 3, 4: Audio từ conversations
            audio_urls = []
            for conv_key, conv_data in part_data["conversations"].items():
                if conv_data["conversation"].audio:
                    audio_urls.append({
                        "conversation_id": conv_data["conversation"].id,
                        "url": conv_data["conversation"].audio.url,
                    })
            part_json["audio_urls"] = audio_urls
        
        parts_list_json.append(part_json)

    return render(
        request,
        "exam/toeic_exam_take.html",
        {
            "session": attempt,
            "template_obj": template,
            "parts_list": parts_list,
            "parts_list_json": mark_safe(json.dumps(parts_list_json)),
            "total_questions": questions.count(),
            "total_minutes": total_minutes,
            "is_redo_mode": is_redo_mode,
        },
    )
