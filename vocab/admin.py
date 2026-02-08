import json
import os
import uuid
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.http import HttpResponseRedirect
from django import forms
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
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
            path('upload-image/', self.admin_site.admin_view(self.upload_image_api), name='vocab_vocabulary_upload_image'),
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
            image_url = request.POST.get("image_url", "")
            
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

                    # Create Definition with image_url
                    WordDefinition.objects.create(
                        entry=entry,
                        meaning=meaning,
                        example_sentence=example or "",
                        example_trans=example_trans or "",
                        image_url=image_url or None
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

    def upload_image_api(self, request):
        """
        API endpoint to upload vocabulary image to Azure Storage.
        Returns the public URL of the uploaded image.
        """
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
        
        if "image" not in request.FILES:
            return JsonResponse({"error": "No image file provided"}, status=400)
        
        image_file = request.FILES["image"]
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                "error": "Invalid file type. Allowed: JPEG, PNG, GIF, WebP"
            }, status=400)
        
        # Validate file size (max 5MB)
        if image_file.size > 5 * 1024 * 1024:
            return JsonResponse({
                "error": "File too large. Maximum size is 5MB"
            }, status=400)
        
        try:
            # Generate unique filename
            ext = os.path.splitext(image_file.name)[1].lower() or ".jpg"
            unique_name = f"vocab/images/{uuid.uuid4().hex}{ext}"
            
            # Use Django's default storage (configured for Azure in production)
            from config.storage_backends import AzureMediaStorage
            
            storage = AzureMediaStorage()
            saved_name = storage.save(unique_name, image_file)
            image_url = storage.url(saved_name)
            
            return JsonResponse({
                "success": True,
                "url": image_url,
                "filename": saved_name
            })
            
        except Exception as e:
            return JsonResponse({
                "error": f"Upload failed: {str(e)}"
            }, status=500)


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
    change_list_template = "admin/vocab/vocabularyset/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name='vocab_vocabularyset_import_json'),
            path('quick-add/', self.admin_site.admin_view(self.quick_add_set_view), name='vocab_vocabularyset_quick_add'),
            path('search-words/', self.admin_site.admin_view(self.search_words_api), name='vocab_vocabularyset_search_words'),
            path('<int:set_id>/add-words/', self.admin_site.admin_view(self.add_words_to_set_api), name='vocab_vocabularyset_add_words'),
            path('<int:set_id>/manage-words/', self.admin_site.admin_view(self.manage_words_view), name='vocab_vocabularyset_manage_words'),
            path('<int:set_id>/remove-word/<int:word_id>/', self.admin_site.admin_view(self.remove_word_from_set_api), name='vocab_vocabularyset_remove_word'),
        ]
        return custom_urls + urls

    def quick_add_set_view(self, request):
        """View for quickly creating a new vocabulary set."""
        if request.method == "POST":
            title = request.POST.get("title", "").strip()
            description = request.POST.get("description", "")
            language = request.POST.get("language", Vocabulary.Language.ENGLISH)
            toeic_level = request.POST.get("toeic_level") or None
            set_number = request.POST.get("set_number") or None
            chapter = request.POST.get("chapter") or None
            chapter_name = request.POST.get("chapter_name", "")
            status = request.POST.get("status", "draft")

            if not title:
                messages.error(request, "Title is required.")
                return redirect("admin:vocab_vocabularyset_quick_add")

            try:
                if toeic_level:
                    toeic_level = int(toeic_level)
                if set_number:
                    set_number = int(set_number)
                if chapter:
                    chapter = int(chapter)

                vocab_set = VocabularySet.objects.create(
                    title=title,
                    description=description,
                    language=language,
                    toeic_level=toeic_level,
                    set_number=set_number,
                    chapter=chapter,
                    chapter_name=chapter_name,
                    status=status,
                    is_public=True,
                )
                messages.success(request, f"Created set: '{title}'")
                
                # Redirect to manage words if requested
                if "save_and_add_words" in request.POST:
                    return redirect("admin:vocab_vocabularyset_manage_words", set_id=vocab_set.id)
                return redirect("admin:vocab_vocabularyset_changelist")

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        context = dict(
            self.admin_site.each_context(request),
            title="Quick Add Vocabulary Set",
            toeic_levels=VocabularySet.ToeicLevel.choices,
            languages=Vocabulary.Language.choices,
            statuses=VocabularySet.Status.choices,
        )
        return render(request, "admin/vocab/vocabularyset/quick_add.html", context)

    def manage_words_view(self, request, set_id):
        """View for managing words in a set."""
        try:
            vocab_set = VocabularySet.objects.get(pk=set_id)
        except VocabularySet.DoesNotExist:
            messages.error(request, "Set not found.")
            return redirect("admin:vocab_vocabularyset_changelist")

        # Get current words in set
        set_items = SetItem.objects.filter(vocabulary_set=vocab_set).select_related(
            'definition__entry__vocab'
        ).order_by('order', 'id')

        context = dict(
            self.admin_site.each_context(request),
            title=f"Manage Words: {vocab_set.title}",
            vocab_set=vocab_set,
            set_items=set_items,
        )
        return render(request, "admin/vocab/vocabularyset/manage_words.html", context)

    def search_words_api(self, request):
        """API endpoint to search for existing words."""
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse({"results": []})

        # Search in Vocabulary and WordDefinition
        definitions = WordDefinition.objects.filter(
            models.Q(entry__vocab__word__icontains=query) |
            models.Q(meaning__icontains=query)
        ).select_related('entry__vocab').distinct()[:20]

        results = []
        for defn in definitions:
            results.append({
                "id": defn.id,
                "word": defn.entry.vocab.word,
                "meaning": defn.meaning[:100] + ("..." if len(defn.meaning) > 100 else ""),
                "pos": defn.entry.part_of_speech or "",
                "ipa": defn.entry.ipa or "",
            })

        return JsonResponse({"results": results})

    def add_words_to_set_api(self, request, set_id):
        """API endpoint to add words to a set."""
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)

        try:
            vocab_set = VocabularySet.objects.get(pk=set_id)
        except VocabularySet.DoesNotExist:
            return JsonResponse({"error": "Set not found"}, status=404)

        try:
            data = json.loads(request.body)
            word_ids = data.get("word_ids", [])
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        added = 0
        for word_id in word_ids:
            try:
                definition = WordDefinition.objects.get(pk=word_id)
                _, created = SetItem.objects.get_or_create(
                    vocabulary_set=vocab_set,
                    definition=definition
                )
                if created:
                    added += 1
            except WordDefinition.DoesNotExist:
                continue

        return JsonResponse({"success": True, "added": added})

    def remove_word_from_set_api(self, request, set_id, word_id):
        """API endpoint to remove a word from a set."""
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)

        try:
            SetItem.objects.filter(vocabulary_set_id=set_id, definition_id=word_id).delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def import_json_view(self, request):
        if request.method == "POST":
            json_data = request.POST.get("json_data")
            if not json_data:
                messages.error(request, "Please enter JSON data.")
                return redirect("admin:vocab_vocabularyset_import_json")

            try:
                data = json.loads(json_data)
                
                # Normalize data to a list of sets
                items_to_process = []
                default_level = None
                
                if isinstance(data, list):
                    items_to_process = data
                elif isinstance(data, dict):
                    # Handle complex structure: { meta: {...}, sets: [...] }
                    if 'sets' in data:
                        items_to_process = data['sets']
                        # Try to get level from meta
                        if 'meta' in data and 'level' in data['meta']:
                            default_level = data['meta']['level']
                    else:
                        messages.error(request, "JSON dict must contain 'sets' key.")
                        return redirect("admin:vocab_vocabularyset_import_json")
                else:
                    messages.error(request, "JSON must be a list or a compatible object.")
                    return redirect("admin:vocab_vocabularyset_import_json")

                created_sets = 0
                created_words = 0
                
                with transaction.atomic():
                    for item in items_to_process:
                        # Determine TOEIC Level
                        toeic_level = item.get('toeic_level') or default_level
                        set_number = item.get('set_number')
                        
                        if not toeic_level or not set_number:
                            continue
                        
                        # Prepare fields
                        chapter_name = item.get('chapter_name') or item.get('chapter_name_vi') or ''
                        
                        # Priority range
                        p_start = item.get('priority_start')
                        p_end = item.get('priority_end')
                        priority_range = item.get('priority_range', '')
                        if not priority_range and p_start and p_end:
                            priority_range = f"{p_start}-{p_end}"

                        # Create/Update VocabularySet
                        title = f"TOEIC {toeic_level} - Set {set_number}"
                        vocab_set, created = VocabularySet.objects.update_or_create(
                            toeic_level=toeic_level,
                            set_number=set_number,
                            defaults={
                                'title': title,
                                'chapter': item.get('chapter', 1),
                                'chapter_name': chapter_name,
                                'milestone': item.get('milestone', ''),
                                'priority_range': priority_range,
                                'status': 'published',
                            }
                        )
                        if created:
                            created_sets += 1
                        
                        # Process words
                        words = item.get('words', [])
                        for word_text in words:
                            word_text = word_text.strip().lower()
                            if not word_text:
                                continue
                            
                            # Check if word exists with definitions
                            vocab = Vocabulary.objects.filter(word=word_text).first()
                            if vocab and WordDefinition.objects.filter(entry__vocab=vocab).exists():
                                # Reuse existing
                                pass
                            else:
                                # Scrape from Cambridge
                                scraped_entries = scrape_cambridge(word_text)
                                if not scraped_entries:
                                    continue
                                
                                vocab, _ = Vocabulary.objects.get_or_create(
                                    word=word_text,
                                    defaults={'language': 'en'}
                                )
                                
                                for entry_data in scraped_entries:
                                    word_entry, _ = WordEntry.objects.get_or_create(
                                        vocab=vocab,
                                        part_of_speech=entry_data.get('type', ''),
                                        defaults={
                                            'ipa': entry_data.get('ipa', ''),
                                            'audio_us': entry_data.get('audio_us', ''),
                                            'audio_uk': entry_data.get('audio_uk', ''),
                                        }
                                    )
                                    WordDefinition.objects.create(
                                        entry=word_entry,
                                        meaning=entry_data.get('definition', ''),
                                        example_sentence=entry_data.get('example', ''),
                                    )
                                    created_words += 1
                            
                            # Link to Set
                            if vocab:
                                first_def = WordDefinition.objects.filter(entry__vocab=vocab).first()
                                if first_def:
                                    SetItem.objects.get_or_create(
                                        vocabulary_set=vocab_set,
                                        definition=first_def
                                    )
                
                messages.success(request, f"Successfully imported: {created_sets} sets, {created_words} new words scraped.")
                return redirect("admin:vocab_vocabularyset_changelist")

            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON format.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        context = dict(
           self.admin_site.each_context(request),
           title="Import Vocabulary Set from JSON"
        )
        return render(request, "admin/vocab/vocabularyset/import_json.html", context)

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
