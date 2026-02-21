import json
import os
import uuid
import base64
import re

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Import models
from exam.models import ExamBook, ExamQuestion, ExamCategory, ExamTemplate, QuestionType, ExamLevel
from config.storage_backends import AzureMediaStorage
from .services.gemini_service import GeminiService

# ==============================================================================
#  PHẦN 1: MIXIN CHO DJANGO ADMIN (Giao diện Web)
#  (Giữ lại cái này để bạn dùng trên web như bình thường)
# ==============================================================================

class ChoukaiToolMixin:
    """
    Mixin này được nhúng vào ModelAdmin để hiển thị giao diện tool trong Admin.
    """
    
    # Định nghĩa các loại Mondai
    CHOUKAI_MONDAI_TYPES = [
        ('1', 'もんだい1 課題理解'),
        ('2', 'もんだい2 ポイント理解'),
        ('3', 'もんだい3 概要理解'),
        ('4', 'もんだい4 発話表現'),
        ('5', 'もんだい5 即時応答'),
    ]

    def choukai_tool_view(self, request):
        """Render giao diện HTML trong Admin."""
        books = ExamBook.objects.filter(
            category=ExamCategory.CHOUKAI
        ).order_by('title')
        
        # Lấy context từ admin site (để có header, menu chuẩn của Django Admin)
        context = dict(
            self.admin_site.each_context(request),
            title="Choukai Data Preparation Tool",
            books=books,
            mondai_types=self.CHOUKAI_MONDAI_TYPES,
        )
        return render(request, "admin/vocab/vocabulary/choukai_tool.html", context)

