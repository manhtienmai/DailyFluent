from django.contrib import admin
from .models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamAttempt,
    QuestionAnswer,
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
        "text",
        "mondai",
        "order_in_mondai",
        "source",
    )
    ordering = ("order",)


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
        "time_limit_minutes",
        "is_active",
    )
    list_filter = (
        "level",
        "category",
        "group_type",
        "book",
        "is_active",
    )
    search_fields = ("title", "subtitle", "description")
    inlines = [ExamQuestionInline]


@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "template",
        "order",
        "question_type",
        "short_text",
        "mondai",
        "order_in_mondai",
        "source",
    )
    list_filter = (
        "question_type",
        "template__level",
        "template__category",
        "template__book",
        "source",
        "mondai",
    )
    search_fields = ("text",)

    def short_text(self, obj):
        return (obj.text or "")[:60]


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


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct")
    list_filter = ("is_correct", "question__question_type")
