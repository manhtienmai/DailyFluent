from django.contrib import admin
from django import forms
from django.db import models

from .models import GrammarPoint


class GrammarPointAdminForm(forms.ModelForm):
    """Form với Textarea lớn hơn cho details và examples"""
    class Meta:
        model = GrammarPoint
        fields = '__all__'
        widgets = {
            'summary': forms.Textarea(attrs={
                'rows': 3,
                'class': 'vLargeTextField',
                'placeholder': 'Mô tả ngắn / ý chính của điểm ngữ pháp này...'
            }),
            'details': forms.Textarea(attrs={
                'rows': 12,
                'class': 'vLargeTextField',
                'placeholder': 'Giải thích chi tiết. Hỗ trợ:\n- Xuống dòng: Enter\n- In đậm: **text** hoặc <strong>text</strong>\n- In nghiêng: *text* hoặc <em>text</em>\n- Viết hoa: tự viết hoa\n- Danh sách: - item hoặc 1. item'
            }),
            'examples': forms.Textarea(attrs={
                'rows': 10,
                'class': 'vLargeTextField',
                'placeholder': 'Mỗi dòng một ví dụ. Ví dụ:\nI am a student.\nShe is a teacher.\nWe are friends.'
            }),
        }


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    form = GrammarPointAdminForm
    list_display = ("title", "level", "course", "section", "lesson", "is_active", "updated_at")
    list_filter = ("level", "course", "section", "lesson", "is_active", "updated_at")
    search_fields = ("title", "summary", "details", "examples", "course__title", "section__title", "lesson__title")
    prepopulated_fields = {"slug": ("title",)}
    
    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("title", "slug", "level", "is_active")
        }),
        ("Nội dung", {
            "fields": ("summary", "details", "examples"),
            "description": (
                "<div style='background: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px; margin-bottom: 12px; border-radius: 4px;'>"
                "<strong style='color: #1e293b; display: block; margin-bottom: 8px;'>📝 Hướng dẫn định dạng:</strong>"
                "<ul style='margin: 0; padding-left: 20px; color: #475569; font-size: 13px; line-height: 1.8;'>"
                "<li><strong>Xuống dòng:</strong> Nhấn Enter để xuống dòng mới</li>"
                "<li><strong>In đậm:</strong> Dùng <code>**text**</code> hoặc <code>&lt;strong&gt;text&lt;/strong&gt;</code></li>"
                "<li><strong>In nghiêng:</strong> Dùng <code>*text*</code> hoặc <code>&lt;em&gt;text&lt;/em&gt;</code></li>"
                "<li><strong>Viết hoa:</strong> Tự viết hoa chữ cái</li>"
                "<li><strong>Ví dụ:</strong> Mỗi dòng một ví dụ (trong trường Examples)</li>"
                "</ul>"
                "</div>"
            )
        }),
        ("Phân loại", {
            "fields": ("course", "section", "lesson"),
            "classes": ("collapse",)
        }),
    )
    
    class Media:
        css = {
            'all': ('admin/css/grammar_admin.css',)
        }

