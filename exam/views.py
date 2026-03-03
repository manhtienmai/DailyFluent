from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import json
import os
import uuid
import base64
import re
from collections import OrderedDict

# Import models
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
from config.storage_backends import AzureMediaStorage

# ==============================================================================
#  1. CHOUKAI TOOL API (Logic lõi - Dùng chung cho cả Script & Admin)
# ==============================================================================

class ChoukaiToolAPI(View):
    """
    Class chứa toàn bộ logic xử lý API.
    LƯU Ý: Đã gắn @csrf_exempt trực tiếp vào từng hàm để tránh lỗi 403.
    """

    ANALYZE_SYSTEM_PROMPT = (
        "Role: You are an AI specialized in Japanese OCR with furigana (ruby) extraction.\n"
        "Task: Analyze the input image, classify it, extract text options WITH furigana, and return strict JSON.\n\n"
        "CLASSIFICATION LOGIC:\n"
        "1. \"SCENE_WITH_OPTIONS\" — Illustration + numbered text options\n"
        "2. \"SCENE_ONLY\"         — Illustration only, no text options\n"
        "3. \"TEXT_OPTIONS_ONLY\"  — Numbered text options, no illustration\n\n"
        "FURIGANA EXTRACTION RULES (CRITICAL):\n"
        "- If a kanji/word has furigana (small kana printed above or below it) in the image, "
        "encode it as {漢字}(ふりがな). Example: {会議}(かいぎ), {走}(はし)る\n"
        "- Only encode furigana that is VISUALLY PRESENT in the image. "
        "Do NOT add furigana that is not shown.\n"
        "- Kana-only words (no furigana shown) are written as plain text. Example: います, ている\n"
        "- Mixed example: {電話}(でんわ)をしています → kanji {電話} has ruby, をしています is plain\n\n"
        "GHIBLI PROMPT RULES (CRITICAL):\n"
        "- JLPT listening images often have a black-bordered square or rectangle containing the main illustration.\n"
        "- For \"ghibli_prompt\": describe ONLY the scene content INSIDE that black border.\n"
        "- Completely ignore: question numbers, answer option labels (1/2/3/4), text outside the border, "
        "page layout, background outside the bordered area.\n"
        "- Describe characters, objects, setting, actions visible within the bordered illustration frame.\n"
        "- If there is no bordered illustration area, set \"ghibli_prompt\" to null.\n\n"
        "OUTPUT JSON FORMAT:\n"
        "{\n"
        "  \"type\": \"SCENE_WITH_OPTIONS\" | \"SCENE_ONLY\" | \"TEXT_OPTIONS_ONLY\",\n"
        "  \"ghibli_prompt\": \"English scene description of content inside the black-bordered illustration only, or null\",\n"
        "  \"data\": {\n"
        "    \"options\": [\n"
        "      { \"label\": \"1\", \"content\": \"{会議}(かいぎ)をしています\" },\n"
        "      { \"label\": \"2\", \"content\": \"{電話}(でんわ)をかけています\" }\n"
        "    ]\n"
        "  }\n"
        "}\n"
        "STRICT JSON only. No markdown. No trailing commas."
    )

    def _get_or_create_choukai_template(self, book):
        template, _ = ExamTemplate.objects.get_or_create(
            book=book,
            category=ExamCategory.CHOUKAI,
            defaults={
                'title': f'Choukai - {book.title}',
                'level': book.level,
            },
        )
        return template

    # --- API: LOAD DATA ---
    def choukai_load_questions_api(self, request):
        """GET: Load danh sách câu hỏi (Dùng cho Admin JS)."""
        book_id = request.GET.get('book_id')
        mondai = request.GET.get('mondai', '')
        if not book_id:
            return JsonResponse({'questions': []})
        
        qs = ExamQuestion.objects.filter(
            template__book_id=int(book_id),
            template__category=ExamCategory.CHOUKAI,
        ).order_by('mondai', 'order_in_mondai', 'order')
        
        if mondai:
            qs = qs.filter(mondai=mondai)
            
        return JsonResponse({'questions': [
            {
                'id': q.id,
                'order': q.order,
                'mondai': q.mondai,
                'order_in_mondai': q.order_in_mondai,
                'text': q.text,
                'text_vi': q.text_vi,
                'audio_url': q.audio.url if q.audio else '',
                'image_url': q.image.url if q.image else '',
                'ghibli_url': (q.data or {}).get('ghibli_image_url', ''),
                'image_type': (q.data or {}).get('image_type', ''),
                'audio_transcript': q.audio_transcript,
                'audio_transcript_vi': q.audio_transcript_vi,
                'data': q.data,
                'correct_answer': q.correct_answer,
            }
            for q in qs
        ]})

    # --- API: PROCESS IMAGE ---
    
    @csrf_exempt
    def choukai_analyze_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'success': True, 'type': None, 'data': {'options': []}})
            
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime_type = image_file.content_type or 'image/png'
            
            # --- FIX IMPORT: Trỏ đúng về vocab.services ---
            from vocab.services.gemini_service import GeminiService 
            raw = GeminiService.generate_with_image(self.ANALYZE_SYSTEM_PROMPT, image_bytes, mime_type, model_name='gemini-2.0-flash')
            
            # Clean JSON Response
            clean = raw.strip()
            # 1. Remove Markdown block
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean)
            if m: clean = m.group(1).strip()
            # 2. Remove leading/trailing text outside {}
            start = clean.find('{')
            end = clean.rfind('}')
            if start != -1 and end != -1:
                clean = clean[start:end+1]

            return JsonResponse(json.loads(clean) | {'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def choukai_ocr_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime = image_file.content_type or 'image/png'
            
            from vocab.services.gemini_service import GeminiService
            prompt = "OCR this Japanese text. Return raw text."
            text = GeminiService.generate_with_image(prompt, image_bytes, mime, model_name='gemini-2.0-flash')
            return JsonResponse({'success': True, 'text': text})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # --- API: PROCESS TEXT ---
    
    @csrf_exempt
    def choukai_translate_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            # Mặc định dùng flash cho nhanh, nhưng nếu cần thông minh hơn có thể dùng pro
            model_name = data.get('model', 'gemini-2.0-flash') 
            level = data.get('level', 'N3').upper()
            if not text: return JsonResponse({'error': 'No text'}, status=400)
            
            # Prompt được tinh chỉnh để Gemini ít sai JSON hơn
            prompt = (
                f"You are a Japanese teacher ({level}). Process this transcript.\n"
                "1. Identify speakers [F]/[M].\n2. Segment text.\n"
                "3. Add furigana {漢字}(kana) for difficult words.\n4. Translate to Vietnamese.\n"
                f"Input:\n{text}\n\n"
                "OUTPUT JSON:\n{ \"conversation\": [ { \"speaker\": \"F\", \"text\": \"...\", \"text_vi\": \"...\" } ] }\n"
                "STRICT JSON. NO Trailing Commas. NO Markdown."
            )
            from vocab.services.gemini_service import GeminiService
            result_raw = GeminiService.generate_text(prompt, model_name=model_name)
            
            # --- LOGIC CLEAN JSON MẠNH MẼ HƠN ---
            clean_json = result_raw.strip()
            
            # 1. Cố gắng lấy nội dung trong ```json ... ```
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean_json)
            if match: 
                clean_json = match.group(1).strip()
            
            # 2. Nếu vẫn còn rác ở đầu/cuối, tìm cặp ngoặc nhọn ngoài cùng
            start_idx = clean_json.find('{')
            end_idx = clean_json.rfind('}')
            if start_idx != -1 and end_idx != -1:
                clean_json = clean_json[start_idx : end_idx + 1]

            # 3. Fix lỗi dấu phẩy thừa (Trailing Comma) thường gặp ở Gemini
            # Xóa dấu phẩy trước dấu đóng ] hoặc }
            clean_json = re.sub(r',\s*([\]}])', r'\1', clean_json)

            try:
                parsed_result = json.loads(clean_json)
            except json.JSONDecodeError:
                # Nếu vẫn lỗi, thử dùng eval (nguy hiểm nhưng xử lý được 1 số lỗi quote) 
                # hoặc trả về lỗi kèm raw text để debug
                print(f"FAILED JSON RAW: {clean_json}") # In ra terminal server để debug
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid JSON format from Gemini', 
                    'raw_preview': clean_json[:100] + '...'
                }, status=500)
            
            return JsonResponse({'success': True, 'conversation': parsed_result.get('conversation', [])})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

    @csrf_exempt
    def choukai_furigana_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            data = json.loads(request.body)
            texts = data.get('texts', [])
            return JsonResponse({'success': True, 'texts': texts}) # Placeholder
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # --- API: GENERATE & UPLOAD ---
    
    @csrf_exempt
    def choukai_ghibli_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            img_bytes = None
            if 'image' in request.FILES:
                img_bytes = request.FILES['image'].read()
            
            user_prompt = request.POST.get('prompt') or "A scene from a Japanese listening test illustration."
            # Prefix instruction: focus only on the content inside the black-bordered frame
            prefix = (
                "Generate a Studio Ghibli style illustration. "
                "If a reference image is provided, reproduce ONLY the scene shown inside the black-bordered "
                "square or rectangle frame. Do NOT include any text, question numbers, answer labels, "
                "or any content that appears outside that bordered area. "
                "Scene to illustrate: "
            )
            prompt = prefix + user_prompt

            from vocab.services.gemini_service import GeminiService
            res_bytes, mime = GeminiService.generate_image(prompt, ref_image_bytes=img_bytes)
            
            if not res_bytes: return JsonResponse({'success': False, 'error': mime})
            b64 = base64.b64encode(res_bytes).decode()
            return JsonResponse({'success': True, 'image_b64': b64, 'mime_type': mime})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def choukai_upload_audio_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            f = request.FILES['audio']
            path = request.POST.get('path') or f"exam/choukai/{uuid.uuid4().hex}.mp3"
            storage = AzureMediaStorage()
            name = storage.save(path, f)
            return JsonResponse({'success': True, 'url': storage.url(name)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # --- API: SAVE ---
    
    @csrf_exempt
    def choukai_save_question_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            book = ExamBook.objects.get(pk=d['book_id'])
            tpl = self._get_or_create_choukai_template(book)
            
            q_id = d.get('question_id')
            if q_id: q = ExamQuestion.objects.get(pk=q_id)
            else: q = ExamQuestion(template=tpl, order=tpl.questions.count()+1)
            
            q.mondai = d.get('mondai', '')
            q.order_in_mondai = d.get('order_in_mondai', 1)
            q.text = d.get('text', '')
            q.text_vi = d.get('text_vi', '')
            q.correct_answer = d.get('correct_answer', '1')
            q.audio_transcript = d.get('audio_transcript', '')
            q.audio_transcript_vi = d.get('audio_transcript_vi', '')
            q.question_type = QuestionType.MCQ
            if d.get('audio_url'): q.audio = d.get('audio_url')
            
            q_data = d.get('data', {})
            if d.get('conversation'): q_data['conversation'] = d['conversation']
            if d.get('image_type'): q_data['image_type'] = d['image_type']
            if d.get('answer_options'): q_data['answer_options'] = d['answer_options'] 
            # Support choices
            if d.get('choices'): q_data['choices'] = d['choices']
            
            q.data = q_data

            if d.get('image_b64'):
                ib = base64.b64decode(d['image_b64'])
                ext = '.png' if 'png' in d.get('image_mime','') else '.jpg'
                fname = f"exam/choukai/img_{uuid.uuid4().hex[:8]}{ext}"
                q.image.name = default_storage.save(fname, ContentFile(ib))
            
            q.save()
            return JsonResponse({'success': True, 'question_id': q.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def choukai_create_book_api(self, request):
        if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            b = ExamBook.objects.create(
                title=d.get('title'), level=d.get('level', 'N2'),
                category=ExamCategory.CHOUKAI, is_active=True
            )
            return JsonResponse({'success': True, 'id': b.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Khởi tạo instance cho urls.py dùng
choukai_tool_instance = ChoukaiToolAPI()


# ==============================================================================
#  2. CHOUKAI MIXIN (Dành cho Django Admin - VocabularyAdmin)
# ==============================================================================

class ChoukaiToolMixin:
    CHOUKAI_MONDAI_TYPES = [
        ('1', 'もんだい1 課題理解'),
        ('2', 'もんだい2 ポイント理解'),
        ('3', 'もんだい3 概要理解'),
        ('4', 'もんだい4 発話表現'),
        ('5', 'もんだい5 即時応答'),
    ]

    def choukai_tool_view(self, request):
        books = ExamBook.objects.filter(category=ExamCategory.CHOUKAI).order_by('title')
        context = dict(
            self.admin_site.each_context(request),
            title="Choukai Data Preparation Tool",
            books=books,
            mondai_types=self.CHOUKAI_MONDAI_TYPES,
        )
        return render(request, "admin/vocab/vocabulary/choukai_tool.html", context)

    # --- PROXY METHODS (Kết nối Admin -> API Class) ---
    def choukai_load_questions_api(self, request): return choukai_tool_instance.choukai_load_questions_api(request)
    def choukai_analyze_api(self, request): return choukai_tool_instance.choukai_analyze_api(request)
    def choukai_ocr_api(self, request): return choukai_tool_instance.choukai_ocr_api(request)
    def choukai_translate_api(self, request): return choukai_tool_instance.choukai_translate_api(request)
    def choukai_furigana_api(self, request): return choukai_tool_instance.choukai_furigana_api(request)
    def choukai_ghibli_api(self, request): return choukai_tool_instance.choukai_ghibli_api(request)
    def choukai_upload_audio_api(self, request): return choukai_tool_instance.choukai_upload_audio_api(request)
    def choukai_save_question_api(self, request): return choukai_tool_instance.choukai_save_question_api(request)
    def choukai_create_book_api(self, request): return choukai_tool_instance.choukai_create_book_api(request)


# ==============================================================================
#  3. STANDARD EXAM VIEWS (Website Logic - Giữ nguyên)
# ==============================================================================

def build_mondai_groups(questions):
    groups = []
    current_mondai = None
    current_questions = []
    for q in questions:
        mondai = q.mondai or ""
        if current_mondai is None: current_mondai = mondai
        if mondai != current_mondai:
            groups.append({"mondai": current_mondai, "questions": current_questions})
            current_mondai = mondai
            current_questions = []
        current_questions.append(q)
    if current_questions:
        groups.append({"mondai": current_mondai, "questions": current_questions})
    
    for g in groups:
        qs = g["questions"]
        has_passage = any(q.passage_id for q in qs)
        g["is_dokkai"] = has_passage
        passage_map = {}
        non_passage = []
        if has_passage:
            for q in qs:
                if q.passage_id:
                    p = q.passage
                    if p.id not in passage_map: passage_map[p.id] = {"passage": p, "questions": []}
                    passage_map[p.id]["questions"].append(q)
                else: non_passage.append(q)
            g["passage_groups"] = sorted(passage_map.values(), key=lambda item: (item["passage"].order, item["passage"].id))
        else:
            g["passage_groups"] = []
            non_passage = qs
        g["non_passage_questions"] = non_passage
    return groups

def exam_list(request):
    from django.core.paginator import Paginator
    selected_level = request.GET.get("level") or ""
    study_lang = 'en'
    if request.user.is_authenticated:
        try:
            from core.models import UserProfile
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile: study_lang = profile.study_language or 'en'
        except: pass
    
    EN_LEVELS = ["TOEIC"]
    JP_LEVELS = ["N5", "N4", "N3", "N2", "N1"]
    allowed_levels = EN_LEVELS if study_lang == 'en' else JP_LEVELS
    
    templates = ExamTemplate.objects.filter(is_active=True, level__in=allowed_levels)\
        .annotate(attempt_count=Count('attempts', filter=Q(attempts__status=ExamAttempt.Status.SUBMITTED)))\
        .order_by('title')
    
    if selected_level: templates = templates.filter(level=selected_level)
    
    paginator = Paginator(templates, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, "exam/exam_list.html", {
        "templates": page_obj, "page_obj": page_obj, "total_exams": paginator.count,
        "selected_level": selected_level, "levels": allowed_levels, "study_lang": study_lang,
    })

@login_required
def toeic_list(request):
    templates = ExamTemplate.objects.filter(is_active=True, level=ExamLevel.TOEIC)\
        .annotate(attempt_count=Count('attempts', filter=Q(attempts__status=ExamAttempt.Status.SUBMITTED)))\
        .prefetch_related('questions').order_by("-created_at")
    for t in templates:
        parts = t.questions.exclude(toeic_part="").values_list('toeic_part', flat=True).distinct()
        t.parts_count = len(list(parts)) or (7 if t.category == ExamCategory.TOEIC_FULL else 0)
    
    return render(request, "exam/toeic_list.html", {
        "templates": templates,
        "full_tests": templates.filter(category=ExamCategory.TOEIC_FULL),
        "listening_tests": templates.filter(category=ExamCategory.LISTENING),
        "reading_tests": templates.filter(category=ExamCategory.READING),
    })

def exam_detail(request, slug):
    from django.contrib import messages
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get('action') == 'add_comment':
            c = request.POST.get('content', '').strip()
            if c and len(c) <= 2000:
                ExamComment.objects.create(template=template, user=request.user, content=c)
                messages.success(request, "Success")
            return redirect('exam:exam_detail', slug=slug)
    
    attempt_count = ExamAttempt.objects.filter(template=template, status=ExamAttempt.Status.SUBMITTED).count()
    comments = ExamComment.objects.filter(template=template, is_active=True).select_related('user').order_by('-created_at')[:50]
    
    parts_list = []
    if template.level == ExamLevel.TOEIC:
        distinct_parts = template.questions.exclude(toeic_part="").values_list('toeic_part', flat=True).distinct().order_by('toeic_part')
        for p in distinct_parts:
            parts_list.append({
                'part': p, 'part_display': dict(TOEICPart.choices).get(p, p),
                'question_count': template.questions.filter(toeic_part=p).count()
            })
            
    return render(request, 'exam/exam_detail.html', {
        'template': template, 'attempt_count': attempt_count,
        'comment_count': comments.count(), 'comments': comments, 'parts_list': parts_list
    })

@login_required
def start_exam(request, slug):
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True)
    mode = request.POST.get('mode', 'full_test')
    parts = request.POST.getlist('selected_parts')
    
    questions = template.questions.all()
    if mode == 'practice' and parts:
        questions = questions.filter(toeic_part__in=parts)
        
    attempt = ExamAttempt.objects.create(user=request.user, template=template, total_questions=questions.count())
    attempt.data = {'mode': mode, 'selected_parts': parts if mode == 'practice' else []}
    attempt.save()
    
    if template.level == ExamLevel.TOEIC: return redirect("exam:take_toeic_exam", session_id=attempt.id)
    return redirect("exam:take_exam", session_id=attempt.id)

@login_required
def take_exam(request, session_id):
    attempt = get_object_or_404(ExamAttempt, id=session_id, user=request.user)
    if request.method == "POST" and attempt.status != ExamAttempt.Status.SUBMITTED:
        correct = 0
        for q in attempt.template.questions.all():
            val = request.POST.get(f"q{q.id}", "").strip()
            is_cor = (q.question_type == QuestionType.MCQ and val == q.correct_answer)
            QuestionAnswer.objects.update_or_create(
                attempt=attempt, question=q,
                defaults={"raw_answer": {"selected_key": val}, "is_correct": is_cor}
            )
            if is_cor: correct += 1
        
        attempt.correct_count = correct
        attempt.status = ExamAttempt.Status.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.save()
        return redirect("exam:exam_result", session_id=attempt.id)
        
    questions = attempt.template.questions.select_related("passage").order_by("mondai", "order_in_mondai", "order")
    return render(request, "exam/exam_take.html", {
        "session": attempt, "template_obj": attempt.template,
        "questions": questions, "mondai_groups": build_mondai_groups(questions)
    })

@login_required
def exam_result(request, session_id):
    attempt = get_object_or_404(ExamAttempt, id=session_id, user=request.user, status=ExamAttempt.Status.SUBMITTED)
    answers = list(attempt.answers.select_related("question").order_by("question__toeic_part", "question__order"))
    
    answers_json = []
    for ans in answers:
        q = ans.question
        answers_json.append({
            "id": ans.id, "is_correct": ans.is_correct,
            "question": {
                "id": q.id, "text": q.text, "correct_answer": q.correct_answer,
                "image": q.image.url if q.image else None, "audio": q.audio.url if q.audio else None,
                "mcq_choices": q.mcq_choices
            },
            "raw_answer": ans.raw_answer
        })
        
    return render(request, "exam/exam_result.html", {
        "session": attempt, "template_obj": attempt.template,
        "answers": answers, "answers_json": json.dumps(answers_json),
        "wrong_count": attempt.total_questions - attempt.correct_count
    })

@login_required
def exam_result_question_detail(request, session_id, question_id):
    attempt = get_object_or_404(ExamAttempt, id=session_id, user=request.user)
    ans = get_object_or_404(attempt.answers, question_id=question_id)
    q = ans.question
    return JsonResponse({
        "question": {"id": q.id, "text": q.text, "text_vi": getattr(q, 'text_vi', '')},
        "answer": {"is_correct": ans.is_correct, "selected_key": ans.raw_answer.get("selected_key")}
    })

@login_required
def redo_wrong_questions(request, session_id):
    orig = get_object_or_404(ExamAttempt, id=session_id, user=request.user)
    q_ids = [int(x) for x in request.POST.getlist('question_ids') if x.isdigit()]
    if not q_ids: return redirect("exam:exam_result", session_id=session_id)
    
    new_att = ExamAttempt.objects.create(
        user=request.user, template=orig.template, total_questions=len(q_ids),
        data={'mode': 'redo_wrong', 'question_ids': q_ids}
    )
    url = "exam:take_toeic_exam" if orig.template.level == ExamLevel.TOEIC else "exam:take_exam"
    return redirect(url, session_id=new_att.id)

def get_question_sub_type(question, part):
    if part == "L1": return "people" if (question.order or 0)%2==0 else "objects"
    if part == "L3": return "conversation"
    return "general"

def book_list(request):
    qs = ExamBook.objects.filter(is_active=True).prefetch_related("tests")
    lvl = request.GET.get("level")
    if lvl: qs = qs.filter(level=lvl)
    q = request.GET.get("q")
    if q: qs = qs.filter(title__icontains=q)
    return render(request, "exam/book_list.html", {"books": qs, "selected_level": lvl, "search_query": q or ""})

def book_detail(request, slug):
    book = get_object_or_404(ExamBook, slug=slug, is_active=True)
    tests = book.tests.filter(is_active=True).order_by("group_type", "lesson_index")
    return render(request, "exam/book_detail.html", {"book": book, "day_tests": tests.filter(group_type=ExamGroupType.BY_DAY)})

# --- CHOUKAI WEB VIEWS ---
def choukai_book_list(request):
    selected_level = request.GET.get('level', '').strip()
    levels = ['N5', 'N4', 'N3', 'N2', 'N1']

    qs = ExamBook.objects.filter(category=ExamCategory.CHOUKAI, is_active=True)
    if selected_level:
        qs = qs.filter(level=selected_level)
    qs = qs.order_by('level', 'title')

    # Annotate question_count via related ExamTemplate questions
    qs = qs.annotate(
        question_count=Count(
            'tests__questions',
            filter=Q(tests__is_active=True, tests__category=ExamCategory.CHOUKAI),
            distinct=True,
        )
    )

    return render(request, 'exam/choukai/book_list.html', {
        'books': qs,
        'selected_level': selected_level,
        'levels': levels,
    })


_MONDAI_LABELS = {'1': 'もんだい1 課題理解', '2': 'もんだい2 ポイント理解', '3': 'もんだい3 概要理解', '4': 'もんだい4 発話表現', '5': 'もんだい5 即時応答'}
from exam.utils import ruby_to_html as _ruby, audio_url as _audio_url

def choukai_book_detail(request, slug):
    book = get_object_or_404(ExamBook, slug=slug, category=ExamCategory.CHOUKAI)
    tpl = book.tests.filter(is_active=True, category=ExamCategory.CHOUKAI).first()

    # Build lightweight group summaries (no full question data)
    groups = []
    total_questions = 0
    if tpl:
        qs = tpl.questions.order_by("mondai", "order_in_mondai")
        cur_k, cur_ids = None, []
        for q in qs:
            m = q.mondai or "0"
            if m != cur_k:
                if cur_k is not None:
                    groups.append({
                        "key": cur_k,
                        "label": _MONDAI_LABELS.get(cur_k, cur_k),
                        "count": len(cur_ids),
                        "qids": cur_ids,
                    })
                cur_k, cur_ids = m, []
            cur_ids.append({"id": q.id, "num": q.order_in_mondai, "correct": q.correct_answer})
        if cur_k is not None:
            groups.append({
                "key": cur_k,
                "label": _MONDAI_LABELS.get(cur_k, cur_k),
                "count": len(cur_ids),
                "qids": cur_ids,
            })
        total_questions = sum(g["count"] for g in groups)

    first_key = groups[0]["key"] if groups else ""

    # Load previous answers for authenticated users
    initial_answers = {}
    if request.user.is_authenticated and tpl:
        attempt = ExamAttempt.objects.filter(
            user=request.user,
            template=tpl,
            status=ExamAttempt.Status.IN_PROGRESS,
        ).first()
        if attempt:
            for qa in attempt.answers.all():
                initial_answers[str(qa.question_id)] = qa.raw_answer.get('selected_key', '')

    return render(request, "exam/choukai/book_detail.html", {
        "book": book,
        "mondai_groups": groups,
        "total_questions": total_questions,
        "first_key": first_key,
        "initial_answers_json": json.dumps(initial_answers),
    })


def choukai_mondai_api(request, slug, mondai_key):
    """API: return full question data for a single mondai group (lazy-load)."""
    book = get_object_or_404(ExamBook, slug=slug, category=ExamCategory.CHOUKAI)
    tpl = book.tests.filter(is_active=True, category=ExamCategory.CHOUKAI).first()
    if not tpl:
        return JsonResponse({"questions": []})

    qs = tpl.questions.filter(mondai=mondai_key).order_by("order_in_mondai")
    questions = []
    for q in qs:
        d = q.data or {}
        no_image_mondais = {"3", "5"} if book.level == "N3" else set()
        img_url = "" if mondai_key in no_image_mondais or d.get('image_type') == 'TEXT_OPTIONS_ONLY' else (q.image.url if q.image else "")

        questions.append({
            "id": q.id,
            "num": q.order_in_mondai,
            "audio_url": _audio_url(q),
            "image_url": img_url,
            "text": q.text,
            "correct": q.correct_answer,
            "choices": [
                {"key": str(c.get("number")), "html": _ruby(c.get("text"))}
                for c in (d.get("choices") or d.get("answer_options") or [])
            ],
            "lines": [
                {"speaker": l.get("speaker"), "html": _ruby(l.get("text")), "vi": l.get("text_vi")}
                for l in d.get("conversation", [])
            ],
        })

    return JsonResponse({"questions": questions})


@require_POST
def choukai_save_answer(request):
    """Lưu đáp án từng câu choukai vào DB (ExamAttempt + QuestionAnswer)."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': True, 'saved': False})
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        selected_key = str(data.get('selected_key', ''))
        if not question_id or not selected_key:
            return JsonResponse({'success': False, 'error': 'Missing fields'}, status=400)

        question = get_object_or_404(ExamQuestion, pk=question_id)
        template = question.template

        # Lấy hoặc tạo attempt IN_PROGRESS cho user + template này
        attempt, _ = ExamAttempt.objects.get_or_create(
            user=request.user,
            template=template,
            status=ExamAttempt.Status.IN_PROGRESS,
            defaults={'data': {'mode': 'choukai'}},
        )

        is_correct = selected_key == str(question.correct_answer)

        QuestionAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'raw_answer': {'selected_key': selected_key},
                'is_correct': is_correct,
            },
        )

        # Cập nhật thống kê attempt
        agg = attempt.answers.aggregate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
        )
        ExamAttempt.objects.filter(pk=attempt.pk).update(
            total_questions=agg['total'],
            correct_count=agg['correct'],
        )

        return JsonResponse({'success': True, 'saved': True, 'is_correct': is_correct})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==============================================================================
#  4. DOKKAI TOOL API (Logic lõi cho Admin Editor)
# ==============================================================================

def _clean_json(raw: str) -> dict:
    """Parse Gemini JSON response, strip markdown fences and trailing commas."""
    clean = raw.strip()
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean)
    if m:
        clean = m.group(1).strip()
    start = clean.find('{')
    end = clean.rfind('}')
    if start != -1 and end != -1:
        clean = clean[start:end+1]
    clean = re.sub(r',\s*([\]}])', r'\1', clean)
    return json.loads(clean)


def _parse_dokkai_options(options_list):
    """Parse option strings like '1. text' or 'A. text' into [{'key': '1', 'text': 'text'}, ...]."""
    choices = []
    for opt in options_list:
        m = re.match(r'^([A-Da-d1-4])[.）．　\s]+(.+)$', opt.strip(), re.DOTALL)
        if m:
            choices.append({'key': m.group(1), 'text': m.group(2).strip()})
        else:
            choices.append({'key': str(len(choices) + 1), 'text': opt.strip()})
    return choices


class DokkaiToolAPI(View):
    """
    API endpoints for the Dokkai Admin Editor.
    All methods are called via proxy in DokkaiMixin on ExamTemplateAdmin.
    """

    FULL_ANALYZE_PROMPT = (
        "Bạn là một chuyên gia giáo dục ngôn ngữ và luyện thi JLPT. "
        "Nhiệm vụ của bạn là phân tích hình ảnh một bài đọc hiểu (Dokkai) tiếng Nhật "
        "và xuất toàn bộ dữ liệu dưới dạng cấu trúc JSON nghiêm ngặt.\n\n"
        "CÁC QUY TẮC QUAN TRỌNG:\n\n"
        "1. TRÍCH XUẤT VĂN BẢN, FURIGANA & ĐỊNH DẠNG:\n"
        "- Lấy toàn bộ nội dung đoạn văn, câu hỏi, đáp án và các chú thích có trong ảnh.\n"
        "- XUỐNG DÒNG: BẮT BUỘC giữ nguyên cấu trúc tách đoạn, tách dòng y hệt như trong ảnh gốc. "
        "Sử dụng thẻ HTML <br> tại đúng vị trí văn bản bị ngắt dòng trong ảnh.\n"
        "- GẠCH CHÂN & IN ĐẬM: Nếu trong ảnh có đoạn văn bản bị gạch chân hoặc in đậm "
        "(thường phục vụ cho câu hỏi), BẮT BUỘC bao bọc đoạn đó bằng thẻ HTML tương ứng: "
        "<u> cho gạch chân (Ví dụ: <u>đoạn gạch chân</u>) và <b> cho in đậm (Ví dụ: <b>từ in đậm</b>).\n"
        "- FURIGANA: TUYỆT ĐỐI KHÔNG tự sinh thêm furigana cho những từ không có furigana trong ảnh. "
        "Nếu trong ảnh có sẵn furigana, hãy biểu diễn bằng thẻ HTML "
        "(Ví dụ: <ruby>漢字<rt>かんじ</rt></ruby>).\n\n"
        "2. GIẢI THÍCH ĐÁP ÁN:\n"
        "- Giải thích ngắn gọn, súc tích và dễ hiểu.\n"
        "- BẮT BUỘC phải có trích dẫn (quote) một đoạn/câu/từ khóa trực tiếp từ văn bản "
        "để chứng minh tại sao đáp án đó đúng.\n\n"
        "3. SONG NGỮ & TỪ VỰNG:\n"
        "- Tách đoạn văn thành từng câu trọn vẹn. Ở phần này, "
        "TUYỆT ĐỐI KHÔNG dùng thẻ <br> để câu văn được liền mạch, dễ đọc.\n"
        "- Dịch mỗi câu sang tiếng Việt sát với văn phong và ngữ cảnh của bài đọc.\n\n"
        "4. BÓC TÁCH TỪ VỰNG:\n"
        "- Với mỗi câu, trích xuất các từ vựng quan trọng nằm trong phạm vi JLPT N2 "
        "(± 1 level, tức là từ N3 đến N1).\n"
        "- Cung cấp đầy đủ Kanji, Hiragana, và Nghĩa "
        "(ưu tiên nghĩa dùng trong ngữ cảnh của câu, có thể kèm thêm nghĩa phổ biến nếu cần).\n\n"
        "ĐỊNH DẠNG ĐẦU RA (Chỉ trả về JSON hợp lệ, KHÔNG kèm markdown như ```json, "
        "KHÔNG kèm bất kỳ text giải thích nào khác ở ngoài):\n"
        '{\n'
        '  "passage": {\n'
        '    "text": "Nội dung toàn bộ đoạn văn. (Giữ nguyên <br>, <u>, <b>, <ruby><rt></rt></ruby> nếu có)",\n'
        '    "footnotes": ["chú thích 1", "chú thích 2"]\n'
        '  },\n'
        '  "questions": [\n'
        '    {\n'
        '      "question_number": "Số thứ tự câu hỏi (ví dụ: 50, 51)",\n'
        '      "question_text": "Nội dung câu hỏi",\n'
        '      "options": ["1. ...", "2. ...", "3. ...", "4. ..."],\n'
        '      "correct_answer": "1",\n'
        '      "explanation": "Giải thích tại sao đúng. (Trích dẫn: \'...\')",\n'
        '      "quote_from_passage": "Câu/từ khóa trích dẫn trực tiếp từ bài"\n'
        '    }\n'
        '  ],\n'
        '  "bilingual_reading": [\n'
        '    {\n'
        '      "japanese_sentence": "Câu tiếng Nhật liền mạch (sử dụng <ruby> nếu có, KHÔNG dùng <br>)",\n'
        '      "vietnamese_translation": "Nghĩa tiếng Việt của câu này",\n'
        '      "vocabulary": [\n'
        '        {\n'
        '          "kanji": "漢字",\n'
        '          "hiragana": "かんじ",\n'
        '          "meaning": "Chữ Hán (Nghĩa ngữ cảnh / Nghĩa phổ biến)",\n'
        '          "jlpt_level": "N2"\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    OCR_PROMPT = (
        "You are an expert Japanese OCR system specialized in JLPT reading comprehension texts.\n"
        "Task: Extract the full Japanese text from this image.\n\n"
        "FURIGANA FORMAT:\n"
        "- If a kanji/word has furigana (small kana printed above it), encode as {漢字}(ふりがな)\n"
        "  Example: {会議}(かいぎ)、{走}(はし)る\n"
        "- Only encode furigana that is VISUALLY PRESENT in the image.\n"
        "- Kana-only words are written as plain text.\n\n"
        "OUTPUT:\n"
        "Return ONLY the extracted Japanese text with furigana markers.\n"
        "Preserve paragraph breaks with newlines.\n"
        "Do NOT add any commentary or extra formatting."
    )

    EXPLAIN_PROMPT_TEMPLATE = (
        "You are a Japanese language teacher specializing in JLPT reading comprehension.\n"
        "Analyze this reading comprehension question and provide a detailed explanation.\n\n"
        "PASSAGE (context):\n{passage_text}\n\n"
        "QUESTION:\n{question_text}\n\n"
        "CHOICES:\n{choices_text}\n\n"
        "CORRECT ANSWER: {correct_answer}\n\n"
        "Provide explanation in Vietnamese. Return STRICT JSON (no markdown, no trailing commas):\n"
        "{{\n"
        '  "correct_option": "{correct_answer}",\n'
        '  "overall_analysis": {{\n'
        '    "summary": "Tóm tắt giải thích ngắn gọn tại sao đáp án đúng..."\n'
        "  }},\n"
        '  "options_breakdown": {{\n'
        '    "1": {{"text": "...", "status": "correct|wrong", "reason": "..."}},\n'
        '    "2": {{"text": "...", "status": "wrong", "reason": "..."}}\n'
        "  }}\n"
        "}}"
    )

    VOCAB_PROMPT_TEMPLATE = (
        "You are a Japanese language teacher. Extract key vocabulary from this JLPT reading passage.\n"
        "Select words that are important for understanding the passage and useful for JLPT learners.\n\n"
        "PASSAGE:\n{passage_text}\n\n"
        "Return a JSON array (no markdown, no trailing commas) of 8-15 vocabulary items:\n"
        '[\n'
        '  {{"word": "会議", "reading": "かいぎ", "han_viet": "hội nghị", "meaning_vi": "cuộc họp", "type": "danh từ"}},\n'
        '  ...\n'
        ']\n'
        "- word: the Japanese word (kanji form)\n"
        "- reading: hiragana reading\n"
        "- han_viet: Sino-Vietnamese reading (Hán Việt)\n"
        "- meaning_vi: Vietnamese meaning\n"
        "- type: part of speech in Vietnamese (danh từ / động từ / tính từ / etc.)\n"
        "STRICT JSON array only. No other text."
    )

    TRANSLATE_PROMPT_TEMPLATE = (
        "Bạn là giáo viên tiếng Nhật chuyên luyện thi JLPT.\n"
        "Nhiệm vụ: Tách đoạn văn tiếng Nhật bên dưới thành từng câu trọn vẹn, "
        "dịch mỗi câu sang tiếng Việt sát nghĩa và tự nhiên.\n\n"
        "QUY TẮC:\n"
        "- Tách câu tại dấu chấm 。hoặc dấu xuống dòng ý nghĩa.\n"
        "- KHÔNG dùng <br> trong câu tiếng Nhật (giữ liền mạch).\n"
        "- Giữ nguyên <ruby><rt></rt></ruby> nếu có.\n"
        "- Với mỗi câu, trích xuất 2-4 từ vựng quan trọng (N3-N1).\n\n"
        "ĐOẠN VĂN:\n{passage_text}\n\n"
        "TRẢ VỀ JSON (KHÔNG markdown, KHÔNG trailing comma):\n"
        '{{\n'
        '  "bilingual_reading": [\n'
        '    {{\n'
        '      "japanese_sentence": "Câu JP liền mạch",\n'
        '      "vietnamese_translation": "Nghĩa tiếng Việt",\n'
        '      "vocabulary": [\n'
        '        {{"kanji": "漢字", "hiragana": "かんじ", "meaning": "chữ Hán"}}\n'
        '      ]\n'
        '    }}\n'
        '  ]\n'
        '}}'
    )

    @csrf_exempt
    def dokkai_translate_api(self, request):
        """POST: Translate passage text sentence-by-sentence."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            passage_text = d.get('passage_text', '').strip()
            if not passage_text:
                return JsonResponse({'success': False, 'error': 'No passage text'}, status=400)

            prompt = self.TRANSLATE_PROMPT_TEMPLATE.format(
                passage_text=passage_text[:3000]
            )

            from vocab.services.gemini_service import GeminiService
            raw = GeminiService.generate_text(prompt, model_name='gemini-2.0-flash')
            result = _clean_json(raw)
            bilingual = result.get('bilingual_reading', [])

            return JsonResponse({'success': True, 'bilingual_reading': bilingual})
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'JSON parse error: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def dokkai_ocr_api(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No image provided'}, status=400)
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime = image_file.content_type or 'image/png'

            from vocab.services.gemini_service import GeminiService
            text = GeminiService.generate_with_image(self.OCR_PROMPT, image_bytes, mime, model_name='gemini-2.0-flash')
            return JsonResponse({'success': True, 'text': text})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def dokkai_explain_api(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            question_text = d.get('question_text', '')
            choices = d.get('choices', [])
            correct_answer = d.get('correct_answer', '')
            passage_text = d.get('passage_text', '')

            choices_text = '\n'.join(
                f"{c.get('key', c.get('number', i+1))}. {c.get('text', '')}"
                for i, c in enumerate(choices)
            )

            prompt = self.EXPLAIN_PROMPT_TEMPLATE.format(
                passage_text=passage_text[:1500] if passage_text else '(không có)',
                question_text=question_text,
                choices_text=choices_text,
                correct_answer=correct_answer,
            )

            from vocab.services.gemini_service import GeminiService
            raw = GeminiService.generate_text(prompt, model_name='gemini-2.0-flash')
            explanation_json = _clean_json(raw)
            return JsonResponse({'success': True, 'explanation_json': explanation_json})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def dokkai_vocab_api(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            passage_text = d.get('passage_text', '').strip()
            if not passage_text:
                return JsonResponse({'success': False, 'error': 'No passage text'}, status=400)

            prompt = self.VOCAB_PROMPT_TEMPLATE.format(passage_text=passage_text[:2000])

            from vocab.services.gemini_service import GeminiService
            raw = GeminiService.generate_text(prompt, model_name='gemini-2.0-flash')

            # Parse JSON array
            clean = raw.strip()
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean)
            if m:
                clean = m.group(1).strip()
            start = clean.find('[')
            end = clean.rfind(']')
            if start != -1 and end != -1:
                clean = clean[start:end+1]
            clean = re.sub(r',\s*([\]}])', r'\1', clean)
            vocabulary = json.loads(clean)

            return JsonResponse({'success': True, 'vocabulary': vocabulary})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def dokkai_save_passage_api(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            passage_id = d.get('passage_id')
            if not passage_id:
                return JsonResponse({'success': False, 'error': 'passage_id required'}, status=400)

            passage = ReadingPassage.objects.get(pk=passage_id)

            if 'text' in d:
                passage.text = d['text']

            if 'vocabulary' in d:
                data = passage.data or {}
                data['vocabulary'] = d['vocabulary']
                passage.data = data

            if 'bilingual_reading' in d:
                data = passage.data or {}
                data['bilingual_reading'] = d['bilingual_reading']
                passage.data = data

            passage.save()
            return JsonResponse({'success': True})
        except ReadingPassage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Passage not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def dokkai_save_explanation_api(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            question_id = d.get('question_id')
            explanation_json = d.get('explanation_json')
            if not question_id:
                return JsonResponse({'success': False, 'error': 'question_id required'}, status=400)

            q = ExamQuestion.objects.get(pk=question_id)
            q.explanation_json = explanation_json or {}
            q.save(update_fields=['explanation_json'])
            return JsonResponse({'success': True})
        except ExamQuestion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Question not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


    @csrf_exempt
    def dokkai_analyze_full_api(self, request):
        """POST: One-shot AI analysis of a dokkai image → passage + questions + bilingual."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        raw = ''
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No image provided'}, status=400)
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime = image_file.content_type or 'image/png'
            model_name = request.POST.get('model', 'gemini-2.5-pro')

            from vocab.services.gemini_service import GeminiService
            raw = GeminiService.generate_with_image(
                self.FULL_ANALYZE_PROMPT, image_bytes, mime, model_name=model_name
            )
            result = _clean_json(raw)
            return JsonResponse({'success': True, 'data': result})
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'JSON parse error: {str(e)}',
                'raw': raw[:400],
            }, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    @csrf_exempt
    def dokkai_save_full_api(self, request):
        """POST: Save full analysis result → update passage + create/update questions."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        try:
            d = json.loads(request.body)
            passage_id  = d.get('passage_id')
            template_id = d.get('template_id')
            analyzed    = d.get('data', {})

            if not passage_id or not template_id:
                return JsonResponse(
                    {'success': False, 'error': 'passage_id and template_id required'}, status=400
                )

            passage  = ReadingPassage.objects.get(pk=passage_id)
            template = ExamTemplate.objects.get(pk=template_id)

            # ── 1. Save passage ──────────────────────────────────────────────
            passage_in = analyzed.get('passage', {})
            if passage_in.get('text'):
                passage.text = passage_in['text']

            passage_data = passage.data or {}
            if passage_in.get('footnotes'):
                passage_data['footnotes'] = passage_in['footnotes']

            bilingual = analyzed.get('bilingual_reading', [])
            if bilingual:
                passage_data['bilingual_reading'] = bilingual
                # Flatten vocabulary from bilingual for quick lookup
                vocab, seen = [], set()
                for sent in bilingual:
                    for v in sent.get('vocabulary', []):
                        key = v.get('kanji') or v.get('hiragana', '')
                        if key and key not in seen:
                            seen.add(key)
                            vocab.append({
                                'word':       v.get('kanji', ''),
                                'reading':    v.get('hiragana', ''),
                                'han_viet':   '',
                                'meaning_vi': v.get('meaning', ''),
                                'type':       '',
                                'jlpt_level': v.get('jlpt_level', ''),
                            })
                if vocab:
                    passage_data['vocabulary'] = vocab

            passage.data = passage_data
            passage.save()

            # ── 2. Save questions ────────────────────────────────────────────
            questions_in  = analyzed.get('questions', [])
            existing_qs   = list(template.questions.order_by('order'))
            saved_q_ids   = []

            for i, q_in in enumerate(questions_in):
                if i < len(existing_qs):
                    q = existing_qs[i]
                else:
                    q = ExamQuestion(template=template, order=template.questions.count() + 1)

                q.text           = q_in.get('question_text', '')
                q.correct_answer = str(q_in.get('correct_answer', '1'))
                q.question_type  = QuestionType.MCQ
                q.passage        = passage

                q_data = q.data or {}
                q_data['choices'] = _parse_dokkai_options(q_in.get('options', []))
                q.data = q_data

                q.explanation_json = {
                    'correct_option': q.correct_answer,
                    'overall_analysis': {
                        'summary': q_in.get('explanation', ''),
                    },
                    'quote_from_passage': q_in.get('quote_from_passage', ''),
                }
                q.save()
                saved_q_ids.append(q.id)

            return JsonResponse({
                'success': True,
                'saved_questions': len(saved_q_ids),
                'question_ids': saved_q_ids,
            })
        except (ReadingPassage.DoesNotExist, ExamTemplate.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


dokkai_tool_instance = DokkaiToolAPI()


# ==============================================================================
#  5. DOKKAI WEB VIEWS (User-facing)
# ==============================================================================

def dokkai_list(request):
    from django.core.paginator import Paginator

    selected_level = request.GET.get('level', '')
    levels = ['N5', 'N4', 'N3', 'N2', 'N1']

    qs = ExamTemplate.objects.filter(
        is_active=True,
        category=ExamCategory.DOKKAI,
    ).order_by('level', 'lesson_index', 'title')

    if selected_level:
        qs = qs.filter(level=selected_level)

    paginator = Paginator(qs, 18)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'exam/dokkai/list.html', {
        'templates': page_obj,
        'page_obj': page_obj,
        'total': paginator.count,
        'levels': levels,
        'selected_level': selected_level,
    })


def dokkai_practice(request, slug):
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True, category=ExamCategory.DOKKAI)

    passages = list(template.passages.prefetch_related('images').order_by('order'))
    questions_qs = template.questions.select_related('passage').order_by('order')

    # Build question data with ruby-rendered text and choices
    questions = []
    for q in questions_qs:
        choices = q.data.get('choices', [])
        # Normalize choice key: prefer 'key', fallback to 'number'
        norm_choices = []
        for c in choices:
            key = str(c.get('key') or c.get('number') or '')
            text = c.get('text', '') or c.get('text_vi', '')
            norm_choices.append({
                'key': key,
                'text': text,
                'text_html': mark_safe(_ruby(text)),
            })
        questions.append({
            'id': q.id,
            'text': q.text,
            'text_html': mark_safe(_ruby(q.text)),
            'correct_answer': q.correct_answer,
            'choices': norm_choices,
            'passage_id': q.passage_id,
        })

    # Render passage text_html
    for p in passages:
        p.text_html = mark_safe(_ruby(p.text)) if p.text else ''

    # Vocab from first passage
    vocab = []
    if passages:
        vocab = passages[0].data.get('vocabulary', [])

    # Load in-progress answers
    initial_answers = {}
    if request.user.is_authenticated:
        attempt = ExamAttempt.objects.filter(
            user=request.user,
            template=template,
            status=ExamAttempt.Status.IN_PROGRESS,
        ).first()
        if attempt:
            for qa in attempt.answers.all():
                initial_answers[str(qa.question_id)] = qa.raw_answer.get('selected_key', '')

    return render(request, 'exam/dokkai/practice.html', {
        'template': template,
        'passages': passages,
        'questions': questions,
        'vocab': vocab,
        'total_count': len(questions),
        'initial_answers_json': json.dumps(initial_answers),
    })


@login_required
@require_POST
def dokkai_submit(request, slug):
    template = get_object_or_404(ExamTemplate, slug=slug, is_active=True, category=ExamCategory.DOKKAI)

    try:
        body = json.loads(request.body)
        raw_answers = body.get('answers', {})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    questions = list(template.questions.order_by('order'))
    total = len(questions)
    correct_count = 0

    # Create or update ExamAttempt
    attempt, _ = ExamAttempt.objects.get_or_create(
        user=request.user,
        template=template,
        status=ExamAttempt.Status.IN_PROGRESS,
        defaults={'data': {'mode': 'dokkai'}},
    )

    answers_out = []
    for q in questions:
        selected_key = str(raw_answers.get(str(q.id), ''))
        is_correct = bool(selected_key and selected_key == str(q.correct_answer))
        if is_correct:
            correct_count += 1

        QuestionAnswer.objects.update_or_create(
            attempt=attempt,
            question=q,
            defaults={
                'raw_answer': {'selected_key': selected_key},
                'is_correct': is_correct,
            },
        )

        answers_out.append({
            'q_id': q.id,
            'is_correct': is_correct,
            'explanation_json': q.explanation_json or {},
        })

    # Mark attempt submitted
    attempt.status = ExamAttempt.Status.SUBMITTED
    attempt.total_questions = total
    attempt.correct_count = correct_count
    attempt.submitted_at = timezone.now()
    attempt.save()

    score = round(correct_count * 100 / total) if total else 0

    return JsonResponse({
        'success': True,
        'score': score,
        'correct_count': correct_count,
        'total': total,
        'answers': answers_out,
    })
