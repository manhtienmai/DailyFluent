from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
import json

from collections import OrderedDict

from .models import (
    ExamTemplate,
    ExamAttempt,
    ExamQuestion,
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

    # Get user's study language for filtering
    study_lang = 'en'
    if request.user.is_authenticated:
        try:
            from core.models import UserProfile
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                study_lang = profile.study_language or 'en'
        except Exception:
            pass

    # Map study language to exam levels
    EN_LEVELS = ["TOEIC"]
    JP_LEVELS = ["N5", "N4", "N3", "N2", "N1"]
    allowed_levels = EN_LEVELS if study_lang == 'en' else JP_LEVELS

    templates = ExamTemplate.objects.filter(
        is_active=True, level__in=allowed_levels
    ).annotate(
        attempt_count=Count('attempts', filter=Q(attempts__status=ExamAttempt.Status.SUBMITTED))
    ).order_by('title')
    
    if selected_level:
        templates = templates.filter(level=selected_level)

    levels = allowed_levels

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
            "study_lang": study_lang,
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

    group_has_any_attempt = {}
    for g in pattern_groups:
        has_any = False
        for t in g["tests"]:
            if getattr(t, "user_attempts", []):
                has_any = True
                break
        group_has_any_attempt[g["lesson_index"]] = has_any

    context = {
        "book": book,
        "day_tests": day_tests,
        "pattern_groups": pattern_groups,
        "standalone_tests": standalone_tests,
        "group_has_any_attempt": group_has_any_attempt,
        # Helper: check list has data
        "has_day_tests": bool(day_tests),
        "has_pattern_tests": bool(pattern_tests),
        "has_standalone_tests": bool(standalone_tests),
    }

    return render(request, "exam/book_detail.html", context)


# -----------------------------------------------------------
# CHOUKAI VIEWS (Listening)
# -----------------------------------------------------------

def choukai_book_list(request):
    """
    List all books with category=CHOUKAI.
    Similar to book_list but specialized for listening layout.
    """
    from django.db.models import Count, Prefetch
    
    selected_level = request.GET.get("level") or ""
    
    qs = ExamBook.objects.filter(
        category=ExamCategory.CHOUKAI,
        is_active=True
    ).order_by("level", "title")
    
    if selected_level:
        qs = qs.filter(level=selected_level)
    
    # Pre-fetch templates/questions for counts
    bk_qs = qs.prefetch_related(
        Prefetch(
            'tests',
            queryset=ExamTemplate.objects.filter(is_active=True),
            to_attr='active_templates'
        )
    )

    books = []
    for b in bk_qs:
        # Choukai books typically have 1 hidden template
        tpl = b.active_templates[0] if b.active_templates else None
        b.question_count = tpl.questions.count() if tpl else 0
        
        # Determine mondai tags from questions (expensive but useful)
        # or simplified approach:
        b.mondai_tags = []
        if tpl:
            # We can grab distinct mondai values
            distinct_mondai = tpl.questions.values_list('mondai', flat=True).distinct().order_by('mondai')
            b.mondai_tags = list(distinct_mondai)
            
        books.append(b)
    
    # Hardcoded valid JLPT levels
    valid_levels = ["N1", "N2", "N3", "N4", "N5"]
    
    context = {
        "books": books,
        "selected_level": selected_level,
        "levels": valid_levels,
    }
    return render(request, "exam/choukai/book_list.html", context)


def choukai_book_detail(request, slug):
    """
    Detail page for a Choukai Book.
    Shows list of questions grouped by Mondai.
    """
    book = get_object_or_404(ExamBook, slug=slug, category=ExamCategory.CHOUKAI, is_active=True)
    
    # Get the template (Choukai books have 1 main template)
    template = book.tests.filter(is_active=True).first()
    
    questions = []
    mondai_groups = []
    
    if template:
        questions = template.questions.select_related("listening_conversation").order_by("mondai", "order_in_mondai", "order")
        mondai_groups = build_mondai_groups(questions)
        
    context = {
        "book": book,
        "template": template,
        "mondai_groups": mondai_groups,
    }
    return render(request, "exam/choukai/book_detail.html", context)


@require_POST
def choukai_save_answer(request):
    """
    API to save progress for Choukai practice.
    Expects JSON: { question_id: 123, is_correct: true/false }
    """
    if not request.user.is_authenticated:
         # For anonymous users, we might just return success (client-side storage only)
         return JsonResponse({'success': True, 'msg': 'Anonymous saved (local only)'})
         
    try:
        data = json.loads(request.body)
        qid = data.get('question_id')
        is_correct = data.get('is_correct', False)
        
        if not qid:
            return JsonResponse({'error': 'Missing question_id'}, status=400)
            
        # Log to QuestionAnswer if inside an Attempt? 
        # For choukai library mode (book_detail), it might be ad-hoc practice.
        # We'll implement a simple usage log or skip for now if not in an ExamAttempt.
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
