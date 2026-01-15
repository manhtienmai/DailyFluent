from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django import forms
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import path, reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.core.exceptions import ValidationError
import json
import uuid
import re
from pathlib import Path
from .models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamAttempt,
    QuestionAnswer,
    ListeningConversation,
    ReadingPassage,
    ReadingPassageImage,
    TOEICPart,
    ExamLevel,
    ExamComment,
)


@admin.register(ExamBook)
class ExamBookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "level", "category", "total_lessons", "is_active")
    list_filter = ("level", "category", "is_active")
    search_fields = ("title", "description")

class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 1
    fields = (
        "order",
        "question_type",
        "toeic_part",
        "text",
        "mondai",
        "order_in_mondai",
        "source",
    )
    ordering = ("order",)


class ListeningConversationInline(admin.TabularInline):
    model = ListeningConversation
    extra = 0
    fields = (
        "toeic_part",
        "order",
        "audio",
        "image",
        "transcript",
    )
    ordering = ("toeic_part", "order",)


class ReadingPassageInline(admin.StackedInline):
    model = ReadingPassage
    extra = 0
    fields = ("order", "title", "text", "image", "data")
    ordering = ("order",)
    formfield_overrides = {
        models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 6})},
    }


class ReadingPassageImageInline(admin.TabularInline):
    model = ReadingPassageImage
    extra = 0
    fields = ("order", "image", "caption")
    ordering = ("order", "id")