# ==============================================================================
#  PHẦN 2: API VIEW CHO PYTHON SCRIPT (Backend xử lý)
#  (Dùng cho import_xlsx.py và cả AJAX trên web nếu cần)
# ==============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class ChoukaiToolAPI(View):
    """
    API View độc lập. 
    - Có CSRF Exempt để Script Python gọi được.
    - Trả về JSON chuẩn.
    """

    ANALYZE_SYSTEM_PROMPT = (
        "Role: You are an AI specialized in Japanese OCR and Art Direction.\n\n"
        "Task: Analyze the input image, classify it into one of the 3 categories below, "
        "and return a strict JSON output.\n\n"
        "---\nCLASSIFICATION LOGIC:\n\n"
        "1. **Category: \"SCENE_WITH_OPTIONS\"**\n"
        "   - Condition: Image contains an illustration AND text-based options (A, B, C, D or 1, 2, 3 with Japanese text).\n"
        "   - Action: Extract the text of the options. Generate a Ghibli-style image prompt based on the illustration.\n\n"
        "2. **Category: \"SCENE_ONLY\"**\n"
        "   - Condition: Image contains an illustration. It might have numbers/labels (1, 2, 3...) pointing to things, but NO text options listed.\n"
        "   - Action: IGNORE the labels/numbers. Focus on the visual scene. Generate a Ghibli-style image prompt. Set options to null.\n\n"
        "3. **Category: \"TEXT_OPTIONS_ONLY\"**\n"
        "   - Condition: Image contains only text options (A, B, C, D...). No illustration.\n"
        "   - Action: Extract the text of the options. Set image prompt to null.\n\n"
        "---\nINSTRUCTIONS:\n\n"
        "1. **NO QUESTION EXTRACTION:** Do not extract the main question sentence. Focus ONLY on the option answers.\n"
        "2. **EXACT TEXT EXTRACTION — DO NOT INVENT READINGS:**\n"
        "   Copy the text of each option EXACTLY as it appears printed in the image.\n"
        "   - If the image shows furigana (small kana) printed above a kanji word, capture it using: `{漢字}(ふりがな)`\n"
        "   - If the image shows NO furigana above a kanji, output the kanji as-is — do NOT add or invent any reading.\n"
        "   - Hiragana and katakana: copy as-is.\n"
        "   Example (furigana present in image):  `{電車}(でんしゃ)に乗ります`\n"
        "   Example (no furigana in image):       `電車に乗ります`\n"
        "3. **IMAGE PROMPT (Style Enforced):**\n"
        "   - Start with: \"Studio Ghibli style anime illustration, high quality, detailed background...\"\n"
        "   - Describe the scene visually (what is happening, who is there, the setting).\n"
        "   - Ignore any overlay text or numbers in the prompt description.\n\n"
        "---\nOUTPUT JSON FORMAT:\n\n"
        "{\n"
        "  \"type\": \"SCENE_WITH_OPTIONS\" | \"SCENE_ONLY\" | \"TEXT_OPTIONS_ONLY\",\n"
        "  \"ghibli_prompt\": \"String (English prompt for image gen) or null\",\n"
        "  \"data\": {\n"
        "    \"options\": [\n"
        "      { \"label\": \"1\", \"content\": \"{電車}(でんしゃ)に乗ります\" },\n"
        "      { \"label\": \"2\", \"content\": \"図書館で本を読みます\" }\n"
        "    ]\n"
        "    // Return empty array [] if type is SCENE_ONLY\n"
        "  }\n"
        "}\n\n"
        "CRITICAL: Do NOT invent or add furigana that is not printed in the image. "
        "Only use {漢字}(ふりがな) format when furigana is visibly printed above the kanji in the image. "
        "Return ONLY the JSON object, no markdown fences."
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

    # --- API METHODS ---

    def choukai_analyze_api(self, request):
        """POST: Phân tích ảnh (OCR Options + Phân loại Tranh/Chữ)."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'success': True, 'type': None, 'ghibli_prompt': None, 'data': {'options': []}})

            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime_type = image_file.content_type or 'image/png'

            raw = GeminiService.generate_with_image(
                self.ANALYZE_SYSTEM_PROMPT, image_bytes, mime_type, model_name='gemini-2.5-pro'
            )
            
            clean = raw.strip()
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean)
            if m: clean = m.group(1).strip()

            parsed = json.loads(clean)
            return JsonResponse({
                'success': True,
                'type': parsed.get('type'),
                'ghibli_prompt': parsed.get('ghibli_prompt'),
                'data': parsed.get('data', {'options': []}),
            })
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'JSON parse error: {str(e)}', 'raw': raw}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_translate_api(self, request):
        """POST: Dịch và Segment Transcript → JSON (có giải thích chi tiết theo mondai)."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        result_raw = ''
        try:
            data      = json.loads(request.body)
            text      = data.get('text', '').strip()
            model_name= data.get('model', 'gemini-2.5-pro')
            level     = data.get('level', '').strip().upper() or 'N3'
            mondai    = str(data.get('mondai', '')).strip()
            options   = data.get('options', [])       # [{key, text}, ...]
            correct   = str(data.get('correct_answer', '')).strip()

            if not text:
                return JsonResponse({'success': False, 'error': 'No text provided'}, status=400)

            # ── Quy tắc chung ──────────────────────────────────────────────
            SPEAKER_RULE = (
                "SPEAKER DETECTION — assign per conversation entry:\n"
                "• 'F:' / 'F：' OR female-role labels (母, 女, 女性, お母さん, 奥さん, 女の人, etc.) → speaker = \"F\"\n"
                "• 'M:' / 'M：' OR male-role labels (父, 息子, 男, 男性, お父さん, 男の人, etc.) → speaker = \"M\"\n"
                "• Narrator / context / question lines → speaker = \"\" (empty string)\n"
                "• Continuation lines (indented with 　 or leading spaces, no new speaker label) "
                "→ MERGE their text into the PREVIOUS entry (same speaker, same JSON object — append with a space)"
            )
            furigana_scope = "all kanji" if level in ("N5", "N4") else "only uncommon/difficult kanji"
            FURIGANA_RULE = (
                f"FURIGANA: Add furigana using {{漢字}}(かな) format. For {level}: {furigana_scope}."
            )
            options_block = (
                "\n".join(f"{o.get('key','?')}. {o.get('text','')}" for o in options)
                if options else "(không có)"
            )
            correct_note = f"Correct answer: option {correct}." if correct else ""

            # ── Prompt theo mondai ──────────────────────────────────────────
            if mondai in ('1', '2'):
                prompt = f"""\
You are a JLPT {level} choukai (listening) expert.

The input is a raw transcript of a JLPT Mondai {mondai} listening exercise.

STANDARD JLPT MONDAI {mondai} AUDIO STRUCTURE (always in this exact order):
  1. INTRO       — situation/context sentence (e.g. 「男の人と女の人が話しています。」)
  2. QUESTION    — what the examinee must identify (e.g. 「男の人はこの後何をしますか。」)
                   NOTE: INTRO and QUESTION are sometimes merged into one sentence.
  3. DIALOGUE    — the actual conversation between speakers (F / M)
  4. QUESTION REPEATED — the exact same question stated once more at the very end

You MUST reproduce ALL four parts faithfully in the "conversation" array, in that order.

CLEANING RULES — silently REMOVE the following from the output (they are NOT spoken audio):
  • Answer-option lines (e.g. 「1. …」 「２ …」 「A. …」 or any numbered/lettered list of choices)
  • Explanations, annotations, commentary (e.g. "答え：2", "解説：...", "ポイント：...", "(正解)", etc.)
  • Answer labels (e.g. "ĐÁP ÁN：", "Đáp án：", "正解：", "答え：" followed by a number/letter)
  • Publisher/editorial notes that clearly do not belong to the audio script
  • Vietnamese translations already embedded in the input (lines in Vietnamese that appear after Japanese lines)
    → IGNORE them entirely. Translate all Japanese text yourself from scratch.

OUTPUT RULES for each entry in "conversation":
  • INTRO line:            speaker=""   |  prefix text_vi with "(Bối cảnh) "
  • QUESTION line:         speaker=""   |  prefix text_vi with "(Câu hỏi) "
    (If INTRO and QUESTION are merged, output them as ONE entry and prefix text_vi with "(Bối cảnh) (Câu hỏi) ")
  • DIALOGUE lines:        speaker="F" or "M" — follow SPEAKER_RULE below
  • QUESTION REPEATED:     speaker=""   |  prefix text_vi with "(Câu hỏi) " — use the same text as QUESTION

TASKS:
1. Parse and output all four structural parts in the correct order as described above.
2. {SPEAKER_RULE}
3. {FURIGANA_RULE}
4. Translate every line to Vietnamese (text_vi).
5. Write a DETAILED Vietnamese explanation ("explanation") of why the correct answer is
   option {correct or '?'}. Reference specific lines from the dialogue. Be concrete and precise.

INPUT TRANSCRIPT:
{text}

{correct_note}
OPTIONS:
{options_block}

OUTPUT — strict JSON, no markdown:
{{
  "conversation": [
    {{"speaker": "", "text": "（intro JP）", "text_vi": "(Bối cảnh) Vietnamese..."}},
    {{"speaker": "", "text": "（question JP）", "text_vi": "(Câu hỏi) Vietnamese..."}},
    {{"speaker": "F", "text": "...", "text_vi": "..."}},
    {{"speaker": "M", "text": "...", "text_vi": "..."}},
    {{"speaker": "", "text": "（question JP repeated）", "text_vi": "(Câu hỏi) Vietnamese..."}}
  ],
  "explanation": "Giải thích chi tiết bằng tiếng Việt tại sao đáp án {correct or '?'} là đúng..."
}}"""

            elif mondai == '3':
                prompt = f"""\
You are a JLPT {level} choukai (listening) expert.

The input is a raw transcript of a JLPT Mondai 3 (概要理解) exercise.

STANDARD JLPT MONDAI 3 AUDIO STRUCTURE (always in this exact order):
  1. CONVERSATION / MONOLOGUE — the spoken content (may have a brief context sentence first)
  2. QUESTION — asked once at the very end, about the overall meaning/gist

CLEANING RULES — silently REMOVE from the output:
  • Answer-option lines (e.g. 「1. …」 「２ …」 「A. …」 or any numbered/lettered list of choices)
  • Explanations, annotations, or commentary ("答え：", "解説：", "ポイント：", etc.)
  • Answer labels ("ĐÁP ÁN：", "Đáp án：", "正解：" followed by a number/letter)
  • Any editorial/publisher notes not part of the actual audio
  • Vietnamese translations already embedded in the input — IGNORE them, translate Japanese yourself from scratch.

TASKS:
1. {SPEAKER_RULE}
2. {FURIGANA_RULE}
3. Faithfully reproduce the conversation/monologue in the "conversation" array (one entry per line/turn).
4. Identify and extract the QUESTION sentence (usually the final sentence ending with か).
   Put it in "question_jp" and translate to "question_vi".
   Do NOT include the question sentence inside the "conversation" array.
5. Translate every conversation line to Vietnamese (text_vi).
6. Write a DETAILED Vietnamese explanation ("explanation") of why option {correct or '?'} is
   the correct answer. Summarise key points from the conversation that support this choice
   and explain why the other options are wrong.

INPUT TRANSCRIPT:
{text}

{correct_note}
OPTIONS:
{options_block}

OUTPUT — strict JSON, no markdown:
{{
  "conversation": [
    {{"speaker": "", "text": "...", "text_vi": "..."}},
    ...
  ],
  "question_jp": "質問文...",
  "question_vi": "Câu hỏi: ...",
  "explanation": "Giải thích chi tiết bằng tiếng Việt..."
}}"""

            elif mondai in ('4', '5'):
                mondai_name = "発話表現" if mondai == '4' else "即時応答"
                prompt = f"""\
You are a JLPT {level} choukai expert.

The input is a short transcript of a JLPT Mondai {mondai} ({mondai_name}) exercise.

STANDARD STRUCTURE:
  • Mondai 4 (発話表現): a situation is described by a narrator, then the examinee chooses the right expression.
  • Mondai 5 (即時応答): a single prompt/question is spoken; the examinee chooses the best reply.

CLEANING RULES — silently REMOVE from the output:
  • Answer-option lines (e.g. 「1. …」 「２ …」 「A. …」)
  • Explanations, annotations, or commentary ("答え：", "解説：", etc.)
  • Answer labels ("ĐÁP ÁN：", "Đáp án：", "正解：" followed by a number/letter)
  • Vietnamese translations already embedded in the input — IGNORE them, translate Japanese yourself from scratch.

TASKS:
1. {SPEAKER_RULE}
2. {FURIGANA_RULE}
3. Faithfully reproduce every line of the audio in the "conversation" array with translation.
   Narrator / situation-description lines: speaker=""
4. Write a DETAILED Vietnamese explanation ("explanation") of why option {correct or '?'} is
   the correct answer. Explain the situation clearly, why this response/expression is most
   appropriate, and why the other options do not fit.

INPUT TRANSCRIPT:
{text}

{correct_note}
OPTIONS:
{options_block}

OUTPUT — strict JSON, no markdown:
{{
  "conversation": [
    {{"speaker": "", "text": "...", "text_vi": "..."}},
    ...
  ],
  "explanation": "Giải thích chi tiết bằng tiếng Việt..."
}}"""

            else:
                prompt = f"""\
You are a JLPT {level} choukai expert.

CLEANING RULES — silently REMOVE from the output:
  • Answer-option lines (e.g. 「1. …」 「２ …」 「A. …」)
  • Explanations, annotations, or commentary ("答え：", "解説：", etc.)
  • Answer labels ("ĐÁP ÁN：", "Đáp án：", "正解：" followed by a number/letter)
  • Vietnamese translations already embedded in the input — IGNORE them, translate Japanese yourself from scratch.

TASKS:
1. {SPEAKER_RULE}
2. {FURIGANA_RULE}
3. Faithfully reproduce each line of the audio in the "conversation" array with translation.
4. Write a DETAILED Vietnamese explanation ("explanation") of why the correct answer is
   option {correct or '?'}.

INPUT:
{text}

{correct_note}
OPTIONS:
{options_block}

OUTPUT — strict JSON, no markdown:
{{
  "conversation": [{{"speaker": "", "text": "...", "text_vi": "..."}}],
  "explanation": "..."
}}"""

            result_raw = GeminiService.generate_text(prompt, model_name=model_name)

            # ── Clean JSON ──────────────────────────────────────────────────
            clean = result_raw.strip()
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean)
            if m:
                clean = m.group(1).strip()
            s, e = clean.find('{'), clean.rfind('}')
            if s != -1 and e != -1:
                clean = clean[s:e+1]
            clean = re.sub(r',\s*([\]}])', r'\1', clean)

            parsed = json.loads(clean)
            return JsonResponse({
                'success':      True,
                'conversation': parsed.get('conversation', []),
                'question_jp':  parsed.get('question_jp', ''),
                'question_vi':  parsed.get('question_vi', ''),
                'explanation':  parsed.get('explanation', ''),
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Gemini returned invalid JSON',
                'raw': result_raw[:300],
            }, status=500)
        except Exception as ex:
            return JsonResponse({'success': False, 'error': str(ex)}, status=500)

    def choukai_ghibli_api(self, request):
        """POST: Vẽ lại ảnh Ghibli."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            image_bytes = None
            mime_type = 'image/png'
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                image_bytes = image_file.read()
                mime_type = image_file.content_type or 'image/png'

            model_name = request.POST.get('model', 'gemini-2.5-flash-image')
            
            prompt = (
                "Redraw this image in Studio Ghibli anime style. Keep the same composition "
                "and scene but transform it into warm, hand-painted Ghibli aesthetic with "
                "soft colors and detailed backgrounds."
            )
            
            result_bytes, result_mime = GeminiService.generate_image(
                prompt, ref_image_bytes=image_bytes, mime_type=mime_type, model_name=model_name,
            )
            
            if result_bytes is None:
                return JsonResponse({'success': False, 'error': result_mime})
            
            b64 = base64.b64encode(result_bytes).decode()
            return JsonResponse({'success': True, 'image_b64': b64, 'mime_type': result_mime})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_upload_audio_api(self, request):
        """POST: Upload Audio lên Azure."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        if 'audio' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No audio file'}, status=400)
        try:
            audio_file = request.FILES['audio']
            custom_path = request.POST.get('path', '').strip()
            ext = os.path.splitext(audio_file.name)[1].lower() or '.mp3'
            
            if custom_path:
                if not custom_path.startswith('exam/choukai/'):
                    custom_path = f"exam/choukai/{custom_path}"
                if not custom_path.endswith(ext):
                    custom_path += ext
                unique_name = custom_path
            else:
                unique_name = f"exam/choukai/{uuid.uuid4().hex}{ext}"
            
            storage = AzureMediaStorage()
            saved = storage.save(unique_name, audio_file)
            url = storage.url(saved)
            return JsonResponse({'success': True, 'url': url})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_save_question_api(self, request):
        """POST: Lưu câu hỏi vào DB."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            data = json.loads(request.body)
            question_id = data.get('question_id')
            book_id = data.get('book_id')
            
            if not book_id:
                return JsonResponse({'success': False, 'error': 'book_id is required'}, status=400)

            book = ExamBook.objects.get(pk=int(book_id))
            template = self._get_or_create_choukai_template(book)

            # --- Parse Data ---
            mondai = data.get('mondai', '')
            order_in_mondai = data.get('order_in_mondai', 1)
            text = data.get('text', '')
            text_vi = data.get('text_vi', '')
            correct_answer = data.get('correct_answer', '')
            q_data = data.get('data', {})
            audio_transcript = data.get('audio_transcript', '')
            audio_transcript_vi = data.get('audio_transcript_vi', '')
            conversation = data.get('conversation', [])
            image_b64 = data.get('image_b64', '')
            image_mime = data.get('image_mime', 'image/png')
            original_b64 = data.get('original_b64', '')
            original_mime = data.get('original_mime', 'image/png')
            image_type = data.get('image_type', '')
            audio_url = data.get('audio_url', '')

            # --- Tìm hoặc Tạo Question ---
            if question_id:
                question = ExamQuestion.objects.get(pk=int(question_id))
            else:
                max_order = template.questions.count()
                question = ExamQuestion(template=template, order=max_order + 1)

            # --- Gán dữ liệu ---
            question.mondai = mondai
            question.order_in_mondai = int(order_in_mondai) if order_in_mondai else 1
            question.text = text
            question.text_vi = text_vi
            question.correct_answer = correct_answer or '1'
            question.audio_transcript = audio_transcript
            question.audio_transcript_vi = audio_transcript_vi
            question.question_type = QuestionType.MCQ
            if audio_url:
                question.audio = audio_url

            # Merge Data JSON
            if conversation: q_data['conversation'] = conversation
            if image_type: q_data['image_type'] = image_type
            
            question.data = q_data

            # --- Xử lý Lưu Ảnh (Ghibli) ---
            if image_b64:
                img_bytes = base64.b64decode(image_b64)
                ext = '.png' if 'png' in image_mime else '.jpg'
                fname = f"exam/choukai/img_{uuid.uuid4().hex[:8]}{ext}"
                saved_name = default_storage.save(fname, ContentFile(img_bytes))
                question.image.name = saved_name

            # --- Xử lý Lưu Ảnh Gốc (Original) ---
            if original_b64:
                orig_bytes = base64.b64decode(original_b64)
                ext = '.png' if 'png' in original_mime else '.jpg'
                orig_fname = f"exam/choukai/original/img_{uuid.uuid4().hex[:8]}{ext}"
                default_storage.save(orig_fname, ContentFile(orig_bytes))
                question.data['original_image_path'] = orig_fname

            question.save()
            
            return JsonResponse({
                'success': True,
                'question_id': question.id,
                'message': f'Saved Q{question.order} mondai={mondai} (id={question.id})',
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Khởi tạo instance để dùng trong urls.py
choukai_tool_instance = ChoukaiToolAPI()