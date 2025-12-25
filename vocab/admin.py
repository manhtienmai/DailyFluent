import json

from django.contrib import admin, messages
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Vocabulary,
    VocabularyExample,
    FixedPhrase,
    FixedPhraseExample,
    FsrsCardState,
    UserStudySettings,
)


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
            'en_meaning',
            'jlpt_level',
            'topic',
            'example_jp',
            'example_vi',
            'notes',
            'is_active',
            'is_verified',
            'created_at',
            'updated_at',
        )
        # hoặc dùng: exclude = ('kanji_chars',) nếu không muốn đụng tới ManyToMany


class VocabularyExampleInline(admin.TabularInline):
    model = VocabularyExample
    extra = 1
    fields = ("order", "jp", "vi")
    ordering = ("order", "id")


class FixedPhraseExampleInline(admin.TabularInline):
    model = FixedPhraseExample
    extra = 1
    fields = ("order", "jp", "vi")
    ordering = ("order", "id")


@admin.register(FixedPhrase)
class FixedPhraseAdmin(admin.ModelAdmin):
    inlines = (FixedPhraseExampleInline,)
    list_display = ("jp_text", "jp_kana", "vi_meaning", "is_verified", "is_active", "created_at")
    list_filter = ("is_verified", "is_active", "created_at")
    search_fields = ("jp_text", "jp_kana", "vi_meaning", "en_meaning", "notes")
    ordering = ("-created_at", "-id")


@admin.register(Vocabulary)
class VocabularyAdmin(ImportExportModelAdmin):
    resource_class = VocabularyResource
    inlines = (VocabularyExampleInline,)

    list_display = ("jp_kana", "jp_kanji", "vi_meaning", "jlpt_level", "is_verified", "is_active", "created_at")
    list_filter = ("jlpt_level", "is_verified", "is_active", "created_at")
    search_fields = ("jp_kana", "jp_kanji", "vi_meaning", "en_meaning", "notes", "example_jp", "example_vi")

    change_list_template = "admin/vocab/vocabulary/change_list.html"

    def get_urls(self):
        """Add a custom URL for paste JSON import."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="vocab_vocabulary_import_json",
            ),
        ]
        return custom_urls + urls

    def import_json_view(self, request):
        """Simple textarea-based JSON import."""
        context = dict(
            self.admin_site.each_context(request),
            title=_("Import Vocabulary from JSON"),
            opts=self.model._meta,
            app_label=self.model._meta.app_label,
            payload=request.POST.get("payload", ""),
            default_jlpt=request.POST.get("default_jlpt", ""),
            default_topic=request.POST.get("default_topic", ""),
            default_active=request.POST.get("default_active", "true"),
        )

        if request.method == "POST":
            raw = request.POST.get("payload", "").strip()
            default_jlpt = request.POST.get("default_jlpt", "").strip()
            default_topic = request.POST.get("default_topic", "").strip()
            default_active = request.POST.get("default_active", "true").lower() != "false"

            if not raw:
                messages.error(request, _("Please paste JSON data."))
                return TemplateResponse(request, "admin/vocab/vocabulary/import_json.html", context)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                messages.error(request, _("Invalid JSON: %s") % exc)
                return TemplateResponse(request, "admin/vocab/vocabulary/import_json.html", context)

            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                messages.error(request, _("JSON must be an object or a list of objects."))
                return TemplateResponse(request, "admin/vocab/vocabulary/import_json.html", context)

            created = 0
            skipped = 0
            errors = 0
            for item in data:
                if not isinstance(item, dict):
                    errors += 1
                    continue

                jp_kana = (item.get("jp_kana") or "").strip()
                vi_meaning = (item.get("vi_meaning") or "").strip()
                if not jp_kana or not vi_meaning:
                    skipped += 1
                    continue

                vocab_kwargs = {
                    "jp_kana": jp_kana,
                    "vi_meaning": vi_meaning,
                    "jp_kanji": (item.get("jp_kanji") or "").strip(),
                    "sino_vi": (item.get("sino_vi") or "").strip(),
                    "en_meaning": (item.get("en_meaning") or item.get("meaning_en") or "").strip(),
                    "jlpt_level": (item.get("jlpt_level") or default_jlpt).strip(),
                    "topic": (item.get("topic") or default_topic).strip(),
                    "example_jp": (item.get("example_jp") or "").strip(),
                    "example_vi": (item.get("example_vi") or "").strip(),
                    "notes": (item.get("notes") or "").strip(),
                    "is_active": bool(item.get("is_active", default_active)),
                    "is_verified": bool(item.get("is_verified", False)),
                }

                try:
                    Vocabulary.objects.create(**vocab_kwargs)
                    created += 1
                except Exception as exc:  # pragma: no cover - admin-only path
                    errors += 1
                    messages.warning(
                        request,
                        _("Could not import %(word)s: %(err)s")
                        % {"word": jp_kana or vi_meaning, "err": exc},
                    )

            if created:
                messages.success(request, _("%d items imported.") % created)
            if skipped:
                messages.info(request, _("%d items skipped (missing jp_kana or vi_meaning).") % skipped)
            if errors and not created:
                messages.error(request, _("%d items failed to import.") % errors)

            return TemplateResponse(request, "admin/vocab/vocabulary/import_json.html", context)

        return TemplateResponse(request, "admin/vocab/vocabulary/import_json.html", context)


@admin.register(FsrsCardState)
class FsrsCardStateAdmin(admin.ModelAdmin):
    list_display = ("user", "vocab", "due", "last_reviewed", "total_reviews", "last_rating")
    list_filter = ("user", "due", "last_rating")
    search_fields = ("user__email", "vocab__jp_kana", "vocab__vi_meaning")
    readonly_fields = ("card_json",)


@admin.register(UserStudySettings)
class UserStudySettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "new_cards_per_day", "reviews_per_day", "new_cards_today", "reviews_today", "last_study_date")
    list_filter = ("last_study_date",)
    search_fields = ("user__email",)
