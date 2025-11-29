from django.contrib import admin
from .models import Kanji


@admin.register(Kanji)
class KanjiAdmin(admin.ModelAdmin):
    list_display = ("char", "keyword", "sino_vi", "level", "jlpt_level", "strokes")
    list_filter = ("level", "jlpt_level")
    search_fields = ("char", "keyword", "sino_vi", "onyomi", "kunyomi")
