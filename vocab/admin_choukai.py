import json
import os
import uuid

from django.http import JsonResponse
from django.shortcuts import render


# Mondai types for JLPT Choukai
CHOUKAI_MONDAI_TYPES = [
    ('1', 'もんだい1 課題理解'),
    ('2', 'もんだい2 ポイント理解'),
    ('3', 'もんだい3 概要理解'),
    ('4', 'もんだい4 発話表現'),
    ('5', 'もんだい5 即時応答'),
]


class ChoukaiToolMixin:
    """Mixin providing all Choukai Data Preparation Tool views and APIs."""

    CHOUKAI_MONDAI_TYPES = CHOUKAI_MONDAI_TYPES

    def _get_or_create_choukai_template(self, book):
        """Get or create the single hidden template for a choukai book."""
        from exam.models import ExamTemplate, ExamCategory
        template, _ = ExamTemplate.objects.get_or_create(
            book=book,
            category=ExamCategory.CHOUKAI,
            defaults={
                'title': f'Choukai - {book.title}',
                'level': book.level,
            },
        )
        return template

    def choukai_tool_view(self, request):
        from exam.models import ExamBook, ExamCategory
        books = ExamBook.objects.filter(
            category=ExamCategory.CHOUKAI
        ).order_by('title')
        context = dict(
            self.admin_site.each_context(request),
            title="Choukai Data Preparation Tool",
            books=books,
            mondai_types=self.CHOUKAI_MONDAI_TYPES,
        )
        return render(request, "admin/vocab/vocabulary/choukai_tool.html", context)

    def choukai_load_questions_api(self, request):
        """GET: return questions for a book, optionally filtered by mondai tag."""
        from exam.models import ExamQuestion
        book_id = request.GET.get('book_id')
        mondai = request.GET.get('mondai', '')
        if not book_id:
            return JsonResponse({'questions': []})
        qs = ExamQuestion.objects.filter(
            template__book_id=int(book_id),
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
                'audio_transcript': q.audio_transcript,
                'audio_transcript_vi': q.audio_transcript_vi,
                'data': q.data,
                'correct_answer': q.correct_answer,
            }
            for q in qs
        ]})

    def choukai_ghibli_api(self, request):
        """POST: Ghibli generate via Gemini. Image is optional; use 'prompt' field if no image."""
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
            custom_prompt = request.POST.get('prompt', '').strip()

            if not custom_prompt and not image_bytes:
                return JsonResponse({'success': False, 'error': 'Need image or prompt'}, status=400)

            from .services.gemini_service import GeminiService
            prompt = custom_prompt or (
                "Redraw this image in Studio Ghibli anime style. Keep the same composition "
                "and scene but transform it into warm, hand-painted Ghibli aesthetic with "
                "soft colors and detailed backgrounds."
            )
            result_bytes, result_mime = GeminiService.generate_image(
                prompt, ref_image_bytes=image_bytes, mime_type=mime_type,
                model_name=model_name,
            )
            if result_bytes is None:
                return JsonResponse({'success': False, 'error': result_mime})
            import base64
            b64 = base64.b64encode(result_bytes).decode()
            return JsonResponse({'success': True, 'image_b64': b64, 'mime_type': result_mime})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
        "2. **RUBY/FURIGANA:** For all Japanese text extraction, you MUST preserve the reading using this format: "
        "`{Kanji}(Furigana)`. Example: `{学生}(がくせい)`.\n"
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
        "      { \"label\": \"1\", \"content\": \"{日本}(にほん)\" }\n"
        "    ]\n"
        "    // Return empty array [] if type is SCENE_ONLY\n"
        "  }\n"
        "}\n\n"
        "Return ONLY the JSON object, no markdown fences."
    )

    def choukai_analyze_api(self, request):
        """POST: Classify image via Gemini 2.5 Flash. Returns type, ghibli_prompt, options."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            if 'image' not in request.FILES:
                return JsonResponse({'success': True, 'type': None, 'ghibli_prompt': None, 'data': {'options': []}})

            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime_type = image_file.content_type or 'image/png'

            from .services.gemini_service import GeminiService
            import re

            raw = GeminiService.generate_with_image(
                self.ANALYZE_SYSTEM_PROMPT, image_bytes, mime_type, model_name='gemini-2.5-flash'
            )
            # Strip code fences if model wraps output
            clean = raw.strip()
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', clean)
            if m:
                clean = m.group(1).strip()

            parsed = json.loads(clean)
            return JsonResponse({
                'success': True,
                'type': parsed.get('type'),
                'ghibli_prompt': parsed.get('ghibli_prompt'),
                'data': parsed.get('data', {'options': []}),
            })
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'JSON parse error: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_ocr_api(self, request):
        """POST: OCR extract via Gemini, return JSON text."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No image file'}, status=400)
        try:
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            mime_type = image_file.content_type or 'image/png'
            model_name = request.POST.get('model', 'gemini-2.5-flash')
            from .services.gemini_service import GeminiService
            prompt = (
                "Extract all text from this Japanese listening exam image. Return as JSON with this structure:\n"
                '{\n  "questions": [\n    {\n'
                '      "number": 1,\n'
                '      "question_text": "...",\n'
                '      "choices": ["1. ...", "2. ...", "3. ...", "4. ..."]\n'
                '    }\n  ]\n}\n'
                'If there are images/illustrations described in the question, note them in an "image_description" field.\n'
                'IMPORTANT: Preserve ALL kanji exactly as printed. Do NOT simplify or replace kanji with hiragana.'
            )
            text = GeminiService.generate_with_image(prompt, image_bytes, mime_type, model_name=model_name)
            return JsonResponse({'success': True, 'text': text})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_translate_api(self, request):
        """POST: segment + translate JP text via Gemini."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            model_name = data.get('model', 'gemini-2.5-flash')
            level = data.get('level', '').strip().upper()  # e.g. "N3"
            if not text:
                return JsonResponse({'success': False, 'error': 'No text provided'}, status=400)
            from .services.gemini_service import GeminiService

            # Build ruby filtering rule based on book level
            ruby_filter = ""
            if level in ("N3", "N2", "N1"):
                # Map levels to numeric difficulty for comparison
                # N5=5(easiest), N4=4, N3=3, N2=2, N1=1(hardest)
                level_num = int(level[1])  # e.g. N3 → 3
                skip_threshold = level_num + 2  # skip words 2+ levels below
                skip_levels = [f"N{n}" for n in range(skip_threshold, 6) if n <= 5]
                if skip_levels:
                    ruby_filter = (
                        f"\n\nIMPORTANT — Ruby/furigana filtering rule:\n"
                        f"The learner is studying at {level} level.\n"
                        f"Only add furigana 漢字(かんじ) for vocabulary that is {level} level or harder (closer to N1).\n"
                        f"Do NOT add furigana for very basic words at {', '.join(skip_levels)} level "
                        f"(e.g. common words like 人, 何, 今日, 食べる, 行く, 大きい, 時間, 学校, etc.).\n"
                        f"These easy words should appear as plain kanji without (reading) annotation.\n"
                        f"Only annotate words that a {level} student would actually need help reading.\n"
                    )
            elif level in ("N4", "N5"):
                ruby_filter = (
                    "\n\nAdd furigana 漢字(かんじ) for all kanji words since the learner is at beginner level.\n"
                )

            prompt = (
                "Segment this Japanese text and provide Vietnamese translation.\n"
                "Lines may have speaker tags like [F] (female) or [M] (male) — keep those tags in your output.\n\n"
                "For each sentence:\n"
                "1. Show the speaker tag if present (e.g. [F] or [M])\n"
                "2. Break into segments (words/phrases)\n"
                "3. Show reading (furigana) for kanji using format: 漢字(かんじ)\n"
                "4. Vietnamese meaning of each segment\n"
                "5. Full Vietnamese translation of the sentence\n\n"
                "Format as structured text. Do NOT wrap in ```json or ``` code fences.\n"
                f"{ruby_filter}\n"
                f"Text:\n{text}"
            )
            result = GeminiService.generate_text(prompt, model_name=model_name)
            return JsonResponse({'success': True, 'result': result})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_upload_audio_api(self, request):
        """POST: upload audio to Azure, return URL."""
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
            from config.storage_backends import AzureMediaStorage
            storage = AzureMediaStorage()
            saved = storage.save(unique_name, audio_file)
            url = storage.url(saved)
            return JsonResponse({'success': True, 'url': url})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_save_question_api(self, request):
        """POST: save question to book. Auto-manages hidden template."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            from exam.models import ExamBook, ExamQuestion, QuestionType
            from django.core.files.base import ContentFile
            import base64

            data = json.loads(request.body)
            question_id = data.get('question_id')
            book_id = data.get('book_id')
            if not book_id:
                return JsonResponse({'success': False, 'error': 'book_id is required'}, status=400)

            book = ExamBook.objects.get(pk=int(book_id))
            template = self._get_or_create_choukai_template(book)

            # Question fields
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
            audio_url = data.get('audio_url', '')

            # Auto-compute order = total questions in book + 1
            if question_id:
                question = ExamQuestion.objects.get(pk=int(question_id))
            else:
                max_order = template.questions.count()
                question = ExamQuestion(template=template, order=max_order + 1)

            question.mondai = mondai
            question.order_in_mondai = int(order_in_mondai) if order_in_mondai else 1
            question.text = text
            question.text_vi = text_vi
            question.correct_answer = correct_answer or '1'
            if conversation:
                q_data['conversation'] = conversation
            question.data = q_data
            question.audio_transcript = audio_transcript
            question.audio_transcript_vi = audio_transcript_vi
            question.question_type = QuestionType.MCQ

            if image_b64:
                img_bytes = base64.b64decode(image_b64)
                ext = '.png' if 'png' in image_mime else '.jpg'
                fname = f"exam/choukai/img_{uuid.uuid4().hex[:8]}{ext}"
                question.image.save(fname, ContentFile(img_bytes), save=False)

            if audio_url:
                question.audio = audio_url

            question.save()
            return JsonResponse({
                'success': True,
                'question_id': question.id,
                'message': f'Saved Q{question.order} mondai={mondai} (id={question.id})',
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def choukai_create_book_api(self, request):
        """POST: create a new ExamBook for Choukai category."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        try:
            from exam.models import ExamBook, ExamCategory, ExamLevel
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            level = data.get('level', 'N2')
            if not title:
                return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)
            if level not in ExamLevel.values:
                return JsonResponse({'success': False, 'error': f'Invalid level: {level}'}, status=400)
            book = ExamBook.objects.create(
                title=title, level=level,
                category=ExamCategory.CHOUKAI, is_active=True,
            )
            return JsonResponse({'success': True, 'id': book.id, 'title': book.title, 'level': book.level})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
