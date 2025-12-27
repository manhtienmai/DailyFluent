from django.contrib import admin

from .models import Course, Section, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)
    ordering = ("order", "title")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_active")
    list_filter = ("course", "is_active")
    search_fields = ("title", "course__title")
    ordering = ("course__order", "course__title", "order", "title")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "order", "is_active")
    list_filter = ("section", "is_active")
    search_fields = ("title", "section__title", "section__course__title")
    ordering = ("section__course__order", "section__course__title", "section__order", "section__title", "order", "title")
    prepopulated_fields = {"slug": ("title",)}
