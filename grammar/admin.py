from django.contrib import admin

from .models import GrammarPoint


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "course", "section", "lesson", "is_active", "updated_at")
    list_filter = ("level", "course", "section", "lesson", "is_active", "updated_at")
    search_fields = ("title", "summary", "details", "examples", "course__title", "section__title", "lesson__title")
    prepopulated_fields = {"slug": ("title",)}

