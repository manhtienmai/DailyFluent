from django.contrib import admin
from .models import Category, Video, TranscriptLine


class TranscriptLineInline(admin.TabularInline):
    model = TranscriptLine
    extra = 1


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "category", "created_at")
    list_filter = ("level", "category")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TranscriptLineInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
