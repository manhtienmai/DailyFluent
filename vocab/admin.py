import json
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.http import HttpResponseRedirect
from django import forms
from django.http import HttpResponseRedirect, JsonResponse
from .models import Vocabulary, WordEntry, WordDefinition, VocabularySet, SetItem, UserSetProgress, Course
from .utils_scraper import scrape_cambridge
import nested_admin


class WordDefinitionInline(nested_admin.NestedStackedInline):
    """Inline definitions under WordEntry"""
    model = WordDefinition
    extra = 1


class WordEntryInline(nested_admin.NestedStackedInline):
    """Inline entries under Vocabulary"""
    model = WordEntry
    extra = 1
    show_change_link = True  # Allow navigating to entry detail
    inlines = [WordDefinitionInline]


class SetItemInline(admin.TabularInline):
    model = SetItem
    extra = 1
    autocomplete_fields = ['definition']


@admin.register(Vocabulary)
class VocabularyAdmin(nested_admin.NestedModelAdmin):
    list_display = ('word', 'language', 'entry_count')
    list_filter = ('language',)
    search_fields = ('word', 'extra_data')
    inlines = [WordEntryInline]
    change_list_template = "admin/vocab/vocabulary/change_list.html"

    def entry_count(self, obj):
        return obj.entries.count()
    entry_count.short_description = "Entries"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name='vocab_vocabulary_import_json'),
            path('manual-add/', self.admin_site.admin_view(self.manual_add_view), name='vocab_vocabulary_manual_add'),
            path('scrape/', self.admin_site.admin_view(self.scrape_view), name='vocab_vocabulary_scrape'),
            path('bulk-add/', self.admin_site.admin_view(self.bulk_add_view), name='vocab_vocabulary_bulk_add'),
            path('bulk-process/', self.admin_site.admin_view(self.bulk_process_api), name='vocab_vocabulary_bulk_process'),
            path('chapter-import/', self.admin_site.admin_view(self.chapter_import_view), name='vocab_vocabulary_chapter_import'),
            path('chapter-import/create-set/', self.admin_site.admin_view(self.chapter_import_create_set), name='vocab_vocabulary_chapter_import_create_set'),
        ]
        return custom_urls + urls

    def bulk_add_view(self, request):
        """View to render the bulk add page."""
        context = dict(
           self.admin_site.each_context(request),
           title="Bulk Add Vocabulary"
        )
        return render(request, "admin/vocab/vocabulary/bulk_add.html", context)

    def bulk_process_api(self, request):
        """
        API to process a single word: Scrape -> Save -> Return Result.
        Called via AJAX from bulk_add.html.
        """
        word = request.GET.get('word', '').strip().lower()
        if not word:
            return JsonResponse({'status': 'error', 'message': 'No word provided'}, status=400)
        
        try:
            # 0. Check if word exists and has definitions
            vocab = Vocabulary.objects.filter(word=word).first()
            reuse_existing = False
            scraped_entries = []
            created_entries = 0
            
            if vocab and WordDefinition.objects.filter(entry__vocab=vocab).exists():
                reuse_existing = True
            else:
                # 1. Scrape Info
                scraped_entries = scrape_cambridge(word)
                if not scraped_entries:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f"Not found dictionary data for '{word}'",
                        'word': word
                    })
                
                # Apply limit
                try:
                    limit = int(request.GET.get('limit', 0))
                    if limit > 0:
                        scraped_entries = scraped_entries[:limit]
                except ValueError:
                    pass

            # 2. Save to DB (Transaction)
            with transaction.atomic():
                if not reuse_existing:
                    # Get/Create Vocabulary
                    vocab, _ = Vocabulary.objects.get_or_create(
                        word=word,
                        defaults={'language': Vocabulary.Language.ENGLISH}
                    )
                    
                    # Loop through scraped entries
                    for item in scraped_entries:
                        pos = item.get('type') or 'unknown'
                        
                        # Create/Update WordEntry
                        entry, _ = WordEntry.objects.get_or_create(
                            vocab=vocab,
                            part_of_speech=pos,
                            defaults={
                                'ipa': item.get('ipa', ''),
                                'audio_us': item.get('audio_us') or '',
                                'audio_uk': item.get('audio_uk') or ''
                            }
                        )
                        
                        # Create Definition if not exists
                        definition_text = item.get('definition', '')
                        if definition_text:
                            if not entry.definitions.filter(meaning=definition_text).exists():
                                WordDefinition.objects.create(
                                    entry=entry,
                                    meaning=definition_text,
                                    example_sentence=item.get('example', '')
                                )
                                created_entries += 1
            
            # Optionally add to a VocabularySet
            set_id = request.GET.get('set_id')
            if set_id:
                try:
                    vocab_set = VocabularySet.objects.get(pk=int(set_id))
                    # Get the first definition created for this word
                    first_def = WordDefinition.objects.filter(entry__vocab=vocab).first()
                    if first_def and not SetItem.objects.filter(vocabulary_set=vocab_set, definition=first_def).exists():
                        SetItem.objects.create(
                            vocabulary_set=vocab_set,
                            definition=first_def,
                            display_order=vocab_set.items.count()
                        )
                except (VocabularySet.DoesNotExist, ValueError):
                    pass
            
            return JsonResponse({
                'status': 'success',
                'message': f"Added/Updated '{word}' with {created_entries} definitions.",
                'word': word,
                'definitions': len(scraped_entries)
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'word': word
            }, status=500)

    def scrape_view(self, request):
        """API to scrape data from Cambridge Dictionary"""
        word = request.GET.get('word', '').strip()
        if not word:
            return JsonResponse({'error': 'No word provided'}, status=400)
            
        try:
            results = scrape_cambridge(word)
            return JsonResponse({'results': results})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def chapter_import_view(self, request):
        """View to render the chapter import page."""
        context = dict(
           self.admin_site.each_context(request),
           title="Import TOEIC Chapters"
        )
        return render(request, "admin/vocab/vocabulary/chapter_import.html", context)

    def chapter_import_create_set(self, request):
        """API to create a VocabularySet with chapter/milestone data."""
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
        
        try:
            data = json.loads(request.body)
            
            toeic_level = data.get('toeic_level')
            set_number = data.get('set_number')
            chapter = data.get('chapter')
            chapter_name = data.get('chapter_name', '')
            milestone = data.get('milestone', '')
            priority_range = data.get('priority_range', '')
            
            if not toeic_level or not set_number:
                return JsonResponse({'status': 'error', 'message': 'toeic_level and set_number required'}, status=400)
            
            # Check if set already exists
            existing = VocabularySet.objects.filter(toeic_level=toeic_level, set_number=set_number).first()
            if existing:
                # Update existing set
                existing.chapter = chapter
                existing.chapter_name = chapter_name
                existing.milestone = milestone
                existing.priority_range = priority_range
                existing.status = VocabularySet.Status.PUBLISHED
                existing.save()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Updated existing set {set_number}',
                    'set_id': existing.pk
                })
            
            # Create new set
            title = f"TOEIC {toeic_level} - Set {set_number}"
            if chapter_name:
                title = f"{chapter_name} ({milestone}) - Set {set_number}"
            
            vocab_set = VocabularySet.objects.create(
                title=title,
                description=f"Priority: {priority_range}",
                owner=None,  # System set
                is_public=True,
                status=VocabularySet.Status.PUBLISHED,
                toeic_level=toeic_level,
                set_number=set_number,
                chapter=chapter,
                chapter_name=chapter_name,
                milestone=milestone,
                priority_range=priority_range
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'Created set {set_number}',
                'set_id': vocab_set.pk
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def import_json_view(self, request):
        if request.method == "POST":
            json_data = request.POST.get("json_data")
            if not json_data:
                messages.error(request, "Please enter JSON data.")
                return redirect("admin:vocab_vocabulary_import_json")

            try:
                data = json.loads(json_data)
                if not isinstance(data, list):
                    messages.error(request, "JSON must be a list of objects.")
                    return redirect("admin:vocab_vocabulary_import_json")

                created_count = 0
                with transaction.atomic():
                    for item in data:
                        word = item.get("word")
                        if not word:
                            continue
                        
                        # Get or create Vocabulary (word only)
                        vocab, _ = Vocabulary.objects.get_or_create(
                            word=word,
                            defaults={
                                "language": item.get("language", Vocabulary.Language.ENGLISH),
                                "extra_data": item.get("extra_data", {})
                            }
                        )

                        # Create Entries and Definitions
                        meanings = item.get("meanings", [])
                        if isinstance(meanings, list):
                            for m in meanings:
                                pos = m.get("pos", "")
                                # Get or create WordEntry
                                entry, _ = WordEntry.objects.get_or_create(
                                    vocab=vocab,
                                    part_of_speech=pos,
                                    defaults={
                                        "ipa": m.get("ipa", item.get("ipa", "")),
                                        "audio_us": m.get("audio_us", item.get("audio_url", "")),
                                        "audio_uk": m.get("audio_uk", "")
                                    }
                                )
                                # Create Definition
                                WordDefinition.objects.create(
                                    entry=entry,
                                    meaning=m.get("meaning", ""),
                                    example_sentence=m.get("example", ""),
                                    example_trans=m.get("example_trans", ""),
                                    image_url=m.get("image", "")
                                )
                        created_count += 1
                
                messages.success(request, f"Successfully imported {created_count} vocabulary items.")
                return redirect("admin:vocab_vocabulary_changelist")

            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON format.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        context = dict(
           self.admin_site.each_context(request),
           title="Import Vocabulary from JSON"
        )
        return render(request, "admin/vocab/vocabulary/import_json.html", context)
    
    def manual_add_view(self, request):
        if request.method == "POST":
            word = request.POST.get("word")
            ipa = request.POST.get("ipa")
            audio_us = request.POST.get("audio_us", request.POST.get("audio_url", ""))
            audio_uk = request.POST.get("audio_uk", "")
            language = request.POST.get("language", Vocabulary.Language.ENGLISH)
            
            meaning = request.POST.get("meaning")
            pos = request.POST.get("pos")
            example = request.POST.get("example")
            example_trans = request.POST.get("example_trans")
            
            if not word or not meaning:
                 messages.error(request, "Word and Meaning are required.")
                 return redirect("admin:vocab_vocabulary_manual_add")

            try:
                with transaction.atomic():
                    # Create Vocab (word only)
                    vocab, _ = Vocabulary.objects.get_or_create(
                        word=word,
                        defaults={"language": language}
                    )
                    
                    # Get or create WordEntry
                    entry, _ = WordEntry.objects.get_or_create(
                        vocab=vocab,
                        part_of_speech=pos or "",
                        defaults={
                            "ipa": ipa or "",
                            "audio_us": audio_us,
                            "audio_uk": audio_uk
                        }
                    )

                    # Create Definition
                    WordDefinition.objects.create(
                        entry=entry,
                        meaning=meaning,
                        example_sentence=example or "",
                        example_trans=example_trans or ""
                    )
                
                messages.success(request, f"Successfully added '{word}'.")
                if "save_add_another" in request.POST:
                     return redirect("admin:vocab_vocabulary_manual_add")
                return redirect("admin:vocab_vocabulary_changelist")

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        context = dict(
           self.admin_site.each_context(request),
           title="Quick Add Vocabulary"
        )
        return render(request, "admin/vocab/vocabulary/manual_add.html", context)


@admin.register(WordEntry)
class WordEntryAdmin(admin.ModelAdmin):
    list_display = ('vocab', 'part_of_speech', 'ipa', 'definition_count')
    list_filter = ('part_of_speech',)
    search_fields = ('vocab__word', 'ipa')
    autocomplete_fields = ['vocab']
    inlines = [WordDefinitionInline]

    def definition_count(self, obj):
        return obj.definitions.count()
    definition_count.short_description = "Definitions"


@admin.register(WordDefinition)
class WordDefinitionAdmin(admin.ModelAdmin):
    list_display = ('get_word', 'get_pos', 'meaning')
    search_fields = ('entry__vocab__word', 'meaning')
    list_filter = ('entry__part_of_speech',)
    autocomplete_fields = ['entry']

    def get_word(self, obj):
        return obj.entry.vocab.word
    get_word.short_description = "Word"
    get_word.admin_order_field = 'entry__vocab__word'

    def get_pos(self, obj):
        return obj.entry.part_of_speech
    get_pos.short_description = "POS"


@admin.register(VocabularySet)
class VocabularySetAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_course', 'owner', 'status', 'is_public', 'toeic_level', 'set_number', 'created_at')
    list_filter = ('status', 'is_public', 'toeic_level', 'created_at')
    search_fields = ('title', 'description')
    inlines = [SetItemInline]

    def get_course(self, obj):
        if not obj.toeic_level:
            return "-"
        # Try to find the Course object matching this level
        course = Course.objects.filter(toeic_level=obj.toeic_level).first()
        return course.title if course else f"TOEIC {obj.toeic_level} (No Course)"
    get_course.short_description = "Course"
    get_course.admin_order_field = 'toeic_level'


@admin.register(SetItem)
class SetItemAdmin(admin.ModelAdmin):
    list_display = ('vocabulary_set', 'definition', 'display_order')
    list_filter = ('vocabulary_set',)
    search_fields = ('vocabulary_set__title', 'definition__entry__vocab__word')


@admin.register(UserSetProgress)
class UserSetProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'vocabulary_set', 'status', 'words_learned', 'words_total', 'quiz_best_score', 'started_at', 'completed_at')
    list_filter = ('status', 'vocabulary_set__toeic_level')
    search_fields = ('user__username', 'vocabulary_set__title')
    raw_id_fields = ('user', 'vocabulary_set')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'toeic_level', 'slug', 'is_active')
    list_filter = ('is_active', 'toeic_level')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    change_list_template = "admin/vocab/course/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('init-defaults/', self.admin_site.admin_view(self.init_defaults_view), name='vocab_course_init_defaults'),
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name='vocab_course_import_json'),
        ]
        return custom_urls + urls

    def import_json_view(self, request):
        if request.method == "POST":
            json_data = request.POST.get("json_data")
            if not json_data:
                messages.error(request, "Please enter JSON data.")
                return redirect("admin:vocab_course_import_json")

            try:
                data = json.loads(json_data)
                if not isinstance(data, list):
                    messages.error(request, "JSON must be a list of objects.")
                    return redirect("admin:vocab_course_import_json")

                created_count = 0
                updated_count = 0
                with transaction.atomic():
                    for item in data:
                        slug = item.get("slug")
                        if not slug: continue
                        
                        course, created = Course.objects.update_or_create(
                            slug=slug,
                            defaults={
                                'title': item.get('title', ''),
                                'toeic_level': item.get('level'),
                                'description': item.get('description', ''),
                                'icon': item.get('icon', ''),
                                'gradient': item.get('gradient', ''),
                                'is_active': True
                            }
                        )
                        if created: created_count += 1
                        else: updated_count += 1
                
                messages.success(request, f"Successfully imported courses: {created_count} created, {updated_count} updated.")
                return redirect("admin:vocab_course_changelist")

            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON format.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        context = dict(
           self.admin_site.each_context(request),
           title="Import Course from JSON"
        )
        return render(request, "admin/vocab/course/import_json.html", context)

    def init_defaults_view(self, request):
        """Create the 4 default TOEIC courses."""
        courses_data = [
            {'title': 'TOEIC 600 Essential', 'slug': 'toeic-600-essential', 'toeic_level': 600, 'description': 'Từ vựng cơ bản dành cho người mới bắt đầu.', 'icon': '🌱', 'gradient': 'linear-gradient(135deg, #4caf50, #2e7d32)'},
            {'title': 'TOEIC 730 Intermediate', 'slug': 'toeic-730-intermediate', 'toeic_level': 730, 'description': 'Từ vựng trung cấp dành cho môi trường công sở.', 'icon': '📘', 'gradient': 'linear-gradient(135deg, #2196f3, #1565c0)'},
            {'title': 'TOEIC 860 Advanced', 'slug': 'toeic-860-advanced', 'toeic_level': 860, 'description': 'Từ vựng nâng cao để đạt điểm xuất sắc.', 'icon': '🔮', 'gradient': 'linear-gradient(135deg, #9c27b0, #6a1b9a)'},
            {'title': 'TOEIC 990 Master', 'slug': 'toeic-990-master', 'toeic_level': 990, 'description': 'Từ vựng chuyên sâu chinh phục điểm tuyệt đối.', 'icon': '👑', 'gradient': 'linear-gradient(135deg, #ff9800, #e65100)'},
        ]
        
        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                for data in courses_data:
                    course, created = Course.objects.update_or_create(
                        slug=data['slug'],
                        defaults={
                            'title': data['title'],
                            'toeic_level': data['toeic_level'],
                            'description': data['description'],
                            'icon': data['icon'],
                            'gradient': data['gradient'],
                            'is_active': True
                        }
                    )
                    if created: created_count += 1
                    else: updated_count += 1
            
            messages.success(request, f"Successfully initialized courses: {created_count} created, {updated_count} updated.")
        except Exception as e:
            messages.error(request, f"Error initializing courses: {e}")
            
        return redirect("admin:vocab_course_changelist")
