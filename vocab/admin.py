import json
from django.utils.html import format_html
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
from .models import Vocabulary, WordEntry, WordDefinition, ExampleSentence, VocabularySet, SetItem, SetItemExample, UserSetProgress, Course, VocabSource
from .utils_scraper import scrape_cambridge
from .services.jp_import import import_jp_vocab_data, import_jp_vocab_grouped, distribute_jp_vocab
import nested_admin


class ExampleSentenceInline(nested_admin.NestedTabularInline):
    """Inline examples under WordDefinition"""
    model = ExampleSentence
    extra = 1


class WordDefinitionInline(nested_admin.NestedStackedInline):
    """Inline definitions under WordEntry"""
    model = WordDefinition
    extra = 1
    inlines = [ExampleSentenceInline]


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


class LessonAssignedFilter(admin.SimpleListFilter):
    """Filter JP vocabulary by whether extra_data.lesson is assigned."""
    title = 'Lesson assigned'
    parameter_name = 'lesson_assigned'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Has lesson'),
            ('no', 'No lesson (needs manual assign)'),
        ]

    def queryset(self, request, queryset):
        from django.db.models import Q
        if self.value() == 'yes':
            return queryset.exclude(
                extra_data__lesson__isnull=True
            ).exclude(extra_data__lesson='')
        if self.value() == 'no':
            return queryset.filter(
                Q(extra_data__lesson__isnull=True) |
                Q(extra_data__lesson='') |
                Q(extra_data__lesson=None)
            )
        return queryset


