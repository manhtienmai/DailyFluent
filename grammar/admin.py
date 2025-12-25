from django.contrib import admin

from .models import GrammarPoint


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "is_active", "updated_at")
    list_filter = ("level", "is_active", "updated_at")
    search_fields = ("title", "summary", "details", "examples")
    prepopulated_fields = {"slug": ("title",)}

