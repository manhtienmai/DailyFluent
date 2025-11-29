from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Vocabulary, FsrsCardState


# Resource định nghĩa các field sẽ import/export
class VocabularyResource(resources.ModelResource):
    class Meta:
        model = Vocabulary
        # Có thể ghi rõ các field cho chắc
        fields = (
            'id',
            'owner',
            'jp_kanji',
            'jp_kana',
            'sino_vi',
            'vi_meaning',
            'jlpt_level',
            'topic',
            'example_jp',
            'example_vi',
            'is_active',
            'created_at',
            'updated_at',
        )
        # hoặc dùng: exclude = ('kanji_chars',) nếu không muốn đụng tới ManyToMany


@admin.register(Vocabulary)
class VocabularyAdmin(ImportExportModelAdmin):
    resource_class = VocabularyResource

    list_display = ("jp_kana", "jp_kanji", "vi_meaning", "jlpt_level", "topic", "created_at")
    list_filter = ("jlpt_level", "topic", "created_at")
    search_fields = ("jp_kana", "jp_kanji", "vi_meaning", "example_jp", "example_vi")


@admin.register(FsrsCardState)
class FsrsCardStateAdmin(admin.ModelAdmin):
    list_display = ("user", "vocab", "due", "last_reviewed")
    list_filter = ("user", "due")
    search_fields = ("user__email", "vocab__jp_kana", "vocab__vi_meaning")
