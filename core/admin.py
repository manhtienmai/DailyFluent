from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms
from urllib.parse import urlsplit
import json

from .models import Course, Section, Lesson, DictationExercise, DictationSegment, DictationProgress


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "image_preview")
    list_filter = ("is_active",)
    search_fields = ("title",)
    ordering = ("order", "title")
    prepopulated_fields = {"slug": ("title",)}
    fields = ("title", "slug", "image", "description", "order", "is_active")
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Ảnh"


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_active")
    list_filter = ("course", "is_active")
    search_fields = ("title", "course__title")
    ordering = ("course__order", "course__title", "order", "title")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "order", "is_active", "has_content")
    list_filter = ("section", "is_active")
    search_fields = ("title", "section__title", "section__course__title")
    ordering = ("section__course__order", "section__course__title", "section__order", "section__title", "order", "title")
    prepopulated_fields = {"slug": ("title",)}
    
    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("section", "title", "slug", "order", "is_active")
        }),
        ("Nội dung bài học", {
            "fields": ("content",),
            "description": (
                "<div style='background: linear-gradient(to right, #f0f9ff, #e0f2fe); border-left: 4px solid #3b82f6; padding: 16px; margin-bottom: 16px; border-radius: 6px;'>"
                "<strong style='color: #1e293b; display: block; margin-bottom: 12px; font-size: 14px;'>📝 Rich Text Editor - Phím tắt nhanh:</strong>"
                "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; color: #475569; font-size: 12px; line-height: 1.8;'>"
                "<div><strong>Ctrl+B</strong>: In đậm</div>"
                "<div><strong>Ctrl+I</strong>: In nghiêng</div>"
                "<div><strong>Ctrl+U</strong>: Gạch chân</div>"
                "<div><strong>Ctrl+1/2/3</strong>: Tiêu đề</div>"
                "<div><strong>Ctrl+L</strong>: Danh sách</div>"
                "<div><strong>Ctrl+Q</strong>: Trích dẫn</div>"
                "<div><strong>Ctrl+K</strong>: Chèn liên kết</div>"
                "<div><strong>Ctrl+Z/Y</strong>: Hoàn tác/Làm lại</div>"
                "</div>"
                "<div style='margin-top: 12px; padding-top: 12px; border-top: 1px solid #bfdbfe; color: #64748b; font-size: 11px;'>"
                "💡 Paste sẽ tự động xóa định dạng. Sử dụng toolbar để định dạng nội dung."
                "</div>"
                "</div>"
            )
        }),
    )
    
    class Media:
        css = {
            'all': ('admin/css/lesson_editor.css',)
        }
        js = ('admin/js/lesson_editor.js',)
    
    def has_content(self, obj):
        return bool(obj.content and obj.content.strip())
    has_content.boolean = True
    has_content.short_description = "Có nội dung"


class DictationSegmentInline(admin.TabularInline):
    model = DictationSegment
    extra = 1
    fields = ("order", "start_time", "end_time", "correct_text", "hint")
    ordering = ("order",)


class DictationExerciseForm(forms.ModelForm):
    """
    Cho phép dán đường dẫn blob (hoặc URL đầy đủ) đã upload sẵn lên Azure,
    để gán thẳng vào audio_file mà không cần upload qua admin.
    """

    audio_blob = forms.CharField(
        required=False,
        label="Audio blob path/URL (đã upload)",
        help_text="Dán blob path (ví dụ: dictation/audio/20250114-foo.mp3) hoặc URL đầy đủ trên Azure. "
                  "Để trống nếu dùng upload file như bình thường.",
        widget=forms.TextInput(attrs={"style": "width: 100%;"}),
    )

    class Meta:
        model = DictationExercise
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "audio_file", None):
            self.fields["audio_blob"].initial = self.instance.audio_file.name

    def clean_audio_blob(self):
        blob = (self.cleaned_data.get("audio_blob") or "").strip()
        if not blob:
            return ""
        # Nếu là URL, trích blob path
        if "://" in blob:
            try:
                parts = urlsplit(blob)
                path = parts.path.lstrip("/")
                if path:
                    return path
            except Exception:
                pass
        return blob

    def save(self, commit=True):
        obj = super().save(commit=False)
        blob = self.cleaned_data.get("audio_blob") or ""
        if blob:
            obj.audio_file.name = blob
        if commit:
            obj.save()
            self.save_m2m()
        return obj