@admin.register(Vocabulary)
class VocabularyAdmin(nested_admin.NestedModelAdmin):
    list_display = ('word', 'language', 'entry_count')
    list_filter = ('language', LessonAssignedFilter)
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
            path('import-jp/', self.admin_site.admin_view(self.import_jp_view), name='vocab_vocabulary_import_jp'),
            path('distribute-jp/', self.admin_site.admin_view(self.distribute_jp_view), name='vocab_vocabulary_distribute_jp'),
            # Quick create VocabularySet API (used by import page)
            path('quick-create-set/', self.admin_site.admin_view(self.quick_create_set_api), name='vocab_vocabulary_quick_create_set'),
            # Manual Distribution 3-Panel
            path('manual-distribute/', self.admin_site.admin_view(self.manual_distribute_view), name='vocab_vocabulary_manual_distribute'),
            path('manual-distribute/api/', self.admin_site.admin_view(self.manual_distribute_api), name='vocab_vocabulary_manual_distribute_api'),
            path('manual-distribute/move/', self.admin_site.admin_view(self.move_to_set_api), name='vocab_vocabulary_move_to_set_api'),
            path('manual-distribute/create-set/', self.admin_site.admin_view(self.create_set_api), name='vocab_vocabulary_create_set_api'),
            path('manual-distribute/set-counts/', self.admin_site.admin_view(self.set_counts_api), name='vocab_vocabulary_set_counts_api'),
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
                                defn = WordDefinition.objects.create(
                                    entry=entry,
                                    meaning=definition_text,
                                )
                                example_text = item.get('example', '')
                                if example_text:
                                    ExampleSentence.objects.create(
                                        definition=defn,
                                        sentence=example_text,
                                        source='cambridge',
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
                                defn = WordDefinition.objects.create(
                                    entry=entry,
                                    meaning=m.get("meaning", ""),
                                    image_url=m.get("image", "")
                                )
                                example_text = m.get("example", "")
                                if example_text:
                                    ExampleSentence.objects.create(
                                        definition=defn,
                                        sentence=example_text,
                                        translation=m.get("example_trans", ""),
                                        source='other',
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
                    defn = WordDefinition.objects.create(
                        entry=entry,
                        meaning=meaning,
                        image_url=image_url or None
                    )
                    if example:
                        ExampleSentence.objects.create(
                            definition=defn,
                            sentence=example,
                            translation=example_trans or "",
                            source='user',
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


    def import_jp_view(self, request):
        """Admin view to import Japanese vocabulary from Mimikara-format JSON."""
        json_data = ''
        if request.method == "POST":
            json_files = request.FILES.getlist('json_files')
            json_data = request.POST.get("json_data", "")
            
            if not json_files and not json_data:
                messages.error(request, "Please select JSON files or enter JSON data.")
                return redirect("admin:vocab_vocabulary_import_jp")

            try:
                # Resolve collection (bộ từ vựng)
                collection = None
                collection_id = request.POST.get("collection")
                if collection_id:
                    try:
                        collection = VocabSource.objects.get(pk=int(collection_id))
                    except (VocabSource.DoesNotExist, ValueError):
                        messages.warning(request, "Bộ từ vựng not found.")

                # Resolve optional VocabularySet within the collection
                vocab_set = None
                set_id = request.POST.get("vocab_set")
                if set_id:
                    try:
                        vocab_set = VocabularySet.objects.get(pk=int(set_id))
                    except (VocabularySet.DoesNotExist, ValueError):
                        pass

                # Check auto-group mode
                auto_group = request.POST.get("auto_group") == "on"

                source = request.POST.get("source", "other")
                default_pos = request.POST.get("default_pos", "noun")

                # -----------------------------------------------------------
                # MODE 1: Auto-group by lesson → 1 set per lesson/section
                # Requires: collection chosen + no specific set selected + auto_group on
                # -----------------------------------------------------------
                if collection and not vocab_set and auto_group:
                    # Collect all (filename, items) pairs
                    file_items_list = []

                    if json_files:
                        for f in json_files:
                            data = json.load(f)
                            if not isinstance(data, list):
                                messages.warning(request, f"Skipped {f.name}: JSON must be a list.")
                                continue
                            file_items_list.append((f.name, data))

                    if json_data:
                        data = json.loads(json_data)
                        if isinstance(data, list):
                            file_items_list.append((None, data))

                    if not file_items_list:
                        messages.error(request, "Không có dữ liệu hợp lệ để import.")
                        return redirect("admin:vocab_vocabulary_import_jp")

                    total_stats = import_jp_vocab_grouped(
                        file_items_list=file_items_list,
                        collection=collection,
                        source=source,
                        default_pos=default_pos,
                    )

                    s = total_stats
                    msg_parts = [f"Import thành công!"]
                    msg_parts.append(f"Từ mới: {s['created_vocabs']}")
                    if s['existing_vocabs']:
                        msg_parts.append(f"Từ đã có: {s['existing_vocabs']}")
                    msg_parts.append(f"Nghĩa: {s['created_definitions']}")
                    if s['created_examples']:
                        msg_parts.append(f"Ví dụ: {s['created_examples']}")
                    msg_parts.append(f"Sets tạo: {s['sets_created']}")
                    msg_parts.append(f"Từ vào set: {s['added_to_set']}")
                    if s['skipped']:
                        msg_parts.append(f"Bỏ qua: {s['skipped']}")
                    msg = ' | '.join(msg_parts) + f" → Bộ: {collection.name}"
                    messages.success(request, msg)

                    # Show details per set
                    for detail in s.get('sets_detail', []):
                        messages.info(
                            request,
                            f"  Ch{detail['chapter']}: {detail['title']} ({detail['count']} từ)"
                        )

                    if s.get('skip_reasons'):
                        messages.warning(
                            request,
                            f"Skip reasons: {' | '.join(s['skip_reasons'][:5])}"
                        )

                    return redirect("admin:vocab_vocabulary_distribute_jp")

                # -----------------------------------------------------------
                # MODE 2: Import all into a single set (legacy behavior)
                # -----------------------------------------------------------
                # Auto-create set if collection chosen but no specific set
                if collection and not vocab_set:
                    set_title = request.POST.get("new_set_title", "").strip()
                    if not set_title:
                        from django.utils import timezone
                        set_title = f"{collection.name} - Import {timezone.now().strftime('%d/%m/%Y %H:%M')}"

                    vocab_set = VocabularySet.objects.create(
                        title=set_title,
                        collection=collection,
                        language=Vocabulary.Language.JAPANESE,
                        is_public=True,
                        status=VocabularySet.Status.PUBLISHED,
                    )
                    messages.info(request, f"Đã tạo set mới: {vocab_set.title}")

                total_stats = {
                    'created_vocabs': 0,
                    'existing_vocabs': 0,
                    'created_definitions': 0,
                    'existing_definitions': 0,
                    'created_examples': 0,
                    'added_to_set': 0,
                    'skipped': 0,
                }

                # Process Files
                if json_files:
                    for f in json_files:
                        data = json.load(f)
                        if not isinstance(data, list):
                            messages.warning(request, f"Skipped {f.name}: JSON must be a list.")
                            continue

                        stats = import_jp_vocab_data(
                            items=data,
                            vocab_set=vocab_set,
                            source=source,
                            default_pos=default_pos,
                        )
                        for k in total_stats:
                            total_stats[k] += stats.get(k, 0)

                # Process Text Area
                if json_data:
                    data = json.loads(json_data)
                    if isinstance(data, list):
                        stats = import_jp_vocab_data(
                            items=data,
                            vocab_set=vocab_set,
                            source=source,
                            default_pos=default_pos,
                        )
                        for k in total_stats:
                            total_stats[k] += stats.get(k, 0)

                s = total_stats
                msg_parts = [f"Import thành công!"]
                msg_parts.append(f"Từ mới: {s['created_vocabs']}")
                if s['existing_vocabs']:
                    msg_parts.append(f"Từ đã có: {s['existing_vocabs']}")
                msg_parts.append(f"Nghĩa mới: {s['created_definitions']}")
                if s['existing_definitions']:
                    msg_parts.append(f"Nghĩa đã có: {s['existing_definitions']}")
                if s['created_examples']:
                    msg_parts.append(f"Ví dụ mới: {s['created_examples']}")
                if s['added_to_set']:
                    msg_parts.append(f"Thêm vào set: {s['added_to_set']}")
                if s['skipped']:
                    msg_parts.append(f"Bỏ qua: {s['skipped']}")
                    skip_reasons = s.get('skip_reasons', [])
                    if skip_reasons:
                        messages.warning(request, f"Skip reasons (mẫu): {' | '.join(skip_reasons[:3])}")
                msg = ' | '.join(msg_parts)
                if collection:
                    msg += f" → Bộ: {collection.name}"
                if vocab_set:
                    msg += f" → Set: {vocab_set.title}"
                messages.success(request, msg)
                
                return redirect("admin:vocab_vocabulary_distribute_jp")

            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON format.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        # GET: prepare context
        # Collections (bộ từ vựng)
        collections = VocabSource.objects.filter(is_active=True).order_by('display_order', 'name')
        if not collections.exists():
            VocabSource.get_or_create_default_sources()
            collections = VocabSource.objects.filter(is_active=True).order_by('display_order', 'name')
        
        # Sets within collections (for JS to filter)
        from django.db.models import Count
        vocab_sets = VocabularySet.objects.filter(
            language=Vocabulary.Language.JAPANESE
        ).annotate(
            word_count=Count('items')
        ).order_by('collection__name', 'title')
        
        # Also include sets without language filter if none found
        if not vocab_sets.exists():
            vocab_sets = VocabularySet.objects.all().annotate(
                word_count=Count('items')
            ).order_by('-created_at')[:50]

        source_types = VocabSource.SourceType.choices

        context = dict(
            self.admin_site.each_context(request),
            title="Import Japanese Vocabulary",
            collections=collections,
            vocab_sets=vocab_sets,
            source_types=source_types,
            json_data=json_data,
        )
        return render(request, "admin/vocab/vocabulary/import_jp.html", context)

    def quick_create_set_api(self, request):
        """API to quickly create a VocabularySet from the import page."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        
        title = request.POST.get('title', '').strip()
        language = request.POST.get('language', 'jp')
        description = request.POST.get('description', '').strip()
        
        if not title:
            return JsonResponse({'error': 'Tên bộ từ vựng không được để trống'}, status=400)
        
        try:
            vocab_set = VocabularySet.objects.create(
                title=title,
                language=language,
                description=description,
                is_public=True,
                status=VocabularySet.Status.PUBLISHED,
            )
            return JsonResponse({
                'id': vocab_set.id,
                'title': vocab_set.title,
                'language': vocab_set.language,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def manual_distribute_view(self, request):
        """3-Panel Manual Distribution UI for JP Vocabulary."""
        from django.db.models import Count
        
        # Get filter from query params
        collection_id = request.GET.get('collection', '')
        
        # Get all collections for filter dropdown
        collections = VocabSource.objects.filter(is_active=True).order_by('display_order', 'name')
        
        # Get all VocabularySets with word count, filtered by collection if selected
        sets_qs = VocabularySet.objects.annotate(
            word_count=Count('items')
        )
        
        if collection_id:
            sets_qs = sets_qs.filter(collection_id=collection_id)
        
        sets = sets_qs.order_by('collection__name', 'toeic_level', 'set_number', 'title')
        
        # Count total JP vocab and unassigned (also filtered by collection if selected)
        if collection_id:
            # Only count vocab in sets belonging to this collection
            vocab_in_collection = SetItem.objects.filter(
                vocabulary_set__collection_id=collection_id
            ).values_list('definition__entry__vocab_id', flat=True).distinct()
            total_vocab = len(set(vocab_in_collection))
            unassigned_count = 0  # When filtering by collection, no "unassigned" concept
        else:
            total_vocab = Vocabulary.objects.filter(language=Vocabulary.Language.JAPANESE).count()
            # Unassigned = JP vocab that has no SetItem pointing to any of its definitions
            assigned_vocab_ids = SetItem.objects.filter(
                definition__entry__vocab__language=Vocabulary.Language.JAPANESE
            ).values_list('definition__entry__vocab_id', flat=True).distinct()
            unassigned_count = total_vocab - len(set(assigned_vocab_ids))
        
        context = dict(
            self.admin_site.each_context(request),
            title="Manual Vocabulary Distribution",
            sets=sets,
            total_vocab=total_vocab,
            unassigned_count=unassigned_count,
            collections=collections,
            current_collection_id=collection_id,
        )
        return render(request, "admin/vocab/vocabulary/manual_distribute.html", context)
    
    def manual_distribute_api(self, request):
        """API to get vocabulary items for a set."""
        set_id = request.GET.get('set_id', 'unassigned')
        
        vocabs = []
        
        if set_id == 'unassigned':
            # Get JP vocab that has no SetItem
            from django.db.models import Exists, OuterRef
            
            has_set_item = SetItem.objects.filter(
                definition__entry__vocab=OuterRef('pk')
            )
            
            unassigned_vocabs = Vocabulary.objects.filter(
                language=Vocabulary.Language.JAPANESE
            ).exclude(
                Exists(has_set_item)
            ).order_by('word')[:500]  # Limit for performance
            
            for v in unassigned_vocabs:
                lesson = ''
                if v.extra_data and isinstance(v.extra_data, dict):
                    lesson = v.extra_data.get('lesson', '')
                vocabs.append({
                    'id': v.id,
                    'word': v.word,
                    'lesson': lesson,
                })
        else:
            # Get vocab in the specified set
            try:
                vocab_set = VocabularySet.objects.get(pk=int(set_id))
                items = SetItem.objects.filter(vocabulary_set=vocab_set).select_related(
                    'definition__entry__vocab'
                ).order_by('display_order', 'id')
                
                for item in items:
                    v = item.definition.entry.vocab
                    lesson = ''
                    if v.extra_data and isinstance(v.extra_data, dict):
                        lesson = v.extra_data.get('lesson', '')
                    vocabs.append({
                        'id': v.id,
                        'word': v.word,
                        'lesson': lesson,
                        'set_item_id': item.id,
                    })
            except (VocabularySet.DoesNotExist, ValueError):
                pass
        
        return JsonResponse({'vocabs': vocabs})
    
    def move_to_set_api(self, request):
        """API to move vocabulary items to a target set."""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
        
        try:
            vocab_ids = json.loads(request.POST.get('vocab_ids', '[]'))
            target_set_id = request.POST.get('target_set_id', '')
            source_set_id = request.POST.get('source_set_id', '')
            
            if not vocab_ids:
                return JsonResponse({'success': False, 'error': 'No vocab_ids provided'})
            
            moved = 0
            
            with transaction.atomic():
                for vocab_id in vocab_ids:
                    try:
                        vocab = Vocabulary.objects.get(pk=int(vocab_id))
                    except Vocabulary.DoesNotExist:
                        continue
                    
                    # Get the first definition for this vocab
                    first_def = WordDefinition.objects.filter(entry__vocab=vocab).first()
                    if not first_def:
                        # Create a placeholder entry and definition if none exists
                        entry, _ = WordEntry.objects.get_or_create(
                            vocab=vocab,
                            part_of_speech='noun',
                            defaults={'ipa': ''}
                        )
                        first_def = WordDefinition.objects.create(
                            entry=entry,
                            meaning=vocab.word
                        )
                    
                    # Remove from source set if it was in one
                    if source_set_id and source_set_id != 'unassigned':
                        SetItem.objects.filter(
                            vocabulary_set_id=int(source_set_id),
                            definition=first_def
                        ).delete()
                    
                    # If moving to unassigned, just remove from all sets
                    if target_set_id == 'unassigned':
                        SetItem.objects.filter(definition=first_def).delete()
                        moved += 1
                        continue
                    
                    # Add to target set
                    try:
                        target_set = VocabularySet.objects.get(pk=int(target_set_id))
                        
                        # Check if already in target set
                        if not SetItem.objects.filter(
                            vocabulary_set=target_set,
                            definition=first_def
                        ).exists():
                            max_order = SetItem.objects.filter(
                                vocabulary_set=target_set
                            ).count()
                            
                            SetItem.objects.create(
                                vocabulary_set=target_set,
                                definition=first_def,
                                display_order=max_order
                            )
                        moved += 1
                    except (VocabularySet.DoesNotExist, ValueError):
                        continue
            
            return JsonResponse({'success': True, 'moved': moved})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def create_set_api(self, request):
        """API to create a new VocabularySet."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        
        title = request.POST.get('title', '').strip()
        toeic_level = request.POST.get('toeic_level', '').strip()
        collection_id = request.POST.get('collection_id', '').strip()
        chapter = request.POST.get('chapter', '').strip()
        
        if not title:
            return JsonResponse({'error': 'Title required'}, status=400)
        
        try:
            # Get collection if provided
            collection = None
            collection_name = None
            if collection_id:
                try:
                    collection = VocabSource.objects.get(pk=int(collection_id))
                    collection_name = collection.name
                except (VocabSource.DoesNotExist, ValueError):
                    pass
            
            # Parse chapter
            chapter_num = None
            if chapter:
                try:
                    chapter_num = int(chapter)
                except ValueError:
                    pass
            
            vocab_set = VocabularySet.objects.create(
                title=title,
                toeic_level=toeic_level if toeic_level else None,
                collection=collection,
                chapter=chapter_num,
                language=collection.language if collection else 'en',
                is_public=True,
                status=VocabularySet.Status.PUBLISHED,
            )
            
            return JsonResponse({
                'id': vocab_set.id,
                'title': vocab_set.title,
                'toeic_level': vocab_set.toeic_level,
                'chapter': vocab_set.chapter,
                'collection_id': collection.id if collection else None,
                'collection_name': collection_name,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def set_counts_api(self, request):
        """API to get updated word counts for sets."""
        from django.db.models import Count, Exists, OuterRef
        
        # Count unassigned JP vocab
        has_set_item = SetItem.objects.filter(
            definition__entry__vocab=OuterRef('pk')
        )
        
        unassigned = Vocabulary.objects.filter(
            language=Vocabulary.Language.JAPANESE
        ).exclude(
            Exists(has_set_item)
        ).count()
        
        # Get counts for all sets
        sets = VocabularySet.objects.annotate(
            word_count=Count('items')
        ).values('id', 'word_count')
        
        return JsonResponse({
            'unassigned': unassigned,
            'sets': [{'id': s['id'], 'count': s['word_count']} for s in sets]
        })

    def distribute_jp_view(self, request):
        """Auto-distribute JP words into VocabularySets by lesson."""
        if request.method == "POST":
            try:
                include_assigned = request.POST.get('include_assigned') == 'on'
                stats = distribute_jp_vocab(
                    source='mimikara_n2',
                    only_unassigned=not include_assigned,
                )
                messages.success(
                    request,
                    f"Distributed! Sets created: {stats['sets_created']}, "
                    f"Sets reused: {stats['sets_reused']}, "
                    f"Words assigned: {stats['words_assigned']}, "
                    f"Already assigned: {stats['already_assigned']}"
                )
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            return redirect("admin:vocab_vocabulary_changelist")

        # GET: show confirmation page
        # Count unassigned JP words with lesson
        from django.db.models import Q, Exists, OuterRef
        jp_with_lesson = Vocabulary.objects.filter(
            language=Vocabulary.Language.JAPANESE,
        ).exclude(extra_data__lesson='').exclude(extra_data__lesson__isnull=True)

        assigned_vocab_ids = SetItem.objects.filter(
            definition__entry__vocab__in=jp_with_lesson
        ).values_list('definition__entry__vocab_id', flat=True).distinct()

        total_jp = jp_with_lesson.count()
        assigned = assigned_vocab_ids.count()
        unassigned = total_jp - assigned

        # Distinct lessons
        lessons = set()
        for ed in jp_with_lesson.values_list('extra_data', flat=True):
            if ed and ed.get('lesson'):
                lessons.add(ed['lesson'].split('|')[0].strip())

        context = dict(
            self.admin_site.each_context(request),
            title="Auto-distribute JP Vocabulary",
            total_jp=total_jp,
            assigned=assigned,
            unassigned=unassigned,
            lesson_count=len(lessons),
        )
        return render(request, "admin/vocab/vocabulary/distribute_jp.html", context)


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


@admin.register(ExampleSentence)
class ExampleSentenceAdmin(admin.ModelAdmin):
    list_display = ('get_word', 'sentence_preview', 'source', 'order', 'created_at')
    list_filter = ('source',)
    search_fields = ('sentence', 'translation', 'definition__entry__vocab__word')
    autocomplete_fields = ['definition']

    def get_word(self, obj):
        return obj.definition.entry.vocab.word
    get_word.short_description = "Word"
    get_word.admin_order_field = 'definition__entry__vocab__word'

    def sentence_preview(self, obj):
        return obj.sentence[:80] + ('...' if len(obj.sentence) > 80 else '')
    sentence_preview.short_description = "Sentence"


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
            path('course-sets/', self.admin_site.admin_view(self.course_sets_api), name='vocab_vocabularyset_course_sets'),
            path('<int:set_id>/add-words/', self.admin_site.admin_view(self.add_words_to_set_api), name='vocab_vocabularyset_add_words'),
            path('<int:set_id>/manage-words/', self.admin_site.admin_view(self.manage_words_view), name='vocab_vocabularyset_manage_words'),
            path('<int:set_id>/remove-word/<int:word_id>/', self.admin_site.admin_view(self.remove_word_from_set_api), name='vocab_vocabularyset_remove_word'),
            path('<int:set_id>/move-words/', self.admin_site.admin_view(self.move_words_api), name='vocab_vocabularyset_move_words'),
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

        # Get all courses for dropdown
        courses = Course.objects.filter(is_active=True).order_by('toeic_level')
        courses_data = []
        for c in courses:
            sets = VocabularySet.objects.filter(toeic_level=c.toeic_level).order_by('set_number')
            courses_data.append({
                'id': c.id,
                'title': c.title,
                'toeic_level': c.toeic_level,
                'set_count': sets.count(),
            })

        context = dict(
            self.admin_site.each_context(request),
            title="Quick Add Vocabulary Set",
            toeic_levels=VocabularySet.ToeicLevel.choices,
            languages=Vocabulary.Language.choices,
            statuses=VocabularySet.Status.choices,
            courses=courses,
            courses_json=json.dumps(courses_data),
        )
        return render(request, "admin/vocab/vocabularyset/quick_add.html", context)

    def course_sets_api(self, request):
        """API endpoint to get sets for a given course/toeic_level."""
        toeic_level = request.GET.get('toeic_level')
        if not toeic_level:
            return JsonResponse({'sets': []})

        try:
            toeic_level = int(toeic_level)
        except ValueError:
            return JsonResponse({'sets': []})

        sets = VocabularySet.objects.filter(
            toeic_level=toeic_level
        ).order_by('chapter', 'set_number')

        results = []
        for s in sets:
            results.append({
                'id': s.id,
                'title': s.title,
                'set_number': s.set_number,
                'chapter': s.chapter,
                'chapter_name': s.chapter_name,
                'milestone': s.milestone,
                'word_count': s.items.count(),
                'status': s.status,
            })

        return JsonResponse({'sets': results})

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
        ).order_by('display_order', 'id')

        # Get all other sets for "Move to..." dropdown
        all_sets = VocabularySet.objects.exclude(pk=set_id).order_by(
            'toeic_level', 'set_number', 'chapter'
        ).values('id', 'title', 'set_number', 'toeic_level', 'chapter_name', 'milestone')

        context = dict(
            self.admin_site.each_context(request),
            title=f"Manage Words: {vocab_set.title}",
            vocab_set=vocab_set,
            set_items=set_items,
            all_sets=list(all_sets),
        )
        return render(request, "admin/vocab/vocabularyset/manage_words.html", context)


    def move_words_api(self, request, set_id):
        """API to move selected words from current set to another set."""
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)

        try:
            data = json.loads(request.body)
            target_set_id = data.get('target_set_id')
            word_def_ids = data.get('word_ids', [])

            if not target_set_id or not word_def_ids:
                return JsonResponse({"error": "Target set and word IDs are required"}, status=400)

            # verify sets exist
            source_set = VocabularySet.objects.get(pk=set_id)
            target_set = VocabularySet.objects.get(pk=target_set_id)

            moved_count = 0
            with transaction.atomic():
                # Get items to move
                items_to_move = SetItem.objects.filter(
                    vocabulary_set=source_set, 
                    definition_id__in=word_def_ids
                )
                
                # Get existing definitions in target set to avoid duplicates
                existing_defs_in_target = SetItem.objects.filter(
                    vocabulary_set=target_set,
                    definition_id__in=word_def_ids
                ).values_list('definition_id', flat=True)
                
                # Create links in target set for words NOT already there
                new_items = []
                current_target_count = target_set.items.count()
                
                for item in items_to_move:
                    if item.definition_id not in existing_defs_in_target:
                        new_items.append(SetItem(
                            vocabulary_set=target_set,
                            definition=item.definition,
                            display_order=current_target_count + len(new_items)
                        ))
                
                if new_items:
                    SetItem.objects.bulk_create(new_items)
                
                # Delete from source set
                count, _ = items_to_move.delete()
                moved_count = count

            return JsonResponse({
                "success": True, 
                "moved_count": moved_count,
                "message": f"Moved {moved_count} words to {target_set.title}"
            })

        except VocabularySet.DoesNotExist:
            return JsonResponse({"error": "Set not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

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
                                    defn = WordDefinition.objects.create(
                                        entry=word_entry,
                                        meaning=entry_data.get('definition', ''),
                                    )
                                    example_text = entry_data.get('example', '')
                                    if example_text:
                                        ExampleSentence.objects.create(
                                            definition=defn,
                                            sentence=example_text,
                                            source='cambridge',
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


class SetItemExampleInline(admin.TabularInline):
    model = SetItemExample
    extra = 1
    autocomplete_fields = ['example']


@admin.register(SetItem)
class SetItemAdmin(admin.ModelAdmin):
    list_display = ('vocabulary_set', 'definition', 'display_order', 'example_count')
    list_filter = ('vocabulary_set',)
    search_fields = ('vocabulary_set__title', 'definition__entry__vocab__word')
    inlines = [SetItemExampleInline]

    def example_count(self, obj):
        return obj.set_examples.count()
    example_count.short_description = "Set Examples"


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
            {'title': 'TOEIC 600 Cơ bản', 'slug': 'toeic-600-essential', 'toeic_level': 600, 'description': 'Từ vựng cơ bản dành cho người mới bắt đầu.', 'icon': '🌱', 'gradient': 'linear-gradient(135deg, #4caf50, #2e7d32)'},
            {'title': 'TOEIC 730 Trung cấp', 'slug': 'toeic-730-intermediate', 'toeic_level': 730, 'description': 'Từ vựng trung cấp dành cho môi trường công sở.', 'icon': '📘', 'gradient': 'linear-gradient(135deg, #2196f3, #1565c0)'},
            {'title': 'TOEIC 860 Nâng cao', 'slug': 'toeic-860-advanced', 'toeic_level': 860, 'description': 'Từ vựng nâng cao để đạt điểm xuất sắc.', 'icon': '🔮', 'gradient': 'linear-gradient(135deg, #9c27b0, #6a1b9a)'},
            {'title': 'TOEIC 990 Chuyên gia', 'slug': 'toeic-990-master', 'toeic_level': 990, 'description': 'Từ vựng chuyên sâu chinh phục điểm tuyệt đối.', 'icon': '👑', 'gradient': 'linear-gradient(135deg, #ff9800, #e65100)'},
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


@admin.register(VocabSource)
class VocabSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'source_type', 'language', 'level', 'is_active', 'display_order', 'cover_image_preview')
    list_filter = ('source_type', 'language', 'is_active')
    search_fields = ('code', 'name', 'description')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'source_type')
        }),
        ('Details', {
            'fields': ('description', 'language', 'level', 'publisher')
        }),
        ('Ảnh bìa', {
            'fields': ('cover_image', 'cover_image_large_preview'),
            'description': 'Upload ảnh bìa 600×330px (WebP/JPG). Ảnh sẽ được lưu trên Azure.'
        }),
        ('Settings', {
            'fields': ('is_active', 'display_order')
        }),
    )

    readonly_fields = ('cover_image_large_preview',)

    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="height:40px; width:72px; object-fit:cover; border-radius:6px; border:1px solid #e2e8f0;"/>',
                obj.cover_image.url
            )
        return '—'
    cover_image_preview.short_description = 'Ảnh'

    def cover_image_large_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width:600px; max-height:330px; border-radius:12px; border:1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"/>',
                obj.cover_image.url
            )
        return 'Chưa có ảnh'
    cover_image_large_preview.short_description = 'Xem trước'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('init-defaults/', self.admin_site.admin_view(self.init_defaults_view), name='vocab_vocabsource_init_defaults'),
            path('api/create/', self.admin_site.admin_view(self.create_api), name='vocab_vocabsource_create_api'),
        ]
        return custom_urls + urls
    
    def init_defaults_view(self, request):
        """Initialize default sources."""
        VocabSource.get_or_create_default_sources()
        messages.success(request, "Default sources initialized successfully.")
        return redirect("admin:vocab_vocabsource_changelist")
    
    def create_api(self, request):
        """API to create a new source (used by import page)."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)
        
        code = request.POST.get('code', '').strip().lower()
        name = request.POST.get('name', '').strip()
        source_type = request.POST.get('source_type', 'book')
        language = request.POST.get('language', '')
        level = request.POST.get('level', '')
        
        if not code or not name:
            return JsonResponse({'error': 'Code and name are required'}, status=400)
        
        # Sanitize code
        import re
        code = re.sub(r'[^a-z0-9_]', '_', code)
        
        # Check if exists
        if VocabSource.objects.filter(code=code).exists():
            source = VocabSource.objects.get(code=code)
            return JsonResponse({
                'id': source.id,
                'code': source.code,
                'name': source.name,
                'exists': True,
            })
        
        try:
            source = VocabSource.objects.create(
                code=code,
                name=name,
                source_type=source_type,
                language=language,
                level=level,
                is_active=True,
            )
            return JsonResponse({
                'id': source.id,
                'code': source.code,
                'name': source.name,
                'exists': False,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