@admin.register(ExamTemplate)
class ExamTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "book",
        "level",
        "category",
        "group_type",
        "lesson_index",
        "main_question_type",
        "is_full_toeic",
        "listening_time_limit_minutes",
        "reading_time_limit_minutes",
        "time_limit_minutes",
        "is_active",
    )
    list_filter = (
        "level",
        "category",
        "group_type",
        "book",
        "is_full_toeic",
        "is_active",
    )
    search_fields = ("title", "subtitle", "description")
    actions = ["fix_reading_title"]
    
    def fix_reading_title(self, request, queryset):
        """Remove 'READING_' prefix from template titles that have both Listening and Reading"""
        updated = 0
        for template in queryset:
            listening = template.questions.filter(toeic_part__in=['L1', 'L2', 'L3', 'L4']).count()
            reading = template.questions.filter(toeic_part__in=['R5', 'R6', 'R7']).count()
            
            if listening > 0 and reading > 0 and template.title.startswith('READING_'):
                old_title = template.title
                new_title = template.title.replace('READING_', '', 1)
                template.title = new_title
                template.save()
                self.message_user(
                    request,
                    f"Updated '{old_title}' → '{new_title}' (has both Listening and Reading)",
                    level=messages.SUCCESS
                )
                updated += 1
            elif listening > 0 and reading > 0 and template.title.startswith('LISTENING_'):
                old_title = template.title
                new_title = template.title.replace('LISTENING_', '', 1)
                template.title = new_title
                template.save()
                self.message_user(
                    request,
                    f"Updated '{old_title}' → '{new_title}' (has both Listening and Reading)",
                    level=messages.SUCCESS
                )
                updated += 1
        
        if updated == 0:
            self.message_user(
                request,
                "No templates needed updating. Templates must have both Listening and Reading questions and start with 'READING_' or 'LISTENING_'.",
                level=messages.INFO
            )
    fix_reading_title.short_description = "Fix title: Remove READING_/LISTENING_ prefix if has both parts"
    fieldsets = (
        ("Basic Information", {
            "fields": ("book", "title", "slug", "description", "level", "category")
        }),
        ("Organization", {
            "fields": ("group_type", "lesson_index", "subtitle")
        }),
        ("Question Settings", {
            "fields": ("main_question_type", "reading_format", "dokkai_skill")
        }),
        ("TOEIC Settings", {
            "fields": (
                "is_full_toeic",
                "listening_time_limit_minutes",
                "reading_time_limit_minutes",
                "audio_file",
            ),
            "classes": ("collapse",),
        }),
        ("Time & Status", {
            "fields": ("time_limit_minutes", "is_active")
        }),
    )
    inlines = [ListeningConversationInline, ReadingPassageInline, ExamQuestionInline]
    change_list_template = "admin/exam/examtemplate/change_list.html"
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        extra_context['import_audio_url'] = reverse('admin:exam_examtemplate_import_audio', args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-toeic-json/',
                self.admin_site.admin_view(self.import_toeic_json_view),
                name='exam_examtemplate_import_toeic_json_new',
            ),
            path(
                '<int:template_id>/import-toeic-json/',
                self.admin_site.admin_view(self.import_toeic_json_view),
                name='exam_examtemplate_import_toeic_json',
            ),
            path(
                '<int:template_id>/import-audio/',
                self.admin_site.admin_view(self.import_audio_view),
                name='exam_examtemplate_import_audio',
            ),
        ]
        return custom_urls + urls
    
    def import_toeic_json_view(self, request, template_id=None):
        """
        Custom admin view để import TOEIC JSON (Reading hoặc Listening).
        
        Nếu template_id=None, sẽ tự động tạo ExamTemplate từ JSON nếu có test_id.
        """
        template = None
        auto_created = False
        
        if template_id:
            template = get_object_or_404(ExamTemplate, pk=template_id)
        
        if request.method == 'POST':
            # Get JSON file or JSON text
            json_file = request.FILES.get('json_file')
            json_text = request.POST.get('json_text', '').strip()
            
            if not json_file and not json_text:
                messages.error(request, "Vui lòng upload file JSON hoặc nhập JSON text.")
                return render(request, 'admin/exam/examtemplate/import_toeic_json.html', {
                    'template': template,
                    'opts': self.model._meta,
                    'has_view_permission': True,
                    'auto_create': template_id is None,
                })
            
            # Parse JSON
            try:
                if json_file:
                    json_data = json.load(json_file)
                else:
                    json_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                messages.error(request, f"Lỗi parse JSON: {str(e)}")
                return render(request, 'admin/exam/examtemplate/import_toeic_json.html', {
                    'template': template,
                    'opts': self.model._meta,
                    'has_view_permission': True,
                    'auto_create': template_id is None,
                })
            
            # Nếu không có template_id, tự động tạo hoặc tìm template từ JSON
            if not template:
                # Bilingual format is a list - requires template_id
                if isinstance(json_data, list):
                    messages.error(request, "Bilingual JSON format yêu cầu chọn template trước. Vui lòng vào trang ExamTemplate cụ thể và thử lại.")
                    return render(request, 'admin/exam/examtemplate/import_toeic_json.html', {
                        'template': template,
                        'opts': self.model._meta,
                        'has_view_permission': True,
                        'auto_create': template_id is None,
                    })
                from .import_json import create_or_get_template_from_json
                template, auto_created = create_or_get_template_from_json(json_data)
                if auto_created:
                    messages.info(request, f"Đã tự động tạo ExamTemplate: {template.title}")
            
            # Detect format and import accordingly
            if isinstance(json_data, list):
                # Bilingual format: list with "type" field (single/group)
                from .import_json import import_bilingual_listening_json
                result = import_bilingual_listening_json(template, json_data)
            else:
                # Standard format (schema_version 1.0 or 2.1)
                from .import_json import import_toeic_json
                result = import_toeic_json(template, json_data)
            
            if result['success']:
                messages.success(request, result['message'])
                if result.get('category_updated'):
                    messages.info(request, f"Category đã tự động cập nhật thành: {template.get_category_display()}")
                if result['errors']:
                    for error in result['errors']:
                        messages.warning(request, error)
            else:
                messages.error(request, result['message'])
                if result['errors']:
                    for error in result['errors']:
                        messages.error(request, error)
            
            # Redirect back to template change page
            return redirect(reverse('admin:exam_examtemplate_change', args=[template.id]))
        
        # GET request: show form
        return render(request, 'admin/exam/examtemplate/import_toeic_json.html', {
            'template': template,
            'opts': self.model._meta,
            'has_view_permission': True,
            'auto_create': template_id is None,
        })

    def import_audio_view(self, request, template_id):
        """Import audio files from folder to questions/conversations"""
        template = get_object_or_404(ExamTemplate, pk=template_id)
        
        if request.method == 'POST':
            # Chỉ xử lý audio cho Listening (L1-L4)
            listening_qs = template.questions.filter(toeic_part__in=["L1", "L2", "L3", "L4"])

            audio_files = request.FILES.getlist('audio_files')
            
            if not audio_files:
                messages.error(request, "Vui lòng chọn ít nhất một file audio.")
                return redirect(request.path)
            
            # Parse and map audio files
            success_count = 0
            error_messages = []
            
            # Sort files by name to ensure correct order
            audio_files = sorted(audio_files, key=lambda f: f.name)
            
            for audio_file in audio_files:
                filename = audio_file.name
                
                # Parse filename: E26-T01-01.mp3 or E26-T01-32-34.mp3
                # Pattern: any-prefix-(number) or any-prefix-(start)-(end)
                match = re.match(r'^.+-(\d+)(?:-(\d+))?\.(mp3|wav|m4a)$', filename, re.IGNORECASE)
                
                if not match:
                    error_messages.append(f"Không thể parse filename: {filename}")
                    continue
                
                first_num = int(match.group(1))
                second_num = match.group(2)
                
                if second_num:
                    # Conversation audio: E26-T01-32-34.mp3 -> questions from order 32 to 34
                    start_order = first_num
                    end_order = int(second_num)
                    
                    # Find listening questions in range
                    questions = listening_qs.filter(order__gte=start_order, order__lte=end_order).order_by('order')
                    
                    if not questions.exists():
                        error_messages.append(f"Không tìm thấy questions từ {start_order} đến {end_order} cho file: {filename}")
                        continue
                    
                    # Check if questions have listening_conversation
                    # Group by conversation
                    conversations = {}
                    questions_without_conv = []
                    
                    for q in questions:
                        if q.listening_conversation:
                            conv_id = q.listening_conversation.id
                            if conv_id not in conversations:
                                conversations[conv_id] = q.listening_conversation
                        else:
                            questions_without_conv.append(q)
                    
                    # Assign audio to conversations (if any)
                    # If questions have conversation, assign to conversation only
                    for conv in conversations.values():
                        conv.audio.save(
                            f"conv_{conv.toeic_part}_{conv.order}_{filename}",
                            ContentFile(audio_file.read()),
                            save=True
                        )
                        audio_file.seek(0)
                        success_count += 1
                    
                    # Assign audio to questions without conversation
                    for q in questions_without_conv:
                        q.audio.save(
                            f"q_{q.order}_{filename}",
                            ContentFile(audio_file.read()),
                            save=True
                        )
                        audio_file.seek(0)
                        success_count += 1
                    
                    if conversations and questions_without_conv:
                        messages.info(request, f"Đã gán audio {filename} cho {len(conversations)} conversation(s) và {len(questions_without_conv)} question(s) (từ {start_order} đến {end_order})")
                    elif conversations:
                        messages.info(request, f"Đã gán audio {filename} cho {len(conversations)} conversation(s) (từ {start_order} đến {end_order})")
                    else:
                        messages.info(request, f"Đã gán audio {filename} cho {len(questions_without_conv)} question(s) (từ {start_order} đến {end_order})")
                else:
                    # Single question audio: E26-T01-01.mp3 -> question order 1
                    order = first_num
                    
                    try:
                        question = listening_qs.get(order=order)
                        
                        # If question has listening_conversation, assign to conversation instead
                        if question.listening_conversation:
                            conv = question.listening_conversation
                            conv.audio.save(
                                f"conv_{conv.toeic_part}_{conv.order}_{filename}",
                                ContentFile(audio_file.read()),
                                save=True
                            )
                            messages.info(request, f"Đã gán audio {filename} cho conversation (question {order} có conversation)")
                        else:
                            # Assign to question
                            question.audio.save(
                                f"q_{order}_{filename}",
                                ContentFile(audio_file.read()),
                                save=True
                            )
                        
                        success_count += 1
                    except ExamQuestion.DoesNotExist:
                        error_messages.append(f"Không tìm thấy question order {order} cho file: {filename}")
                    except ExamQuestion.MultipleObjectsReturned:
                        # Multiple questions with same order (shouldn't happen, but handle it)
                        questions = listening_qs.filter(order=order)
                        for q in questions:
                            if q.listening_conversation:
                                q.listening_conversation.audio.save(
                                    f"conv_{q.listening_conversation.toeic_part}_{q.listening_conversation.order}_{filename}",
                                    ContentFile(audio_file.read()),
                                    save=True
                                )
                                audio_file.seek(0)
                            else:
                                q.audio.save(
                                    f"q_{order}_{filename}",
                                    ContentFile(audio_file.read()),
                                    save=True
                                )
                                audio_file.seek(0)
                        success_count += 1
            
            if success_count > 0:
                messages.success(request, f"Đã import thành công {success_count} audio file(s)!")
            if error_messages:
                for msg in error_messages[:10]:  # Limit to 10 errors
                    messages.warning(request, msg)
                if len(error_messages) > 10:
                    messages.warning(request, f"... và {len(error_messages) - 10} lỗi khác.")
            
            return redirect(reverse('admin:exam_examtemplate_change', args=[template.id]))
        
        # GET request: show form
        listening_qs = template.questions.filter(toeic_part__in=["L1", "L2", "L3", "L4"]).order_by("order")
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'template': template,
            'title': f'Import Audio Files for {template.title}',
            'listening_questions': listening_qs,
        }
        return render(request, 'admin/exam/examtemplate/import_audio.html', context)


