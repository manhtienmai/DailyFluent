import json

from django.contrib import admin, messages
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.db import transaction

from .models import (
    Vocabulary,
    VocabularyExample,
    FixedPhrase,
    FixedPhraseExample,
    FsrsCardState,
    UserStudySettings,
    EnglishVocabulary,
    EnglishVocabularyExample,
    FsrsCardStateEn,
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


class EnglishVocabularyResource(resources.ModelResource):
    class Meta:
        model = EnglishVocabulary
        fields = (
            "id",
            "en_word",
            "phonetic",
            "vi_meaning",
            "en_definition",
            "course",
            "lesson",
            "course_ref",
            "lesson_ref",
            "notes",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        )


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


class EnglishVocabularyExampleInline(admin.TabularInline):
    model = EnglishVocabularyExample
    extra = 1
    fields = ("order", "en", "vi")
    ordering = ("order", "id")


@admin.register(EnglishVocabulary)
class EnglishVocabularyAdmin(ImportExportModelAdmin):
    resource_class = EnglishVocabularyResource
    inlines = (EnglishVocabularyExampleInline,)
    list_display = (
        "en_word",
        "phonetic",
        "vi_meaning",
        "course_ref",
        "lesson_ref",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = ("is_verified", "is_active", "course_ref", "lesson_ref", "created_at")
    search_fields = (
        "en_word",
        "phonetic",
        "vi_meaning",
        "en_definition",
        "example_en",
        "example_vi",
        "notes",
    )
    ordering = ("en_word", "id")

    change_list_template = "admin/vocab/englishvocabulary/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="vocab_englishvocabulary_import_json",
            ),
            path(
                "api/create-course/",
                self.admin_site.admin_view(self.create_course_api),
                name="vocab_englishvocabulary_create_course_api",
            ),
            path(
                "api/create-section/",
                self.admin_site.admin_view(self.create_section_api),
                name="vocab_englishvocabulary_create_section_api",
            ),
            path(
                "api/create-lesson/",
                self.admin_site.admin_view(self.create_lesson_api),
                name="vocab_englishvocabulary_create_lesson_api",
            ),
        ]
        return custom_urls + urls

    def create_course_api(self, request):
        """
        Create Course from admin import screen (AJAX).
        """
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        from core.models import Course
        title = (request.POST.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "Missing title"}, status=400)

        course_obj, _created = Course.objects.get_or_create(title=title)
        return JsonResponse({"id": course_obj.id, "title": course_obj.title})

    def create_section_api(self, request):
        """
        Create Section under a Course (AJAX).
        Enforce: must select a course first.
        """
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        from core.models import Course, Section
        title = (request.POST.get("title") or "").strip()
        course_id = (request.POST.get("course_id") or "").strip()

        if not title:
            return JsonResponse({"error": "Missing title"}, status=400)
        if not course_id:
            return JsonResponse({"error": "Missing course_id"}, status=400)

        try:
            course_obj = Course.objects.get(id=int(course_id))
        except Exception:
            return JsonResponse({"error": "Invalid course_id"}, status=400)

        section_obj, _created = Section.objects.get_or_create(course=course_obj, title=title)
        return JsonResponse({
            "id": section_obj.id,
            "title": section_obj.title,
            "course_id": course_obj.id,
            "course_title": course_obj.title,
        })

    def create_lesson_api(self, request):
        """
        Create Lesson under a Section (AJAX).
        Enforce: must select course + section first.
        """
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        from core.models import Course, Section, Lesson
        title = (request.POST.get("title") or "").strip()
        course_id = (request.POST.get("course_id") or "").strip()
        section_id = (request.POST.get("section_id") or "").strip()

        if not title:
            return JsonResponse({"error": "Missing title"}, status=400)
        if not course_id:
            return JsonResponse({"error": "Missing course_id"}, status=400)
        if not section_id:
            return JsonResponse({"error": "Missing section_id"}, status=400)

        try:
            course_obj = Course.objects.get(id=int(course_id))
        except Exception:
            return JsonResponse({"error": "Invalid course_id"}, status=400)

        try:
            section_obj = Section.objects.get(id=int(section_id), course=course_obj)
        except Exception:
            return JsonResponse({"error": "Invalid section_id"}, status=400)

        lesson_obj, _created = Lesson.objects.get_or_create(section=section_obj, title=title)
        return JsonResponse({
            "id": lesson_obj.id,
            "title": lesson_obj.title,
            "course_id": course_obj.id,
            "course_title": course_obj.title,
            "section_id": section_obj.id,
            "section_title": section_obj.title,
        })

    def import_json_view(self, request):
        """
        Import EnglishVocabulary từ JSON (paste hoặc upload file).

        Input JSON: object hoặc array.
        Required: en_word, vi_meaning
        Optional: phonetic, en_definition, lesson, course, notes, is_active, is_verified
        Optional examples:
          - examples: [{"en": "...", "vi": "...", "order": 0}, ...]
          - hoặc legacy: example_en/example_vi (tạo 1 example)
        """
        # Options for UI (dropdown)
        from core.models import Course, Section, Lesson
        courses_qs = Course.objects.order_by("order", "title")
        sections_qs = Section.objects.select_related("course").order_by("course__order", "course__title", "order", "title")
        lessons_qs = Lesson.objects.select_related("section", "section__course").order_by(
            "section__course__order",
            "section__course__title",
            "section__order",
            "section__title",
            "order",
            "title",
        )

        context = dict(
            self.admin_site.each_context(request),
            title=_("Import English Vocabulary from JSON"),
            opts=self.model._meta,
            app_label=self.model._meta.app_label,
            payload=request.POST.get("payload", ""),
            default_lesson=request.POST.get("default_lesson", ""),
            default_section=request.POST.get("default_section", ""),
            default_course=request.POST.get("default_course", ""),
            default_active=request.POST.get("default_active", "true"),
            courses=courses_qs,
            sections=sections_qs,
            lessons=lessons_qs,
            selected_course_id=request.POST.get("course_id", ""),
            selected_section_id=request.POST.get("section_id", ""),
            selected_lesson_id=request.POST.get("lesson_id", ""),
            new_course_title=request.POST.get("new_course_title", ""),
            new_section_title=request.POST.get("new_section_title", ""),
            new_lesson_title=request.POST.get("new_lesson_title", ""),
        )

        if request.method == "POST":
            raw = (request.POST.get("payload") or "").strip()
            upload = request.FILES.get("json_file")
            default_lesson = (request.POST.get("default_lesson") or "").strip()
            default_section = (request.POST.get("default_section") or "").strip()
            default_course = (request.POST.get("default_course") or "").strip()
            default_active = (request.POST.get("default_active", "true") or "").lower() != "false"

            # UI selections (optional)
            course_id = (request.POST.get("course_id") or "").strip()
            section_id = (request.POST.get("section_id") or "").strip()
            lesson_id = (request.POST.get("lesson_id") or "").strip()
            new_course_title = (request.POST.get("new_course_title") or "").strip()
            new_section_title = (request.POST.get("new_section_title") or "").strip()
            new_lesson_title = (request.POST.get("new_lesson_title") or "").strip()

            # Resolve/create Course/Section/Lesson defaults from UI without requiring IDs in JSON
            course_obj = None
            section_obj = None
            lesson_obj = None

            if new_course_title:
                course_obj, _created_course = Course.objects.get_or_create(title=new_course_title)
                default_course = course_obj.title
            elif course_id:
                try:
                    course_obj = Course.objects.get(id=int(course_id))
                    default_course = course_obj.title
                except Exception:
                    course_obj = None

            if new_section_title:
                if not course_obj:
                    messages.error(request, _("Please create/select a Course before creating a Section."))
                    return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)
                section_obj, _created_section = Section.objects.get_or_create(course=course_obj, title=new_section_title)
                default_section = section_obj.title
            elif section_id:
                try:
                    section_obj = Section.objects.select_related("course").get(id=int(section_id))
                    if not course_obj:
                        course_obj = section_obj.course
                        default_course = course_obj.title
                    default_section = section_obj.title
                except Exception:
                    section_obj = None
                    default_section = ""

            if new_lesson_title:
                if not section_obj:
                    messages.error(request, _("Please create/select a Section before creating a Lesson."))
                    return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)
                # create lesson under selected/new course if provided
                lesson_obj, _created_lesson = Lesson.objects.get_or_create(section=section_obj, title=new_lesson_title)
                default_lesson = lesson_obj.title
            elif lesson_id:
                try:
                    lesson_obj = Lesson.objects.select_related("section", "section__course").get(id=int(lesson_id))
                    default_lesson = lesson_obj.title
                    # if user picked a lesson but not a section/course, infer them
                    if not section_obj and lesson_obj.section_id:
                        section_obj = lesson_obj.section
                        default_section = section_obj.title
                    if not course_obj and section_obj and section_obj.course_id:
                        course_obj = section_obj.course
                        default_course = course_obj.title
                except Exception:
                    lesson_obj = None

            if upload and not raw:
                try:
                    raw = upload.read().decode("utf-8").strip()
                except Exception as exc:
                    messages.error(request, _("Could not read file: %s") % exc)
                    return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)

            if not raw:
                messages.error(request, _("Please paste JSON data or upload a JSON file."))
                return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                messages.error(request, _("Invalid JSON: %s") % exc)
                return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)

            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                messages.error(request, _("JSON must be an object or a list of objects."))
                return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)

            created = 0
            updated = 0
            skipped = 0
            errors = 0

            with transaction.atomic():
                for item in data:
                    if not isinstance(item, dict):
                        errors += 1
                        continue

                    en_word = (item.get("en_word") or item.get("word") or "").strip()
                    vi_meaning = (item.get("vi_meaning") or item.get("meaning_vi") or "").strip()
                    if not en_word or not vi_meaning:
                        skipped += 1
                        continue

                    course_title = (item.get("course") or default_course).strip()
                    section_title = (item.get("section") or item.get("part") or default_section).strip()
                    lesson_title = (item.get("lesson") or default_lesson).strip()

                    item_course_obj = course_obj
                    item_section_obj = section_obj
                    item_lesson_obj = lesson_obj
                    if course_title and (not item_course_obj or item_course_obj.title != course_title):
                        item_course_obj, _created_course_item = Course.objects.get_or_create(title=course_title)
                    if section_title and (not item_section_obj or item_section_obj.title != section_title or item_section_obj.course_id != (item_course_obj.id if item_course_obj else None)):
                        item_section_obj, _created_section_item = Section.objects.get_or_create(course=item_course_obj, title=section_title)
                    if lesson_title and (not item_lesson_obj or item_lesson_obj.title != lesson_title or item_lesson_obj.section_id != (item_section_obj.id if item_section_obj else None)):
                        item_lesson_obj, _created_lesson_item = Lesson.objects.get_or_create(section=item_section_obj, title=lesson_title)

                    vocab_kwargs = {
                        "phonetic": (item.get("phonetic") or item.get("ipa") or "").strip(),
                        "vi_meaning": vi_meaning,
                        "en_definition": (item.get("en_definition") or item.get("definition_en") or "").strip(),
                        "course": course_title,
                        "section": section_title,
                        "lesson": lesson_title,
                        "course_ref": item_course_obj,
                        "section_ref": item_section_obj,
                        "lesson_ref": item_lesson_obj,
                        "notes": (item.get("notes") or "").strip(),
                        "is_active": bool(item.get("is_active", default_active)),
                        "is_verified": bool(item.get("is_verified", False)),
                    }

                    try:
                        vocab_obj, was_created = EnglishVocabulary.objects.update_or_create(
                            en_word=en_word,
                            defaults=vocab_kwargs,
                        )
                        created += 1 if was_created else 0
                        updated += 0 if was_created else 1

                        # Examples: list preferred
                        examples = item.get("examples")
                        if isinstance(examples, list):
                            # replace existing examples for deterministic import
                            vocab_obj.examples.all().delete()
                            for idx, ex in enumerate(examples):
                                if not isinstance(ex, dict):
                                    continue
                                ex_en = (ex.get("en") or "").strip()
                                ex_vi = (ex.get("vi") or "").strip()
                                if not ex_en and not ex_vi:
                                    continue
                                order = ex.get("order")
                                try:
                                    order = int(order)
                                except Exception:
                                    order = idx
                                EnglishVocabularyExample.objects.create(
                                    vocab=vocab_obj,
                                    order=order,
                                    en=ex_en or "",
                                    vi=ex_vi or "",
                                )
                        else:
                            # Legacy: example_en/example_vi -> create one example if present
                            legacy_en = (item.get("example_en") or "").strip()
                            legacy_vi = (item.get("example_vi") or "").strip()
                            if legacy_en or legacy_vi:
                                # don't duplicate if already exists from a previous import
                                if not vocab_obj.examples.exists():
                                    EnglishVocabularyExample.objects.create(
                                        vocab=vocab_obj,
                                        order=0,
                                        en=legacy_en or "",
                                        vi=legacy_vi or "",
                                    )
                    except Exception as exc:  # pragma: no cover - admin-only path
                        errors += 1
                        messages.warning(
                            request,
                            _("Could not import %(word)s: %(err)s")
                            % {"word": en_word or vi_meaning, "err": exc},
                        )

            if created:
                messages.success(request, _("%d items created.") % created)
            if updated:
                messages.success(request, _("%d items updated.") % updated)
            if skipped:
                messages.info(request, _("%d items skipped (missing en_word or vi_meaning).") % skipped)
            if errors and not (created or updated):
                messages.error(request, _("%d items failed to import.") % errors)

        return TemplateResponse(request, "admin/vocab/englishvocabulary/import_json.html", context)


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


@admin.register(FsrsCardStateEn)
class FsrsCardStateEnAdmin(admin.ModelAdmin):
    list_display = ("user", "vocab", "due", "last_reviewed", "total_reviews", "last_rating")
    list_filter = ("user", "due", "last_rating")
    search_fields = ("user__email", "vocab__en_word", "vocab__vi_meaning")
    readonly_fields = ("card_json",)


@admin.register(UserStudySettings)
class UserStudySettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "new_cards_per_day", "reviews_per_day", "new_cards_today", "reviews_today", "last_study_date")
    list_filter = ("last_study_date",)
    search_fields = ("user__email",)