@admin.register(DictationExercise)
class DictationExerciseAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "difficulty", "segment_count", "is_active", "order")
    list_filter = ("lesson", "difficulty", "is_active")
    search_fields = ("title", "description", "full_transcript")
    ordering = ("order", "title")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [DictationSegmentInline]
    form = DictationExerciseForm
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "lesson", "description")
        }),
        ("Audio", {
            "fields": ("audio_file", "audio_blob", "audio_duration", "full_transcript")
        }),
        ("Settings", {
            "fields": ("difficulty", "is_active", "order")
        }),
    )
    
    def segment_count(self, obj):
        return obj.segments.count()
    segment_count.short_description = "Segments"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:core_dictationexercise_import_json', args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    change_form_template = 'admin/core/dictationexercise/change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:exercise_id>/import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='core_dictationexercise_import_json',
            ),
        ]
        return custom_urls + urls

    def import_json_view(self, request, exercise_id):
        exercise = get_object_or_404(DictationExercise, pk=exercise_id)
        
        if request.method == 'POST':
            json_file = request.FILES.get('json_file')
            json_text = request.POST.get('json_text', '').strip()
            
            if not json_file and not json_text:
                messages.error(request, "Vui lòng upload file JSON hoặc nhập JSON text.")
                return redirect(request.path)
            
            try:
                if json_file:
                    data = json.load(json_file)
                else:
                    data = json.loads(json_text)

                # Chấp nhận 2 dạng:
                # 1) Danh sách segments thuần: [ {start_time, end_time, correct_text} ]
                # 2) Danh sách các dict có "id" và "segments": [{ "id": "...", "segments": [...] }, ...]
                segments_data = None

                if isinstance(data, list):
                    # Nếu là list các object có "segments" -> gộp tất cả segments của mọi id
                    if data and isinstance(data[0], dict) and "segments" in data[0]:
                        collected = []
                        for item in data:
                            if not isinstance(item, dict) or "segments" not in item:
                                continue
                            segs = item.get("segments") or []
                            if isinstance(segs, list):
                                collected.extend(segs)
                        segments_data = collected
                    else:
                        # Dạng danh sách segments thuần
                        segments_data = data
                elif isinstance(data, dict) and "segments" in data:
                    segments_data = data.get("segments")
                else:
                    raise ValueError("JSON phải là list segments, hoặc list các object có khóa 'segments'.")

                if not isinstance(segments_data, list):
                    raise ValueError("Trường 'segments' phải là một danh sách.")

                # Xóa cũ, import mới để tránh trùng lặp
                exercise.segments.all().delete()

                created_count = 0
                for item in segments_data:
                    if not isinstance(item, dict):
                        continue

                    # Bỏ qua meta/label/instruction..., chỉ lấy type == content hoặc không có type
                    seg_type = (item.get("type") or "").lower()
                    if seg_type in {"meta", "label", "instruction"}:
                        continue
                    if seg_type and seg_type != "content":
                        continue

                    start = item.get("start_time") or item.get("start")
                    end = item.get("end_time") or item.get("end")
                    text = item.get("correct_text") or item.get("text")
                    hint = item.get("hint", "")

                    if start is None or end is None or not text:
                        continue

                    DictationSegment.objects.create(
                        exercise=exercise,
                        order=created_count + 1,
                        start_time=float(start),
                        end_time=float(end),
                        correct_text=text,
                        hint=hint,
                    )
                    created_count += 1

                messages.success(request, f"Đã import thành công {created_count} segments!")
                return redirect(reverse('admin:core_dictationexercise_change', args=[exercise.id]))

            except Exception as e:
                messages.error(request, f"Lỗi import: {str(e)}")
        
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'exercise': exercise,
            'title': f'Import Segments for {exercise.title}',
        }
        return render(request, 'admin/core/dictationexercise/import_json.html', context)


@admin.register(DictationSegment)
class DictationSegmentAdmin(admin.ModelAdmin):
    list_display = ("exercise", "order", "start_time", "end_time", "duration_display", "preview_text")
    list_filter = ("exercise",)
    search_fields = ("correct_text", "hint", "exercise__title")
    ordering = ("exercise", "order")
    
    def duration_display(self, obj):
        return f"{obj.duration:.1f}s"
    duration_display.short_description = "Duration"
    
    def preview_text(self, obj):
        text = obj.correct_text[:50]
        if len(obj.correct_text) > 50:
            text += "..."
        return text
    preview_text.short_description = "Text Preview"


@admin.register(DictationProgress)
class DictationProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "exercise", "current_segment", "total_segments", "percent_display", "updated_at")
    search_fields = ("user__username", "exercise__title")
    list_filter = ("exercise",)
    ordering = ("-updated_at",)

    def percent_display(self, obj):
        return f"{obj.percent:.1f}%"
    percent_display.short_description = "% Hoàn thành"