@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    change_list_template = "admin/exam/examquestion/change_list.html"
    list_display = (
        "id",
        "template",
        "order",
        "question_type",
        "toeic_part",
        "short_text",
        "mondai",
        "order_in_mondai",
        "source",
    )
    # Filters moved to a custom top filter bar (template + part).
    # We intentionally disable the default left sidebar filters.
    list_filter = ()
    search_fields = ("text",)
    class ExamQuestionForm(forms.ModelForm):
        """
        Admin helper for structured answer explanation JSON.
        """

        SAMPLE_EXPLANATION_JSON = (
            '{\n'
            '  "meta": {\n'
            '    "difficulty": "medium",\n'
            '    "tags": ["grammar", "past_simple", "part_5"]\n'
            '  },\n'
            '  "correct_option": "A",\n'
            '  "content_translation": {\n'
            '    "en": "I went to the supermarket last night.",\n'
            '    "vi": "Tối qua tôi đã đi siêu thị."\n'
            '  },\n'
            '  "overall_analysis": {\n'
            '    "summary": "Câu này kiểm tra thì Quá khứ đơn (Past Simple).",\n'
            '    "detail_html": "<p>...</p>"\n'
            '  },\n'
            '  "options_breakdown": {\n'
            '    "A": {"text": "went", "status": "correct", "reason": "..."},\n'
            '    "B": {"text": "go", "status": "wrong_tense", "reason": "..."},\n'
            '    "C": {"text": "gone", "status": "wrong_form", "reason": "..."},\n'
            '    "D": {"text": "going", "status": "wrong_form", "reason": "..."}\n'
            '  },\n'
            '  "vocabulary_extraction": [\n'
            '    {"word": "supermarket", "ipa": "/.../", "meaning": "siêu thị", "type": "noun"}\n'
            '  ]\n'
            '}\n'
        )

        explanation_json = forms.CharField(
            required=False,
            widget=forms.Textarea(
                attrs={
                    "rows": 18,
                    "style": "font-family: monospace; width: 100%;",
                    "placeholder": SAMPLE_EXPLANATION_JSON,
                }
            ),
            help_text="Dán JSON giải thích chi tiết. Có thể dùng nút 'Tạo mẫu/Format' ở dưới.",
        )

        class Meta:
            model = ExamQuestion
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.is_bound:
                try:
                    raw = getattr(self.instance, "explanation_json", None)
                    if raw:
                        self.initial["explanation_json"] = json.dumps(raw, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        def clean_explanation_json(self):
            raw = self.cleaned_data.get("explanation_json")
            if raw in (None, ""):
                return {}

            # already dict/list
            if isinstance(raw, (dict, list)):
                return raw

            if not isinstance(raw, str):
                return {}

            s = raw.strip()
            if not s:
                return {}

            # Remove // comments
            s = re.sub(r"//.*", "", s)
            # Remove trailing commas: { ... , } or [ ... , ]
            s = re.sub(r",\s*([}\]])", r"\1", s)

            try:
                return json.loads(s)
            except json.JSONDecodeError as e:
                raise forms.ValidationError(
                    f"JSON không hợp lệ: {e.msg} (line {e.lineno}, col {e.colno})."
                )

    form = ExamQuestionForm

    fieldsets = (
        ("Basic Information", {
            "fields": ("template", "order", "question_type", "toeic_part")
        }),
        ("Question Content", {
            "fields": ("text", "correct_answer", "explanation_vi", "explanation_json", "data")
        }),
        ("TOEIC Specific", {
            "fields": (
                "listening_conversation",
                "image",
                "audio",
                "audio_meta",
            ),
            "classes": ("collapse",),
        }),
        ("Reading Passage", {
            "fields": ("passage",),
            "classes": ("collapse",),
        }),
        ("JLPT Metadata", {
            "fields": ("source", "mondai", "order_in_mondai"),
            "classes": ("collapse",),
        }),
    )

    def short_text(self, obj):
        return (obj.text or "")[:60]
    
    short_text.short_description = "Text Preview"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'bulk-upload-images/',
                self.admin_site.admin_view(self.bulk_upload_images_view),
                name='exam_examquestion_bulk_upload_images',
            ),
            path(
                '<int:question_id>/upload-image/',
                self.admin_site.admin_view(self.upload_image_view),
                name='exam_examquestion_upload_image',
            ),
            path(
                'upload-image-api/',
                self.admin_site.admin_view(self.upload_image_api),
                name='exam_examquestion_upload_image_api',
            ),
            path(
                'upload-passage-image-api/',
                self.admin_site.admin_view(self.upload_passage_image_api),
                name='exam_examquestion_upload_passage_image_api',
            ),
            path(
                'upload-listening-images/',
                self.admin_site.admin_view(self.upload_listening_images_view),
                name='exam_examquestion_upload_listening_images',
            ),
            path(
                'upload-listening-image-api/',
                self.admin_site.admin_view(self.upload_listening_image_api),
                name='exam_examquestion_upload_listening_image_api',
            ),
        ]
        return custom_urls + urls

    class _FilteredChangeList(ChangeList):
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            template_id = (request.GET.get("template") or "").strip()
            toeic_part = (request.GET.get("toeic_part") or request.GET.get("part") or "").strip()

            if template_id:
                try:
                    qs = qs.filter(template_id=int(template_id))
                except ValueError:
                    pass

            if toeic_part:
                qs = qs.filter(toeic_part=toeic_part)

            return qs

    def get_changelist(self, request, **kwargs):
        return self._FilteredChangeList

    def lookup_allowed(self, lookup, value):
        """
        Django admin will strip unknown querystring params and redirect to ?e=1.
        We use custom params (template, part) for our top filter bar, so allow them.
        """
        if lookup in {"template", "toeic_part", "part"}:
            return True
        return super().lookup_allowed(lookup, value)

    def get_queryset(self, request):
        """
        Safety net: ensure filtering still applies even if ChangeList customization
        is bypassed by Django admin internals.
        """
        qs = super().get_queryset(request)
        template_id = (request.GET.get("template") or "").strip()
        toeic_part = (request.GET.get("toeic_part") or request.GET.get("part") or "").strip()

        if template_id:
            try:
                qs = qs.filter(template_id=int(template_id))
            except ValueError:
                pass

        if toeic_part:
            qs = qs.filter(toeic_part=toeic_part)

        return qs

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Options for top filter bar
        extra_context["template_options"] = (
            ExamTemplate.objects.order_by("title").only("id", "title")[:500]
        )
        extra_context["part_options"] = TOEICPart.choices
        extra_context["selected_template"] = (request.GET.get("template") or "").strip()
        extra_context["selected_part"] = (request.GET.get("toeic_part") or request.GET.get("part") or "").strip()

        return super().changelist_view(request, extra_context=extra_context)
    
    def bulk_upload_images_view(self, request):
        """Custom view để hiển thị tất cả questions và upload ảnh nhanh"""
        from django.db.models import Q
        
        # Get filter parameters
        template_id = request.GET.get('template', '')
        toeic_part = request.GET.get('part', '')
        has_image = request.GET.get('has_image', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        questions = (
            ExamQuestion.objects
            .select_related('template', 'passage', 'listening_conversation')
            .prefetch_related('passage__images')
            .order_by('template', 'order', 'id')
        )
        
        # Apply filters
        if template_id:
            questions = questions.filter(template_id=template_id)
        
        if toeic_part:
            questions = questions.filter(toeic_part=toeic_part)
        
        # Note: has_image filter checks passage.image OR passage.images (multi images)
        if has_image == 'yes':
            questions = questions.filter(
                Q(passage__image__isnull=False) & ~Q(passage__image='') |
                Q(passage__images__isnull=False)
            ).distinct()
        elif has_image == 'no':
            questions = questions.filter(
                Q(passage__isnull=True) |
                (
                    (Q(passage__image='') | Q(passage__image__isnull=True))
                    & Q(passage__images__isnull=True)
                )
            ).distinct()
        
        if search_query:
            questions = questions.filter(
                Q(text__icontains=search_query) |
                Q(id__icontains=search_query)
            )
        
        # Get all templates for filter dropdown
        templates = ExamTemplate.objects.filter(level='TOEIC').order_by('title')
        
        # Get distinct parts
        from exam.models import TOEICPart
        parts = [{'value': code, 'label': label} for code, label in TOEICPart.choices]
        
        # Group questions by passage
        # Structure: {passage_id: {'passage': passage_obj, 'questions': [q1, q2, ...]}}
        # Questions without passage go to 'no_passage' group
        grouped_questions = {}
        no_passage_questions = []
        
        for q in questions:
            # Add has_meaningful_text property
            q.has_meaningful_text = bool(q.text) and not (
                q.text.strip().lower().startswith("select the best option to fill") or
                q.text.strip().lower().startswith("select the best sentence to") or
                q.text.strip().lower().startswith("select the best answer")
            )
            
            if q.passage:
                passage_id = q.passage.id
                if passage_id not in grouped_questions:
                    grouped_questions[passage_id] = {
                        'passage': q.passage,
                        'questions': []
                    }
                grouped_questions[passage_id]['questions'].append(q)
            else:
                no_passage_questions.append(q)
        
        # Convert to list for template
        question_groups = []
        for passage_id, group_data in sorted(grouped_questions.items(), key=lambda x: (x[1]['passage'].order, x[1]['passage'].id)):
            question_groups.append(group_data)
        
        # Add no_passage group at the end
        if no_passage_questions:
            question_groups.append({
                'passage': None,
                'questions': no_passage_questions
            })
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Bulk Upload Images - Questions',
            'question_groups': question_groups,
            'total_count': questions.count(),
            'templates': templates,
            'parts': parts,
            'current_template': template_id,
            'current_part': toeic_part,
            'current_has_image': has_image,
            'current_search': search_query,
            'opts': self.model._meta,
        }
        return render(request, 'admin/exam/examquestion/bulk_upload_images.html', context)
    
    def upload_image_view(self, request, question_id):
        """Custom view để upload ảnh cho question"""
        question = get_object_or_404(ExamQuestion, id=question_id)
        context = {
            **self.admin_site.each_context(request),
            'title': f'Upload Image - Question {question.id}',
            'question': question,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, question),
        }
        return render(request, 'admin/exam/examquestion/upload_image.html', context)
    
    def upload_image_api(self, request):
        """API endpoint để handle file upload"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Lấy question_id từ request
        question_id = request.POST.get('question_id')
        if not question_id:
            return JsonResponse({'error': 'question_id is required'}, status=400)
        
        question = get_object_or_404(ExamQuestion, id=question_id)
        
        # Lấy file từ request
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_ext = Path(image_file.name).suffix.lower()
        if file_ext not in allowed_extensions:
            return JsonResponse({
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Gán trực tiếp file vào field - Django sẽ tự động upload vào container "media"
        # (không phải "audio") thông qua AzureMediaStorage backend
        try:
            # Gán trực tiếp file object, Django sẽ tự động xử lý upload
            # và sử dụng upload_to="exam/toeic/images/" từ model field
            question.image = image_file
            question.save()
            
            # Get full URL
            image_url = question.image.url if question.image else None
            
            return JsonResponse({
                'success': True,
                'image_url': image_url,
                'message': 'Image uploaded successfully'
            })
        except Exception as e:
            import traceback
            error_detail = str(e)
            error_traceback = traceback.format_exc()
            
            # Log error để debug
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Question image upload error: {error_detail}\n{error_traceback}")
            
            # Kiểm tra các lỗi phổ biến và đưa ra thông báo hữu ích
            if 'AuthenticationFailed' in error_detail or 'authentication' in error_detail.lower():
                error_msg = (
                    'Azure authentication failed. '
                    'Vui lòng kiểm tra các biến môi trường sau trong file .env:\n'
                    '- AZURE_ACCOUNT_NAME\n'
                    '- AZURE_ACCOUNT_KEY\n'
                    '- AZURE_CONTAINER (mặc định: "media")\n'
                    '- AZURE_AUDIO_CONTAINER (mặc định: "audio")'
                )
            elif 'ContainerNotFound' in error_detail or 'container' in error_detail.lower():
                error_msg = (
                    'Azure container không tồn tại. '
                    'Vui lòng đảm bảo container "media" đã được tạo trong Azure Storage Account.'
                )
            elif 'account_name' in error_detail.lower() or 'account_key' in error_detail.lower():
                error_msg = (
                    'Thiếu thông tin Azure Storage. '
                    'Vui lòng kiểm tra các biến môi trường:\n'
                    '- AZURE_ACCOUNT_NAME\n'
                    '- AZURE_ACCOUNT_KEY'
                )
            else:
                error_msg = f'Upload failed: {error_detail}'
            
            return JsonResponse({
                'error': error_msg
            }, status=500)
    
    def upload_passage_image_api(self, request):
        """API endpoint để handle file upload cho passage (supports multiple images per passage)"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Lấy passage_id từ request
        passage_id = request.POST.get('passage_id')
        if not passage_id:
            return JsonResponse({'error': 'passage_id is required'}, status=400)
        
        from exam.models import ReadingPassage
        passage = get_object_or_404(ReadingPassage, id=passage_id)
        
        # Lấy file(s) từ request
        images = request.FILES.getlist('images')
        if not images and 'image' in request.FILES:
            images = [request.FILES['image']]

        if not images:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        for f in images:
            file_ext = Path(f.name).suffix.lower()
            if file_ext not in allowed_extensions:
                return JsonResponse({
                    'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                }, status=400)

        # Lưu nhiều ảnh vào DB (ReadingPassageImage)
        try:
            from django.db import transaction
            from django.db.models import Max

            with transaction.atomic():
                max_order = ReadingPassageImage.objects.filter(passage=passage).aggregate(
                    m=Max('order')
                )['m'] or 0
                next_order = max_order + 1

                created = []
                for f in images:
                    obj = ReadingPassageImage.objects.create(
                        passage=passage,
                        order=next_order,
                        image=f,
                        caption="",
                    )
                    created.append(obj)
                    next_order += 1

            return JsonResponse({
                'success': True,
                'created_count': len(created),
                'image_urls': [obj.image.url for obj in created if obj.image],
                'message': f'Uploaded {len(created)} image(s) successfully'
            })
        except Exception as e:
            import traceback
            error_detail = str(e)
            error_traceback = traceback.format_exc()
            
            # Log error để debug
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Passage image upload error: {error_detail}\n{error_traceback}")
            
            # Kiểm tra các lỗi phổ biến và đưa ra thông báo hữu ích
            if 'AuthenticationFailed' in error_detail or 'authentication' in error_detail.lower():
                error_msg = (
                    'Azure authentication failed. '
                    'Vui lòng kiểm tra các biến môi trường sau trong file .env:\n'
                    '- AZURE_ACCOUNT_NAME\n'
                    '- AZURE_ACCOUNT_KEY\n'
                    '- AZURE_CONTAINER (mặc định: "media")\n'
                    '- AZURE_AUDIO_CONTAINER (mặc định: "audio")'
                )
            elif 'ContainerNotFound' in error_detail or 'container' in error_detail.lower():
                error_msg = (
                    'Azure container không tồn tại. '
                    'Vui lòng đảm bảo container "media" đã được tạo trong Azure Storage Account.'
                )
            elif 'account_name' in error_detail.lower() or 'account_key' in error_detail.lower():
                error_msg = (
                    'Thiếu thông tin Azure Storage. '
                    'Vui lòng kiểm tra các biến môi trường:\n'
                    '- AZURE_ACCOUNT_NAME\n'
                    '- AZURE_ACCOUNT_KEY'
                )
            else:
                error_msg = f'Upload failed: {error_detail}'
            
            return JsonResponse({
                'error': error_msg
            }, status=500)
    
    def upload_listening_images_view(self, request):
        """Custom view để upload ảnh cho listening questions (Part 1-4)"""
        from django.db.models import Q
        
        # Get filter parameters
        template_id = request.GET.get('template', '')
        toeic_part = request.GET.get('part', '')
        has_image = request.GET.get('has_image', '')
        conversation_id = request.GET.get('conversation', '')
        
        # Base queryset - chỉ lấy listening questions (L1-L4)
        questions = ExamQuestion.objects.filter(
            toeic_part__in=['L1', 'L2', 'L3', 'L4']
        ).select_related('template', 'listening_conversation').order_by('template', 'toeic_part', 'order', 'id')
        
        # Apply filters
        if template_id:
            questions = questions.filter(template_id=template_id)
        
        if toeic_part:
            questions = questions.filter(toeic_part=toeic_part)
        
        if conversation_id:
            questions = questions.filter(listening_conversation_id=conversation_id)
        
        if has_image == 'yes':
            questions = questions.filter(image__isnull=False).exclude(image='')
        elif has_image == 'no':
            questions = questions.filter(Q(image__isnull=True) | Q(image=''))
        
        # Get all templates for filter dropdown
        templates = ExamTemplate.objects.filter(level='TOEIC').order_by('title')
        
        # Get distinct parts (only listening, loại bỏ L2 vì không có ảnh)
        from exam.models import TOEICPart
        listening_parts = [
            {'value': code, 'label': label} 
            for code, label in TOEICPart.choices 
            if code in ['L1', 'L3', 'L4']  # Loại bỏ L2 vì không có ảnh
        ]
        
        # Group questions by conversation (for Part 3, 4) or individual (for Part 1 only, Part 2 không có ảnh)
        grouped_questions = {}
        individual_questions = []
        
        for q in questions:
            if q.toeic_part in ['L3', 'L4'] and q.listening_conversation:
                # Group by conversation
                conv_id = q.listening_conversation.id
                conv_key = f"conv_{conv_id}"
                if conv_key not in grouped_questions:
                    grouped_questions[conv_key] = {
                        'type': 'conversation',
                        'conversation': q.listening_conversation,
                        'part': q.toeic_part,
                        'questions': []
                    }
                grouped_questions[conv_key]['questions'].append(q)
            elif q.toeic_part == 'L1':
                # Individual questions (chỉ Part 1, Part 2 không có ảnh nên không hiển thị)
                individual_questions.append(q)
        
        # Sort questions within each conversation by order
        for group_key in grouped_questions:
            grouped_questions[group_key]['questions'].sort(key=lambda q: (q.order, q.id))
        
        # Sort grouped_questions by part (L3, L4) then conversation order
        # Convert to list and sort
        grouped_questions_list = list(grouped_questions.values())
        grouped_questions_list.sort(key=lambda g: (
            g['part'],  # L3 before L4
            g['conversation'].order if g['conversation'] else 0,
            g['conversation'].id if g['conversation'] else 0
        ))
        
        # Sort individual questions by part (L1, L2) then order
        individual_questions.sort(key=lambda q: (
            q.toeic_part,  # L1 before L2
            q.order,
            q.id
        ))
        
        # Get conversations for filter dropdown
        conversations = ListeningConversation.objects.filter(
            template__level='TOEIC',
            toeic_part__in=['L3', 'L4']
        ).select_related('template').order_by('template', 'toeic_part', 'order')
        
        if template_id:
            conversations = conversations.filter(template_id=template_id)
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Upload Ảnh - Listening Questions (Part 1-4)',
            'opts': self.model._meta,
            'has_view_permission': True,
            'questions': questions,
            'grouped_questions': grouped_questions_list,
            'individual_questions': individual_questions,
            'templates': templates,
            'listening_parts': listening_parts,
            'conversations': conversations,
            'filters': {
                'template_id': template_id,
                'toeic_part': toeic_part,
                'has_image': has_image,
                'conversation_id': conversation_id,
            },
        }
        
        return render(request, 'admin/exam/examquestion/upload_listening_images.html', context)
    
    def upload_listening_image_api(self, request):
        """API endpoint để upload ảnh cho listening questions (Part 1, 2) hoặc conversations (Part 3, 4)"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Lấy question_id hoặc conversation_id từ request
        question_id = request.POST.get('question_id')
        conversation_id = request.POST.get('conversation_id')
        
        if not question_id and not conversation_id:
            return JsonResponse({'error': 'question_id or conversation_id is required'}, status=400)
        
        # Lấy file từ request
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_ext = Path(image_file.name).suffix.lower()
        if file_ext not in allowed_extensions:
            return JsonResponse({
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }, status=400)
        
        try:
            if conversation_id:
                # Upload cho conversation (Part 3, 4)
                from exam.models import ListeningConversation
                conversation = get_object_or_404(ListeningConversation, id=conversation_id)
                conversation.image = image_file
                conversation.save()
                
                image_url = conversation.image.url if conversation.image else None
                
                return JsonResponse({
                    'success': True,
                    'image_url': image_url,
                    'message': 'Conversation image uploaded successfully',
                    'type': 'conversation'
                })
            else:
                # Upload cho question (Part 1, 2)
                question = get_object_or_404(ExamQuestion, id=question_id)
                question.image = image_file
                question.save()
                
                image_url = question.image.url if question.image else None
                
                return JsonResponse({
                    'success': True,
                    'image_url': image_url,
                    'message': 'Question image uploaded successfully',
                    'type': 'question'
                })
        except Exception as e:
            import traceback
            error_detail = str(e)
            error_traceback = traceback.format_exc()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Listening image upload error: {error_detail}\n{error_traceback}")
            
            return JsonResponse({
                'error': f'Upload failed: {error_detail}'
            }, status=500)


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "template",
        "status",
        "correct_count",
        "total_questions",
        "started_at",
    )
    list_filter = ("status", "template__level", "template__category")
    search_fields = ("user__username", "template__title")


@admin.register(ListeningConversation)
class ListeningConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "template",
        "toeic_part",
        "order",
        "has_audio",
        "has_image",
        "has_transcript",
    )
    list_filter = (
        "toeic_part",
        "template__level",
        "template__category",
        "template__book",
    )
    search_fields = ("template__title", "transcript")
    fieldsets = (
        ("Basic Information", {
            "fields": ("template", "toeic_part", "order")
        }),
        ("Audio & Media", {
            "fields": ("audio", "image")
        }),
        ("Content", {
            "fields": ("transcript", "data")
        }),
    )

    def has_audio(self, obj):
        return bool(obj.audio)
    has_audio.boolean = True
    has_audio.short_description = "Audio"

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = "Image"

    def has_transcript(self, obj):
        return bool(obj.transcript)
    has_transcript.boolean = True
    has_transcript.short_description = "Transcript"


class ReadingPassageForm(forms.ModelForm):
    """
    Custom form to provide a friendly JSON editor + sample for content_json.
    """

    SAMPLE_JSON = (
        '{\n'
        '  "content_segments": [\n'
        '    {"type": "text", "text": "Acme Corp will hold a meeting on "},\n'
        '    {"type": "blank", "id": "131"},\n'
        '    {"type": "text", "text": " at the main hall. Please bring the schedule attached below."}\n'
        '  ]\n'
        '}\n'
        '// Hoặc dùng HTML trực tiếp:\n'
        '{ "html": "<p><strong>Notice</strong><br>...</p><img src=\\"https://example.com/a.png\\">" }\n'
        '// Hoặc plain text:\n'
        '{ "content": "Plain text with \\n for line breaks" }'
    )

    content_json = forms.JSONField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 12,
                "style": "font-family: monospace; width: 100%;",
                "placeholder": SAMPLE_JSON,
            }
        ),
        help_text="JSON ưu tiên render. Hỗ trợ: html | content_segments | content. Xem placeholder mẫu.",
    )

    class Meta:
        model = ReadingPassage
        fields = "__all__"

    def clean_content_json(self):
        """
        Validate JSON early to provide a clear error if admin paste is invalid.
        - Accept empty -> {}.
        - Accept dict/list directly.
        - Accept string -> json.loads.
        """
        value = self.cleaned_data.get("content_json")

        if value in [None, ""]:
            return {}

        if isinstance(value, (dict, list)):
            return value

        if isinstance(value, str):
            raw = value.strip()
            if raw == "":
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    f"JSON không hợp lệ: {exc.msg} (line {exc.lineno}, col {exc.colno}). "
                    "Loại bỏ comment // và đảm bảo đúng format JSON."
                )

        raise ValidationError("content_json phải là JSON hợp lệ (object hoặc array).")


@admin.register(ReadingPassage)
class ReadingPassageAdmin(admin.ModelAdmin):
    form = ReadingPassageForm
    list_display = ("id", "template", "order", "title", "has_image")
    list_filter = (
        "template__level",
        "template__category",
        "template__book",
    )
    search_fields = ("template__title", "title", "text")
    ordering = ("template_id", "order", "id")
    fieldsets = (
        ("Basic Information", {
            "fields": ("template", "order", "title")
        }),
        ("Content", {
            "fields": ("text", "data", "content_json")
        }),
        ("Media", {
            "fields": ("image",)
        }),
    )
    inlines = [ReadingPassageImageInline]
    formfield_overrides = {
        models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 8})},
    }

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-content-json/",
                self.admin_site.admin_view(self.import_content_json_view),
                name="exam_readingpassage_import_content_json",
            ),
        ]
        return custom_urls + urls

    def import_content_json_view(self, request):
        """
        Simple form to paste JSON content and assign to a passage.
        Find passage by (passage_id) or (template_id + order).
        """
        context = dict(
            self.admin_site.each_context(request),
            title="Import Passage Content JSON",
            errors="",
            success="",
        )

        # Filters for listing passages + prefill fields
        template_filter = request.GET.get("template_id", "").strip()
        part_filter = request.GET.get("part", "").strip()
        prefill_passage_id = request.GET.get("passage_id", "").strip()
        prefill_template_id = request.GET.get("prefill_template_id", "").strip()
        prefill_order = request.GET.get("prefill_order", "").strip()

        # If we come from a specific passage, prefer filtering by its template for faster selection
        if prefill_passage_id and not template_filter:
            try:
                p = ReadingPassage.objects.only("template_id").get(id=int(prefill_passage_id))
                template_filter = str(p.template_id)
            except Exception:
                pass

        if request.method == "POST":
            passage_id = request.POST.get("passage_id", "").strip()
            template_id = request.POST.get("template_id", "").strip()
            order = request.POST.get("order", "").strip()
            content_raw = request.POST.get("content_json", "").strip()
            title = request.POST.get("title", "").strip()

            passage = None
            try:
                if passage_id:
                    passage = ReadingPassage.objects.get(id=int(passage_id))
                elif template_id and order:
                    passage = ReadingPassage.objects.get(
                        template_id=int(template_id),
                        order=int(order),
                    )
                else:
                    context["errors"] = "Cần passage_id hoặc (template_id + order)."
            except (ReadingPassage.DoesNotExist, ValueError):
                passage = None
                context["errors"] = "Không tìm thấy passage theo thông tin cung cấp."

            if passage and content_raw:
                try:
                    data = json.loads(content_raw)
                    passage.content_json = data
                    if title:
                        passage.title = title
                    passage.save()
                    context["success"] = f"Đã import content_json cho Passage ID {passage.id}"
                except json.JSONDecodeError as exc:
                    context["errors"] = f"JSON không hợp lệ: {exc.msg} (line {exc.lineno}, col {exc.colno})"

        # Load passages for quick selection
        passages_qs = ReadingPassage.objects.select_related("template").order_by("template_id", "order")
        if template_filter:
            try:
                passages_qs = passages_qs.filter(template_id=int(template_filter))
            except ValueError:
                pass
        # Derive part from attached questions (first question's toeic_part)
        passages = []
        for p in passages_qs[:300]:  # limit to avoid huge listing
            first_q = p.questions.order_by("order").first()
            part_code = first_q.toeic_part if first_q else ""
            passages.append({
                "id": p.id,
                "template_id": p.template_id,
                "template_title": p.template.title,
                "order": p.order,
                "title": p.title,
                "part": part_code,
            })
        if part_filter:
            passages = [p for p in passages if p["part"] == part_filter]

        # Dropdown options
        template_options = ExamTemplate.objects.filter(level=ExamLevel.TOEIC).order_by("title")[:300]
        part_options = TOEICPart.choices

        context["passages"] = passages
        context["template_filter"] = template_filter
        context["part_filter"] = part_filter
        context["template_options"] = template_options
        context["part_options"] = part_options
        context["prefill_passage_id"] = prefill_passage_id
        context["prefill_template_id"] = prefill_template_id
        context["prefill_order"] = prefill_order

        return render(request, "admin/exam/readingpassage/import_content_json.html", context)

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = "Image"


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct")
    list_filter = ("is_correct", "question__question_type", "question__toeic_part")


@admin.register(ExamComment)
class ExamCommentAdmin(admin.ModelAdmin):
    list_display = ["user", "template", "content_preview", "is_active", "created_at"]
    list_filter = ["is_active", "created_at", "template"]
    search_fields = ["content", "user__username", "template__title"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    
    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("template", "user", "content", "is_active")
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def content_preview(self, obj):
        """Hiển thị preview nội dung comment (tối đa 100 ký tự)"""
        if len(obj.content) > 100:
            return obj.content[:100] + "..."
        return obj.content
    content_preview.short_description = "Nội dung"
