from django.contrib import admin
from django import forms
from django.db import models

from .models import (
    GrammarBook,
    GrammarPoint,
    GrammarExample,
    GrammarExerciseSet,
    GrammarQuestion,
    UserGrammarProgress,
    GrammarAttempt,
    GrammarQuestionAnswer,
)


# ─── Inlines ──────────────────────────────────────────────────────────────────

class GrammarExampleInline(admin.TabularInline):
    model = GrammarExample
    extra = 2
    fields = ("order", "sentence_jp", "sentence_vi", "highlight_start", "highlight_end")


class GrammarQuestionInline(admin.StackedInline):
    model = GrammarQuestion
    extra = 1
    fields = (
        "order",
        "question_type",
        "question_text",
        "choices",
        "correct_answer",
        "sentence_prefix",
        "sentence_suffix",
        "tokens",
        "correct_order",
        "star_position",
        "explanation_jp",
        "explanation_vi",
    )
    formfield_overrides = {
        models.JSONField: {"widget": forms.Textarea(attrs={"rows": 3, "cols": 60})},
    }


class GrammarQuestionAnswerInline(admin.TabularInline):
    model = GrammarQuestionAnswer
    extra = 0
    readonly_fields = ("question", "user_answer", "is_correct")
    can_delete = False


# ─── GrammarBook ──────────────────────────────────────────────────────────────

@admin.register(GrammarBook)
class GrammarBookAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "is_active", "created_at")
    list_filter = ("level", "is_active")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


# ─── GrammarPoint ─────────────────────────────────────────────────────────────

class GrammarPointAdminForm(forms.ModelForm):
    class Meta:
        model = GrammarPoint
        fields = "__all__"
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "explanation": forms.Textarea(attrs={"rows": 8}),
            "details": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "examples": forms.Textarea(attrs={"rows": 6}),
        }


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    form = GrammarPointAdminForm
    list_display = ("title", "level", "book", "order", "is_active", "updated_at")
    list_filter = ("level", "book", "is_active")
    search_fields = ("title", "reading", "meaning_vi", "summary", "explanation")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GrammarExampleInline]

    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("title", "slug", "level", "reading", "meaning_vi", "is_active")
        }),
        ("Cấu trúc & Giải thích", {
            "fields": ("formation", "summary", "explanation", "details", "notes"),
        }),
        ("Ví dụ (cũ)", {
            "fields": ("examples",),
            "classes": ("collapse",),
        }),
        ("Phân loại", {
            "fields": ("book", "order", "course", "section", "lesson"),
            "classes": ("collapse",),
        }),
    )


# ─── GrammarExerciseSet ───────────────────────────────────────────────────────

@admin.register(GrammarExerciseSet)
class GrammarExerciseSetAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "grammar_point", "book", "question_count", "is_active")
    list_filter = ("level", "is_active")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GrammarQuestionInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_question_count()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.update_question_count()


# ─── GrammarQuestion ──────────────────────────────────────────────────────────

@admin.register(GrammarQuestion)
class GrammarQuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "exercise_set", "question_type", "order")
    list_filter = ("question_type", "exercise_set__level")
    search_fields = ("question_text",)
    formfield_overrides = {
        models.JSONField: {"widget": forms.Textarea(attrs={"rows": 3, "cols": 60})},
    }


# ─── UserGrammarProgress ──────────────────────────────────────────────────────

@admin.register(UserGrammarProgress)
class UserGrammarProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "grammar_point", "best_score", "studied_at", "last_practiced")
    list_filter = ("grammar_point__level",)
    search_fields = ("user__username", "grammar_point__title")
    readonly_fields = ("studied_at", "last_practiced")


# ─── GrammarAttempt ───────────────────────────────────────────────────────────

@admin.register(GrammarAttempt)
class GrammarAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "exercise_set", "score", "total", "completed_at")
    list_filter = ("exercise_set__level",)
    readonly_fields = ("completed_at",)
    inlines = [GrammarQuestionAnswerInline]
