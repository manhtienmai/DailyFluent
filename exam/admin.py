from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import path, reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import json
import uuid
from pathlib import Path
from .models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamAttempt,
    QuestionAnswer,
    ListeningConversation,
    ReadingPassage,
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
    inlines = [ListeningConversationInline, ExamQuestionInline]
    change_list_template = "admin/exam/examtemplate/change_list.html"
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
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
                from .import_json import create_or_get_template_from_json
                template, auto_created = create_or_get_template_from_json(json_data)
                if auto_created:
                    messages.info(request, f"Đã tự động tạo ExamTemplate: {template.title}")
            
            # Import (format mới - schema_version 1.0)
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
    list_filter = (
        "question_type",
        "toeic_part",
        "template__level",
        "template__category",
        "template__book",
        "source",
        "mondai",
    )
    search_fields = ("text",)
    fieldsets = (
        ("Basic Information", {
            "fields": ("template", "order", "question_type", "toeic_part")
        }),
        ("Question Content", {
            "fields": ("text", "explanation_vi", "data", "correct_answer")
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
    
    def bulk_upload_images_view(self, request):
        """Custom view để hiển thị tất cả questions và upload ảnh nhanh"""
        from django.db.models import Q
        
        # Get filter parameters
        template_id = request.GET.get('template', '')
        toeic_part = request.GET.get('part', '')
        has_image = request.GET.get('has_image', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        questions = ExamQuestion.objects.select_related('template', 'passage', 'listening_conversation').order_by('template', 'order', 'id')
        
        # Apply filters
        if template_id:
            questions = questions.filter(template_id=template_id)
        
        if toeic_part:
            questions = questions.filter(toeic_part=toeic_part)
        
        # Note: has_image filter now checks passage.image, not question.image
        if has_image == 'yes':
            questions = questions.filter(passage__image__isnull=False).exclude(passage__image='')
        elif has_image == 'no':
            questions = questions.filter(
                Q(passage__isnull=True) | 
                Q(passage__image='') | 
                Q(passage__image__isnull=True)
            )
        
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
        """API endpoint để handle file upload cho passage"""
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
            # và sử dụng upload_to từ model field (ReadingPassage.image)
            passage.image = image_file
            passage.save()
            
            # Get full URL
            image_url = passage.image.url if passage.image else None
            
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
