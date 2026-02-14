from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q, Case, When, Value, IntegerField, F
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
import json
import random
from .models import VocabularySet, SetItem, WordDefinition, WordEntry, Vocabulary, FsrsCardStateEn, UserSetProgress, Course, ExampleSentence
from .toeic_config import TOEIC_LEVELS, TOEIC_LEVEL_ORDER
from . import toeic_utils
from .fsrs_bridge import create_new_card_state, review_card, preview_intervals
from .utils import card_data_to_dict


# ---------------------------------------------------------------------------
# Rate-limit decorator (uses Django cache, no extra dependencies)
# ---------------------------------------------------------------------------

def rate_limit(key_prefix, max_calls=60, period=60):
    """
    Simple per-user rate limiter.
    Allows *max_calls* requests per *period* seconds.
    Falls back to IP when user is anonymous.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            uid = request.user.pk if request.user.is_authenticated else None
            ident = uid or request.META.get('REMOTE_ADDR', '0')
            cache_key = f"rl:{key_prefix}:{ident}"

            calls = cache.get(cache_key, 0)
            if calls >= max_calls:
                return JsonResponse(
                    {'error': 'Too many requests. Please slow down.'},
                    status=429,
                )
            cache.set(cache_key, calls + 1, period)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

class SetListView(ListView):
    """
    List public sets and user's private sets.
    """
    model = VocabularySet
    template_name = 'vocab/set_list.html'
    context_object_name = 'sets'
    paginate_by = 12

    def get_queryset(self):
        queryset = VocabularySet.objects.filter(is_public=True)
        if self.request.user.is_authenticated:
            # Show my private sets + public sets
            queryset = VocabularySet.objects.filter(
                Q(is_public=True) | Q(owner=self.request.user)
            ).distinct()
        
        # Filter by tab (my_sets vs public)
        tab = self.request.GET.get('tab')
        if tab == 'my' and self.request.user.is_authenticated:
             queryset = VocabularySet.objects.filter(owner=self.request.user)
        
        # Filter by language
        lang = self.request.GET.get('lang')
        if lang in ['en', 'jp']:
            queryset = queryset.filter(language=lang)
        
        return queryset.annotate(
            is_toeic=Case(
                When(toeic_level__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-is_toeic', 'toeic_level', 'set_number', '-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'all')
        context['current_lang'] = self.request.GET.get('lang', 'all')
        return context

class SetDetailView(DetailView):
    model = VocabularySet
    template_name = 'vocab/set_detail.html'
    context_object_name = 'vocab_set'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get items for this set
        items = self.object.items.select_related(
            'definition__entry__vocab'
        ).prefetch_related('definition__examples').order_by('display_order', 'created_at')
        context['items'] = items
        return context

class SetCreateView(LoginRequiredMixin, CreateView):
    model = VocabularySet
    template_name = 'vocab/set_form.html'
    fields = ['title', 'description', 'is_public', 'status']
    success_url = reverse_lazy('vocab:set_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Vocabulary set created successfully.")
        return super().form_valid(form)

class SetStudyView(DetailView):
    model = VocabularySet
    template_name = 'vocab/set_study.html'
    context_object_name = 'vocab_set'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get items for this set
        items = self.object.items.select_related(
            'definition__entry__vocab'
        ).prefetch_related('definition__examples').order_by('display_order', 'created_at')

        items_data = []
        for item in items:
            d = item.definition
            e = d.entry  # WordEntry (has ipa, audio)
            v = e.vocab  # Vocabulary (has word)
            items_data.append({
                'id': v.id, # Use Vocab ID for grading API
                'set_item_id': item.id,
                'word': v.word,
                'ipa': e.ipa,
                'audio_url': e.get_audio_url('us'),  # Default to US
                'audio_us': e.audio_us,
                'audio_uk': e.audio_uk,
                'meaning': d.meaning,
                'part_of_speech': e.part_of_speech,
                'example': d.example_sentence,
                'example_trans': d.example_trans,
                'extra_data': {**v.extra_data, **d.extra_data}
            })
            
        context['items_json'] = json.dumps(items_data)
        return context

class SetUpdateView(LoginRequiredMixin, UpdateView):
    model = VocabularySet
    template_name = 'vocab/set_form.html'
    fields = ['title', 'description', 'is_public', 'status']

    def get_queryset(self):
        # Only allow editing own sets
        return VocabularySet.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('vocab:set_detail', kwargs={'pk': self.object.pk})

class SetDeleteView(LoginRequiredMixin, DeleteView):
    model = VocabularySet
    template_name = 'vocab/set_confirm_delete.html'
    success_url = reverse_lazy('vocab:set_list')

    def get_queryset(self):
        return VocabularySet.objects.filter(owner=self.request.user)


def search_words_api(request):
    """
    API to search words and definitions to add to a set.
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    # Search in Vocabulary (word) and WordDefinition (meaning)
    definitions = WordDefinition.objects.filter(
        Q(entry__vocab__word__icontains=query) | Q(meaning__icontains=query)
    ).select_related('entry__vocab')[:20]
    
    results = []
    for d in definitions:
        results.append({
            'id': d.id,
            'word': d.entry.vocab.word,
            'meaning': d.meaning,
            'pos': d.entry.part_of_speech,
            'text': f"{d.entry.vocab.word} ({d.entry.part_of_speech}) - {d.meaning}"
        })
    
    return JsonResponse(results, safe=False)


def add_item_api(request, set_id):
    """
    Add a definition to a set (AJAX).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    if not request.user.is_authenticated:
         return JsonResponse({"error": "Unauthorized"}, status=401)

    vocab_set = get_object_or_404(VocabularySet, id=set_id, owner=request.user)
    definition_id = request.POST.get('definition_id')
    
    if not definition_id:
        return JsonResponse({"error": "Missing definition_id"}, status=400)

    try:
        definition = WordDefinition.objects.get(id=definition_id)
        # Check if already exists
        if SetItem.objects.filter(vocabulary_set=vocab_set, definition=definition).exists():
             return JsonResponse({"error": "Item already in set"}, status=400)
        
        SetItem.objects.create(vocabulary_set=vocab_set, definition=definition)
        return JsonResponse({"success": True})
    except WordDefinition.DoesNotExist:
        return JsonResponse({"error": "Definition not found"}, status=404)

def remove_item_api(request, set_id):
    """
    Remove ability from set.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    vocab_set = get_object_or_404(VocabularySet, id=set_id, owner=request.user)
    item_id = request.POST.get('item_id')

    try:
        item = SetItem.objects.get(id=item_id, vocabulary_set=vocab_set)
        item.delete()
        return JsonResponse({"success": True})
    except SetItem.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)


@require_http_methods(["GET", "POST"])
@login_required
def import_json_view(request, pk):
    """
    Import vocabulary from JSON file into a VocabularySet.
    
    Supported formats:
    - English: {"language": "en", "words": [{"word": "...", "part_of_speech": "...", "ipa": "...", "meaning": "...", "example": "...", "example_trans": "..."}]}
    - Japanese: {"language": "jp", "words": [{"word": "...", "part_of_speech": "...", "reading": "...", "romaji": "...", "meaning": "...", "example": "...", "example_trans": "...", "furigana": "..."}]}
    """
    import json
    
    vocab_set = get_object_or_404(VocabularySet, id=pk, owner=request.user)
    
    if request.method == "GET":
        # Show import form
        return render(request, 'vocab/set_import.html', {'vocab_set': vocab_set})
    
    # POST - handle file upload or text input
    json_file = request.FILES.get('json_file')
    json_text = request.POST.get('json_text')
    
    data = None
    try:
        if json_file:
            data = json.load(json_file)
        elif json_text:
            data = json.loads(json_text)
        else:
            messages.error(request, "Vui lòng chọn file JSON hoặc nhập nội dung JSON.")
            return redirect('vocab:set_import', pk=pk)
    except json.JSONDecodeError as e:
        messages.error(request, f"File JSON không hợp lệ: {e}")
        return redirect('vocab:set_import', pk=pk)
    
    # Validate structure
    if 'words' not in data or not isinstance(data['words'], list):
        messages.error(request, "JSON phải có key 'words' chứa danh sách từ vựng.")
        return redirect('vocab:set_import', pk=pk)
    
    language = data.get('language', 'en')
    if language not in ['en', 'jp']:
        messages.error(request, "Language phải là 'en' hoặc 'jp'.")
        return redirect('vocab:set_import', pk=pk)
    
    # Update set language if needed
    if vocab_set.language != language:
        vocab_set.language = language
        vocab_set.save(update_fields=['language'])
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    for idx, word_data in enumerate(data['words']):
        try:
            word_text = word_data.get('word', '').strip()
            if not word_text:
                errors.append(f"Row {idx + 1}: Missing 'word' field")
                continue
            
            part_of_speech = word_data.get('part_of_speech', 'noun').strip()
            meaning = word_data.get('meaning', '').strip()
            
            if not meaning:
                errors.append(f"Row {idx + 1}: Missing 'meaning' for '{word_text}'")
                continue
            
            # Build extra_data for Japanese
            extra_data = {}
            if language == 'jp':
                if word_data.get('reading'):
                    extra_data['reading'] = word_data['reading']
                if word_data.get('romaji'):
                    extra_data['romaji'] = word_data['romaji']
                if word_data.get('han_viet'):
                    extra_data['han_viet'] = word_data['han_viet']
            
            # Get or create Vocabulary
            vocab_obj, _ = Vocabulary.objects.get_or_create(
                word=word_text,
                defaults={
                    'language': language,
                    'extra_data': extra_data
                }
            )
            # Update extra_data if vocab already existed
            if extra_data and vocab_obj.extra_data != extra_data:
                vocab_obj.extra_data = extra_data
                vocab_obj.save(update_fields=['extra_data'])
            
            # Get or create WordEntry
            entry_obj, _ = WordEntry.objects.get_or_create(
                vocab=vocab_obj,
                part_of_speech=part_of_speech,
                defaults={
                    'ipa': word_data.get('ipa', ''),
                    'audio_us': word_data.get('audio_us', ''),
                    'audio_uk': word_data.get('audio_uk', ''),
                }
            )
            
            # Build definition extra_data
            def_extra = {}
            if language == 'jp' and word_data.get('furigana'):
                def_extra['furigana'] = word_data['furigana']
            
            # Get or create WordDefinition
            definition_obj, created = WordDefinition.objects.get_or_create(
                entry=entry_obj,
                meaning=meaning,
                defaults={
                    'extra_data': def_extra,
                }
            )
            # Create ExampleSentence if provided
            example_text = word_data.get('example', '')
            if created and example_text:
                ExampleSentence.objects.create(
                    definition=definition_obj,
                    sentence=example_text,
                    translation=word_data.get('example_trans', ''),
                    source='user',
                )
            
            # Check if already in set
            if SetItem.objects.filter(vocabulary_set=vocab_set, definition=definition_obj).exists():
                skipped_count += 1
                continue
            
            # Add to set
            SetItem.objects.create(vocabulary_set=vocab_set, definition=definition_obj)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
    
    # Build result message
    if imported_count > 0:
        messages.success(request, f"Đã import thành công {imported_count} từ vựng!")
    if skipped_count > 0:
        messages.warning(request, f"Bỏ qua {skipped_count} từ đã có trong bộ.")
    if errors:
        messages.error(request, f"Có {len(errors)} lỗi: " + "; ".join(errors[:5]))
    
    return redirect('vocab:set_detail', pk=pk)



class GamesView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/games.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate ready count (example logic: words with due reviews)
        # For now, just return total count or 0 if not implemented
        context['ready_count'] = WordDefinition.objects.filter(entry__vocab__language=Vocabulary.Language.ENGLISH).count() 
        return context



class VocabularyDetailView(LoginRequiredMixin, DetailView):
    model = Vocabulary
    template_name = 'vocab/vocabulary_detail.html'
    context_object_name = 'vocab'
    
    def get_object(self, queryset=None):
        word = self.kwargs.get('word')
        # Case-insensitive lookup
        return get_object_or_404(Vocabulary, word__iexact=word)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch entries and definitions
        context['entries'] = self.object.entries.prefetch_related('definitions__examples').order_by('part_of_speech')
        return context


class ProgressView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/progress.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add basic FSRS stats if needed, or leave for template to load via API
        return context

class StudyStatusView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/study_status.html'

class TypingView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/type_review.html'

class PhraseListView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/phrase_list.html'



# ======================================
# TOEIC Views
# ======================================

class CourseListView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/toeic/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get active courses - TOEIC first (by level), then non-TOEIC
        courses = Course.objects.filter(is_active=True).order_by(
            F('toeic_level').asc(nulls_last=True), 'title'
        )

        # Calculate stats for each course
        courses_data = []
        for course in courses:
            level = course.toeic_level

            if level:
                # TOEIC course - use existing toeic_utils
                completion = toeic_utils.get_level_completion_percent(user, level)
                learned_count = toeic_utils.get_level_words_learned_count(user, level)
                total_sets = VocabularySet.objects.filter(toeic_level=level, status='published').count()
                total_words = SetItem.objects.filter(
                    vocabulary_set__toeic_level=level,
                    vocabulary_set__status='published'
                ).count()
                completed_sets = UserSetProgress.objects.filter(
                    user=user,
                    vocabulary_set__toeic_level=level,
                    status=UserSetProgress.ProgressStatus.COMPLETED
                ).count()
            else:
                # Non-TOEIC course (e.g. JP) - calculate stats from language
                lang = course.language
                jp_sets_qs = VocabularySet.objects.filter(language=lang, toeic_level__isnull=True, status='published')
                total_sets = jp_sets_qs.count()
                total_words = SetItem.objects.filter(
                    vocabulary_set__in=jp_sets_qs
                ).count()
                completed_sets = UserSetProgress.objects.filter(
                    user=user,
                    vocabulary_set__in=jp_sets_qs,
                    status=UserSetProgress.ProgressStatus.COMPLETED
                ).count()
                # Learned words via FSRS
                jp_vocab_ids = SetItem.objects.filter(
                    vocabulary_set__in=jp_sets_qs
                ).values_list('definition__entry__vocab_id', flat=True)
                learned_count = FsrsCardStateEn.objects.filter(
                    user=user, vocab_id__in=jp_vocab_ids, state__gte=2
                ).count()
                completion = round(learned_count / total_words * 100) if total_words > 0 else 0

            courses_data.append({
                'object': course,
                'slug': course.slug,
                'completion': completion,
                'words_learned': learned_count,
                'total_sets': total_sets,
                'total_words': total_words,
                'completed_sets': completed_sets,
                'config': {
                    'label': course.title,
                    'description': course.description,
                    'icon': course.icon,
                    'gradient': course.gradient,
                    'level': level,
                    'language': course.language,
                }
            })

        # Calculate total review count across all levels
        review_count = 0
        if user.is_authenticated:
            # Global FSRS review count
            try:
                from vocab.services import FsrsService
                review_count = FsrsService.get_due_cards(user).count()
            except ImportError:
                pass  # Handle case where FsrsService is not ready

        # Aggregate stats
        total_words_all = sum(c['total_words'] for c in courses_data)
        total_learned_all = sum(c['words_learned'] for c in courses_data)
        total_sets_all = sum(c['total_sets'] for c in courses_data)
        total_completed_sets_all = sum(c['completed_sets'] for c in courses_data)
        overall_completion = round(total_learned_all / total_words_all * 100) if total_words_all > 0 else 0

        context.update({
            'levels': courses_data,
            'review_count': review_count,
            'streak': 0,
            'total_words_all': total_words_all,
            'total_learned_all': total_learned_all,
            'total_sets_all': total_sets_all,
            'total_completed_sets_all': total_completed_sets_all,
            'overall_completion': overall_completion,
        })
        return context


class MyWordsView(LoginRequiredMixin, ListView):
    template_name = 'vocab/my_words.html'
    context_object_name = 'cards'
    paginate_by = 30

    def get_queryset(self):
        qs = FsrsCardStateEn.objects.filter(user=self.request.user).select_related('vocab')
        
        filter_type = self.request.GET.get('filter')
        
        if filter_type == 'mastered':
            # Matches logic in core/views.py for "mastered"
            return qs.filter(total_reviews__gte=3, successful_reviews__gte=2).order_by('due')
        elif filter_type == 'learning':
            # Matches logic in core/views.py for "learning" (Total - Mastered)
            return qs.exclude(total_reviews__gte=3, successful_reviews__gte=2).order_by('due')
        elif filter_type == 'all':
            # Show all words
            return qs.order_by('due')
        
        # Default: Filter cards for this user that are not "New" (state > 0)
        return qs.filter(state__gt=0).order_by('due')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add basic count stats
        qs = self.get_queryset()
        context['total_learning'] = qs.count()
        # Mastered should strictly be Review (2). Relearning (3) is NOT mastered.
        context['mastered_count'] = qs.filter(state=2).count()
        
        # Ready count for FSRS review (cards due for review)
        from django.utils import timezone
        all_cards = FsrsCardStateEn.objects.filter(user=self.request.user)
        context['ready_count'] = all_cards.filter(due__lte=timezone.now()).count()
        
        # Learning sets (in progress)
        learning_sets = list(UserSetProgress.objects.filter(
            user=self.request.user,
            status='in_progress'
        ).select_related('vocabulary_set').order_by('-started_at')[:5])
        
        # Attach course slugs by level or language
        courses = Course.objects.all()
        level_slug_map = {c.toeic_level: c.slug for c in courses if c.toeic_level is not None}
        lang_slug_map = {c.language: c.slug for c in courses if c.toeic_level is None}

        for progress in learning_sets:
            lvl = progress.vocabulary_set.toeic_level
            if lvl is not None:
                progress.course_slug = level_slug_map.get(lvl, 'toeic-600-essential')
            else:
                progress.course_slug = lang_slug_map.get(progress.vocabulary_set.language, 'mimikara-n2')

        context['learning_sets'] = learning_sets
        
        return context

class CourseDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/toeic/level_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        user = self.request.user

        course = get_object_or_404(Course, slug=slug)
        level = course.toeic_level
        is_toeic = level is not None

        # Config dict for template compatibility
        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level,
            'language': course.language,
        }

        if is_toeic:
            sets = VocabularySet.objects.filter(
                toeic_level=level, status='published'
            ).order_by('chapter', 'set_number')
        else:
            sets = VocabularySet.objects.filter(
                language=course.language, toeic_level__isnull=True, status='published'
            ).order_by('chapter', 'set_number')

        # Group by chapter -> sets
        chapters = {}
        for s in sets:
            chapter_num = s.chapter or 1
            chapter_name = s.chapter_name or f"Chapter {chapter_num}"

            if chapter_num not in chapters:
                chapters[chapter_num] = {
                    'number': chapter_num,
                    'name': chapter_name,
                    'sets': [],
                    'words_total': 0,
                    'words_learned': 0,
                }

            if is_toeic:
                state = toeic_utils.get_set_state(user, level, s.set_number)
            else:
                # Compute state directly from UserSetProgress
                prog = UserSetProgress.objects.filter(user=user, vocabulary_set=s).first()
                if not prog or prog.status == UserSetProgress.ProgressStatus.NOT_STARTED:
                    state = 'available'
                elif prog.status == UserSetProgress.ProgressStatus.IN_PROGRESS:
                    state = 'in_progress'
                else:
                    state = 'completed'

            progress = UserSetProgress.objects.filter(user=user, vocabulary_set=s).first()
            words_total = s.items.count()
            words_learned = progress.words_learned if progress else 0

            set_data = {
                'set': s,
                'state': state,
                'words_learned': words_learned,
                'words_total': words_total,
                'quiz_score': progress.quiz_best_score if progress else 0,
            }

            chapters[chapter_num]['sets'].append(set_data)
            chapters[chapter_num]['words_total'] += words_total
            chapters[chapter_num]['words_learned'] += words_learned

        # Convert to sorted list
        chapters_list = sorted(chapters.values(), key=lambda x: x['number'])
        for ch in chapters_list:
            ch['completion'] = round((ch['words_learned'] / ch['words_total'] * 100) if ch['words_total'] > 0 else 0)

        total_words = sum(ch['words_total'] for ch in chapters_list)

        if is_toeic:
            learned_words = toeic_utils.get_level_words_learned_count(user, level)
            completion = toeic_utils.get_level_completion_percent(user, level)
            review_count = toeic_utils.get_level_review_count(user, level)
        else:
            set_ids = [s.id for s in sets]
            jp_vocab_ids = SetItem.objects.filter(
                vocabulary_set_id__in=set_ids
            ).values_list('definition__entry__vocab_id', flat=True)
            learned_words = FsrsCardStateEn.objects.filter(
                user=user, vocab_id__in=jp_vocab_ids, state__gte=2
            ).count()
            completion = round(learned_words / total_words * 100) if total_words > 0 else 0
            review_count = FsrsCardStateEn.objects.filter(
                user=user, vocab_id__in=jp_vocab_ids, due__lte=timezone.now()
            ).count()

        # Aggregate set stats
        all_sets_flat = [sd for ch in chapters_list for sd in ch['sets']]
        total_sets = len(all_sets_flat)
        completed_sets = sum(1 for sd in all_sets_flat if sd['state'] == 'completed')
        in_progress_sets = sum(1 for sd in all_sets_flat if sd['state'] == 'in_progress')

        context.update({
            'course': course,
            'level': level,
            'config': config,
            'chapters': chapters_list,
            'total_words': total_words,
            'learned_words': learned_words,
            'completion': completion,
            'review_count': review_count,
            'total_sets': total_sets,
            'completed_sets': completed_sets,
            'in_progress_sets': in_progress_sets,
        })
        return context



class CourseSetDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/toeic/set_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        set_number = self.kwargs['set_number']
        user = self.request.user

        course = get_object_or_404(Course, slug=slug)
        level = course.toeic_level

        if level is not None:
            vocab_set = get_object_or_404(
                VocabularySet, toeic_level=level, set_number=set_number, status='published'
            )
        else:
            vocab_set = get_object_or_404(
                VocabularySet, language=course.language, toeic_level__isnull=True,
                set_number=set_number, status='published'
            )
        
        is_jp = course.language == 'jp'

        # Get items with related data
        items = vocab_set.items.select_related(
            'definition__entry__vocab'
        ).prefetch_related('definition__examples', 'set_examples__example').order_by('display_order', 'created_at')

        # Get user progress for each item
        from .models import FsrsCardStateEn

        vocab_status_map = {}
        if user.is_authenticated:
            vocab_ids = [item.definition.entry.vocab_id for item in items]

            states = FsrsCardStateEn.objects.filter(
                user=user,
                vocab_id__in=vocab_ids
            ).values('vocab_id', 'state')

            for s in states:
                st = s['state']
                if st >= 2:
                    status = 'known'
                elif st == 1:
                    status = 'learning'
                else:
                    status = 'new'
                vocab_status_map[s['vocab_id']] = status

        items_data = []
        voice_pref = 'us'

        for item in items:
            d = item.definition
            e = d.entry
            v = e.vocab
            status = vocab_status_map.get(v.id, 'new')

            item_dict = {
                'word': v.word,
                'ipa': e.ipa,
                'meaning': d.meaning,
                'audio_url': e.get_audio_url(voice_pref),
                'status': status,
                'part_of_speech': e.part_of_speech,
            }

            if is_jp:
                extra = v.extra_data or {}
                item_dict.update({
                    'reading': extra.get('reading', ''),
                    'html_display': extra.get('html_display', ''),
                    'han_viet': extra.get('han_viet', ''),
                    'audio': extra.get('audio', ''),
                    'relations': (d.extra_data or {}).get('relations', []),
                    'examples': [
                        {'sentence': ex.sentence, 'translation': ex.translation}
                        for ex in d.examples.all()
                    ],
                })

            items_data.append(item_dict)
        
        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level,
            'language': course.language,
        }

        # Computed stats
        known_count = sum(1 for i in items_data if i['status'] == 'known')
        learning_count = sum(1 for i in items_data if i['status'] == 'learning')
        new_count = len(items_data) - known_count - learning_count
        total_count = len(items_data)
        progress_pct = round(known_count / total_count * 100) if total_count > 0 else 0

        # User progress record
        user_progress = UserSetProgress.objects.filter(
            user=user, vocabulary_set=vocab_set
        ).first()
        quiz_best = user_progress.quiz_best_score if user_progress else 0
        set_status = user_progress.status if user_progress else 'not_started'

        # Navigation: prev/next sets within the same course
        if level is not None:
            level_sets = VocabularySet.objects.filter(
                toeic_level=level, status='published'
            ).order_by('set_number').values_list('set_number', flat=True)
        else:
            level_sets = VocabularySet.objects.filter(
                language=course.language, toeic_level__isnull=True, status='published'
            ).order_by('set_number').values_list('set_number', flat=True)
        set_numbers = list(level_sets)
        current_idx = set_numbers.index(set_number) if set_number in set_numbers else -1
        prev_set = set_numbers[current_idx - 1] if current_idx > 0 else None
        next_set = set_numbers[current_idx + 1] if current_idx < len(set_numbers) - 1 else None

        context.update({
            'course': course,
            'level': level,
            'set_number': set_number,
            'config': config,
            'vocab_set': vocab_set,
            'items': items_data,
            'is_jp': is_jp,
            'known_count': known_count,
            'new_count': new_count,
            'total_count': total_count,
            'progress_pct': progress_pct,
            'quiz_best': quiz_best,
            'set_status': set_status,
            'prev_set': prev_set,
            'next_set': next_set,
        })
        return context

class CourseLearnView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/toeic/learn.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        set_number = self.kwargs['set_number']
        user = self.request.user

        course = get_object_or_404(Course, slug=slug)
        level = course.toeic_level

        if level is not None and not toeic_utils.is_set_accessible(user, level, set_number):
            raise Http404("Set is locked")

        if level is not None:
            vocab_set = get_object_or_404(
                VocabularySet, toeic_level=level, set_number=set_number, status='published'
            )
        else:
            vocab_set = get_object_or_404(
                VocabularySet, language=course.language, toeic_level__isnull=True,
                set_number=set_number, status='published'
            )
        items = vocab_set.items.select_related(
            'definition__entry__vocab'
        ).prefetch_related('definition__examples').order_by('display_order', 'created_at')

        # Get user's voice preference
        voice_pref = 'us'
        try:
            from .models import UserStudySettings
            settings_obj = UserStudySettings.objects.filter(user=user).first()
            if settings_obj:
                voice_pref = settings_obj.english_voice_preference
        except Exception:
            pass

        # Pre-load FSRS state for resume logic
        all_vocab_ids = [item.definition.entry.vocab_id for item in items]
        studied_states = {}
        if user.is_authenticated:
            studied_states = dict(
                FsrsCardStateEn.objects.filter(
                    user=user, vocab_id__in=all_vocab_ids
                ).values_list('vocab_id', 'state')
            )

        items_data = []
        is_jp = course.language == Vocabulary.Language.JAPANESE
        for item in items:
            d = item.definition
            e = d.entry
            v = e.vocab
            fsrs_state = studied_states.get(v.id, 0)
            row = {
                'id': v.id,
                'definition_id': d.id,
                'word': v.word,
                'ipa': e.ipa,
                'audio_url': e.get_audio_url(voice_pref),
                'meaning': d.meaning,
                'part_of_speech': e.part_of_speech,
                'example': d.example_sentence,
                'example_trans': d.example_trans,
                'studied': fsrs_state > 0,
                'prev_result': 'known' if fsrs_state >= 2 else ('unknown' if fsrs_state == 1 else None),
            }
            if is_jp:
                ed = v.extra_data or {}
                row['reading'] = ed.get('reading', '')
                row['han_viet'] = ed.get('han_viet', '')
                row['html_display'] = ed.get('html_display', '')
                # Collect all examples (sentence type) with HTML
                examples_list = []
                for ex in d.examples.all():
                    examples_list.append({
                        'sentence': ex.sentence,
                        'translation': ex.translation,
                    })
                row['examples'] = examples_list
                # Collect relations from definition extra_data
                row['relations'] = (d.extra_data or {}).get('relations', [])
            items_data.append(row)
            
        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level,
            'language': course.language,
        }

        context.update({
            'course': course,
            'level': level,
            'set_number': set_number,
            'config': config,
            'vocab_set': vocab_set,
            'items_json': json.dumps(items_data),
            'items_count': len(items_data),
        })
        return context


class CourseQuizView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/toeic/quiz.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        course = get_object_or_404(Course, slug=slug)
        level = course.toeic_level
        set_number = self.kwargs['set_number']
        user = self.request.user

        if level is not None and not toeic_utils.is_set_accessible(user, level, set_number):
            raise Http404("Set is locked")

        if level is not None:
            vocab_set = get_object_or_404(
                VocabularySet, toeic_level=level, set_number=set_number, status='published'
            )
        else:
            vocab_set = get_object_or_404(
                VocabularySet, language=course.language, toeic_level__isnull=True,
                set_number=set_number, status='published'
            )

        items = vocab_set.items.select_related(
            'definition__entry__vocab'
        ).order_by('display_order', 'created_at')

        # Get all meanings from same course for distractors
        if level is not None:
            distractor_filter = {'included_in_sets__vocabulary_set__toeic_level': level}
        else:
            distractor_filter = {
                'included_in_sets__vocabulary_set__language': course.language,
                'included_in_sets__vocabulary_set__toeic_level__isnull': True,
            }
        level_definitions = list(
            WordDefinition.objects.filter(
                included_in_sets__vocabulary_set__status='published',
                **distractor_filter,
            ).exclude(
                id__in=[item.definition_id for item in items]
            ).values_list('meaning', flat=True).distinct()
        )

        questions = []
        for item in items:
            d = item.definition
            e = d.entry
            v = e.vocab

            # Build 3 distractors
            distractors = random.sample(level_definitions, min(3, len(level_definitions)))
            choices = [d.meaning] + distractors
            random.shuffle(choices)

            q = {
                'vocab_id': v.id,
                'word': v.word,
                'ipa': e.ipa,
                'audio_url': e.get_audio_url('us'),
                'correct': d.meaning,
                'choices': choices,
            }
            if course.language == Vocabulary.Language.JAPANESE:
                ed = v.extra_data or {}
                q['html_display'] = ed.get('html_display', '')
            questions.append(q)

        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level,
            'language': course.language,
        }

        context.update({
            'course': course,
            'level': level,
            'set_number': set_number,
            'config': config,
            'vocab_set': vocab_set,
            'questions_json': json.dumps(questions),
            'total_questions': len(questions),
        })
        return context


class ToeicReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/toeic/review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        # Get all TOEIC vocab IDs
        toeic_vocab_ids = SetItem.objects.filter(
            vocabulary_set__toeic_level__isnull=False,
            vocabulary_set__status='published',
        ).values_list(
            'definition__entry__vocab_id', flat=True
        ).distinct()

        # Get due FSRS cards
        due_cards = FsrsCardStateEn.objects.filter(
            user=user,
            vocab_id__in=toeic_vocab_ids,
            due__lte=now,
        ).select_related('vocab')[:50]

        # Prefetch entries, definitions, and examples for all due vocabs
        from django.db.models import Prefetch
        vocab_ids = [cs.vocab_id for cs in due_cards]
        vocab_map = {}
        if vocab_ids:
            vocabs_qs = Vocabulary.objects.filter(id__in=vocab_ids).prefetch_related(
                Prefetch('entries', queryset=WordEntry.objects.all()),
                Prefetch('entries__definitions', queryset=WordDefinition.objects.prefetch_related('examples')),
            )
            vocab_map = {v.id: v for v in vocabs_qs}

        cards_data = []
        for card_state in due_cards:
            vocab = vocab_map.get(card_state.vocab_id) or card_state.vocab
            # Get first entry + definition for display
            entries = list(vocab.entries.all())
            entry = entries[0] if entries else None
            if not entry:
                continue
            definitions = list(entry.definitions.all())
            definition = definitions[0] if definitions else None
            if not definition:
                continue

            intervals = preview_intervals(card_state.card_data)
            cards_data.append({
                'vocab_id': vocab.id,
                'word': vocab.word,
                'ipa': entry.ipa,
                'audio_url': entry.get_audio_url('us'),
                'meaning': definition.meaning,
                'part_of_speech': entry.part_of_speech,
                'example': definition.example_sentence,
                'example_trans': definition.example_trans,
                'intervals': intervals,
            })

        context.update({
            'cards_json': json.dumps(cards_data),
            'cards_count': len(cards_data),
        })
        return context


# ======================================
# TOEIC API Views
# ======================================

@require_POST
@login_required
@rate_limit('learn', max_calls=30, period=60)
def api_toeic_learn_result(request):
    """POST: receives set_id, known_ids[], unknown_ids[]. Creates/updates FSRS cards and progress."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    set_id = data.get('set_id')
    known_ids = data.get('known_ids', [])
    unknown_ids = data.get('unknown_ids', [])
    user = request.user

    vocab_set = get_object_or_404(VocabularySet, id=set_id)

    # --- FIX #2: Validate vocab_ids belong to this set ---
    valid_vocab_ids = set(
        vocab_set.items.values_list('definition__entry__vocab_id', flat=True)
    )
    known_ids = [vid for vid in known_ids if vid in valid_vocab_ids]
    unknown_ids = [vid for vid in unknown_ids if vid in valid_vocab_ids]

    known_id_set = set(known_ids)
    all_ids = known_ids + unknown_ids

    # --- FIX #5: Wrap all writes in a transaction ---
    with transaction.atomic():
        for vocab_id in all_ids:
            card_state, created = FsrsCardStateEn.objects.get_or_create(
                user=user, vocab_id=vocab_id,
                # FIX #6: card_data_to_dict ensures dict, not JSON string
                defaults={'card_data': card_data_to_dict(create_new_card_state())}
            )
            if created or card_state.state == 0:  # New card
                rating = 'easy' if vocab_id in known_id_set else 'again'
                # review_card now returns dict (not string) — FIX #6
                new_card_data, _, due_dt = review_card(card_state.card_data, rating)
                card_state.card_data = new_card_data
                card_state.due = due_dt
                card_state.state = new_card_data.get('state', 0)
                card_state.last_review = timezone.now()
                card_state.total_reviews = F('total_reviews') + 1
                if vocab_id in known_id_set:
                    card_state.successful_reviews = F('successful_reviews') + 1
                card_state.save()

        # Update UserSetProgress by counting ACTUAL learned cards in DB
        # state >= 2 = graduated (known). state 1 = Learning (marked unknown).
        learned_count = FsrsCardStateEn.objects.filter(
            user=user,
            vocab_id__in=valid_vocab_ids,
            state__gte=2
        ).count()

        total_items = vocab_set.items.count()
        progress, _ = UserSetProgress.objects.get_or_create(
            user=user, vocabulary_set=vocab_set,
            defaults={'words_total': total_items}
        )
        progress.words_learned = learned_count
        progress.words_total = total_items

        if not progress.started_at:
            progress.started_at = timezone.now()

        mastered_count = FsrsCardStateEn.objects.filter(
            user=user,
            vocab_id__in=valid_vocab_ids,
            state=2  # Strictly Review
        ).count()

        if mastered_count >= total_items and total_items > 0:
            progress.status = UserSetProgress.ProgressStatus.COMPLETED
            if not progress.completed_at:
                progress.completed_at = timezone.now()
        else:
            progress.status = UserSetProgress.ProgressStatus.IN_PROGRESS
            progress.completed_at = None

        progress.save()

    # Check for badges (outside transaction — OK if badge insert fails independently)
    from core.badge_service import check_and_award_badges
    new_badges = check_and_award_badges(request.user)

    badges_data = [
        {"name": gb.name, "description": gb.description, "icon": gb.icon}
        for gb in new_badges
    ]

    # Determine redirect
    level = vocab_set.toeic_level
    set_number = vocab_set.set_number

    if level is not None:
        try:
            course_slug = Course.objects.get(toeic_level=level).slug
        except Course.DoesNotExist:
            course_slug = f"toeic-{level}"
    else:
        # Non-TOEIC set - find course by language
        try:
            course_slug = Course.objects.get(language=vocab_set.language, toeic_level__isnull=True).slug
        except Course.DoesNotExist:
            course_slug = 'mimikara-n2'

    if progress.status == UserSetProgress.ProgressStatus.COMPLETED:
        next_url = reverse('vocab:course_detail', kwargs={'slug': course_slug})
    else:
        next_url = reverse('vocab:course_quiz', kwargs={'slug': course_slug, 'set_number': set_number})

    return JsonResponse({
        'success': True,
        'status': progress.status,
        'words_learned': progress.words_learned,
        'words_total': progress.words_total,
        'next_url': next_url,
        'quiz_url': reverse('vocab:course_quiz', kwargs={'slug': course_slug, 'set_number': set_number}),
        'level_url': reverse('vocab:course_detail', kwargs={'slug': course_slug}),
        'new_badges': badges_data,
    })


@require_POST
@login_required
@rate_limit('quiz', max_calls=30, period=60)
def api_toeic_quiz_result(request):
    """POST: receives set_id, score, total, wrong_word_ids[]."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    set_id = data.get('set_id')
    score = int(data.get('score', 0))
    total = int(data.get('total', 0))
    user = request.user

    vocab_set = get_object_or_404(VocabularySet, id=set_id)

    # --- FIX #1: Server-side score validation ---
    # Clamp score to [0, total] so client cannot fake arbitrary scores
    actual_total = vocab_set.items.count()
    total = min(total, actual_total)  # Cannot claim more questions than exist
    score = max(0, min(score, total))  # Score bounded by [0, total]

    with transaction.atomic():
        progress, _ = UserSetProgress.objects.get_or_create(
            user=user, vocabulary_set=vocab_set,
            defaults={'words_total': actual_total}
        )

        # Update best score (as percentage)
        score_pct = round(score / total * 100) if total > 0 else 0
        if score_pct > progress.quiz_best_score:
            progress.quiz_best_score = score_pct

        # FIX #1: Use percentage threshold, not absolute numbers
        if (total > 0 and score_pct >= 80
                and progress.status == UserSetProgress.ProgressStatus.IN_PROGRESS):
            progress.status = UserSetProgress.ProgressStatus.COMPLETED
            progress.completed_at = timezone.now()
            progress.words_learned = progress.words_total

        progress.save()

    # Check for badges
    from core.badge_service import check_and_award_badges
    new_badges = check_and_award_badges(request.user)

    badges_data = [
        {"name": gb.name, "description": gb.description, "icon": gb.icon}
        for gb in new_badges
    ]

    level = vocab_set.toeic_level
    set_number = vocab_set.set_number

    if level is not None:
        try:
            course_slug = Course.objects.get(toeic_level=level).slug
        except Course.DoesNotExist:
            course_slug = f"toeic-{level}"
    else:
        try:
            course_slug = Course.objects.get(language=vocab_set.language, toeic_level__isnull=True).slug
        except Course.DoesNotExist:
            course_slug = 'mimikara-n2'

    return JsonResponse({
        'success': True,
        'status': progress.status,
        'score': score,
        'total': total,
        'score_pct': score_pct,
        'best_score': progress.quiz_best_score,
        'next_url': reverse('vocab:course_detail', kwargs={'slug': course_slug}),
        'retry_url': reverse('vocab:course_quiz', kwargs={'slug': course_slug, 'set_number': set_number}),
        'learn_url': reverse('vocab:course_learn', kwargs={'slug': course_slug, 'set_number': set_number}),
        'new_badges': badges_data,
    })


@require_POST
@login_required
@rate_limit('grade', max_calls=120, period=60)
def api_toeic_review_grade(request):
    """POST: receives vocab_id, rating (again/hard/good/easy). Calls FSRS review via FsrsService."""
    from vocab.services import FsrsService
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    vocab_id = data.get('vocab_id')
    rating = data.get('rating', 'good')
    
    if not vocab_id:
        return JsonResponse({'error': 'vocab_id required'}, status=400)

    result = FsrsService.grade_card(
        user=request.user,
        vocab_id=vocab_id,
        rating=rating,
        create_if_missing=True
    )
    
    if not result.get('success'):
        return JsonResponse({'error': result.get('error', 'Unknown error')}, status=400)

    return JsonResponse(result)


@require_POST
@login_required
@rate_limit('grade', max_calls=120, period=60)
def api_flashcard_grade_english(request):
    """
    POST: Grade an English flashcard.

    Accepts form data or JSON:
    - state_id: ID of FsrsCardStateEn (optional, for existing cards)
    - vocab_id: ID of Vocabulary (alternative to state_id)
    - rating: 'again', 'hard', 'good', 'easy'
    - is_new: 'true'/'false' (optional hint)

    Returns JSON with success, intervals, requeue, requeue_delay_ms
    """
    from vocab.services import FsrsService
    
    # Parse request data (support both form and JSON)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        vocab_id = data.get('vocab_id')
        state_id = data.get('state_id')
        rating = data.get('rating', 'good')
    else:
        vocab_id = request.POST.get('vocab_id')
        state_id = request.POST.get('state_id')
        rating = request.POST.get('rating', 'good')
    
    # Get vocab_id from state_id if not provided
    if not vocab_id and state_id:
        try:
            card_state = FsrsCardStateEn.objects.get(id=state_id, user=request.user)
            vocab_id = card_state.vocab_id
        except FsrsCardStateEn.DoesNotExist:
            return JsonResponse({'error': 'Card state not found'}, status=404)
    
    if not vocab_id:
        return JsonResponse({'error': 'vocab_id or state_id required'}, status=400)

    try:
        vocab_id = int(vocab_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid vocab_id'}, status=400)

    result = FsrsService.grade_card(
        user=request.user,
        vocab_id=vocab_id,
        rating=rating,
        create_if_missing=True
    )

    if not result.get('success'):
        return JsonResponse({'error': result.get('error', 'Unknown error')}, status=400)

    return JsonResponse(result)


# ==========================
# GAME VIEWS (Placeholders)
# ==========================

class GameMCQView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/games/mcq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Fetch random definitions
        # Optimization: Use samples if table is large. For now, random order is fine for small db.
        definitions = list(WordDefinition.objects.select_related('entry__vocab').all().values(
            'meaning', 'entry__vocab__word'
        ))
        
        # If not enough data
        if len(definitions) < 4:
            context['questions'] = []
            context['questions_json'] = '[]'
            context['total_count'] = 0
            return context

        # Pick 10 random questions
        random.shuffle(definitions)
        selection = definitions[:10]
        
        questions = []
        all_words = list(set(d['entry__vocab__word'] for d in definitions))

        for item in selection:
            correct_word = item['entry__vocab__word']
            meaning = item['meaning']
            
            # Pick 3 distractors
            distractors = [w for w in all_words if w != correct_word]
            if len(distractors) < 3:
                opts = distractors
            else:
                opts = random.sample(distractors, 3)
            
            options = opts + [correct_word]
            random.shuffle(options)
            
            questions.append({
                'question': meaning,
                'answer': correct_word,
                'options': options,
                'hint': None # Could add hints later
            })
            
        context['questions'] = questions
        context['questions_json'] = json.dumps(questions)
        context['total_count'] = len(questions)
        return context

class GameMatchingView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/games/matching.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 2. Fetch random pairs
        definitions = list(WordDefinition.objects.select_related('entry__vocab').all().values(
            'meaning', 'entry__vocab__word'
        ))
        
        if len(definitions) < 4:
             context['tiles'] = []
             context['tiles_json'] = '[]'
             context['total_pairs'] = 0
             return context
             
        random.shuffle(definitions)
        selection = definitions[:6] # 6 pairs = 12 tiles
        
        tiles = []
        for i, item in enumerate(selection):
            # Word tile
            tiles.append({
                'id': f"w-{i}",
                'text': item['entry__vocab__word'],
                'type': 'word',
                'pair_id': i
            })
            # Meaning tile
            tiles.append({
                'id': f"m-{i}",
                'text': item['meaning'],
                'type': 'meaning',
                'pair_id': i
            })
            
        random.shuffle(tiles)
        
        context['tiles'] = tiles
        context['tiles_json'] = json.dumps(tiles)
        context['total_pairs'] = len(selection)
        return context

class GameListeningView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/games/listening.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 3. Fetch entries with audio
        # Optimally we filter for entries that have either audio_us or audio_uk
        entries = list(WordEntry.objects.filter(
            Q(audio_us__startswith='http') | Q(audio_uk__startswith='http')
        ).select_related('vocab').values(
            'vocab__word', 'audio_us', 'audio_uk'
        ))
        
        if len(entries) < 4:
            context['questions'] = []
            context['questions_json'] = '[]'
            context['total_count'] = 0
            return context
            
        random.shuffle(entries)
        selection = entries[:10]
        
        questions = []
        all_words = list(set(e['vocab__word'] for e in entries))
        
        for item in selection:
            correct_word = item['vocab__word']
            audio = item['audio_us'] if item['audio_us'] else item['audio_uk']
            
            # Distractors
            distractors = [w for w in all_words if w != correct_word]
            if len(distractors) < 3:
                opts = distractors
            else:
                opts = random.sample(distractors, 3)
            
            options = opts + [correct_word]
            random.shuffle(options)
            
            questions.append({
                'audio': audio,
                'answer': correct_word,
                'options': options
            })
            
        context['questions'] = questions
        context['questions_json'] = json.dumps(questions)
        context['total_count'] = len(questions)
        return context

class GameFillView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/games/fill.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 4. Fetch random definitions for spelling
        definitions = list(WordDefinition.objects.select_related('entry__vocab').all().values(
            'meaning', 'entry__vocab__word'
        ))
        
        if not definitions:
            context['questions'] = []
            context['questions_json'] = '[]'
            context['total_count'] = 0
            return context

        random.shuffle(definitions)
        selection = definitions[:10]
        
        questions = []
        for item in selection:
            questions.append({
                'question': item['meaning'],
                'answer': item['entry__vocab__word'].lower(),
                'display_answer': item['entry__vocab__word'],
                'hint': f"Từ có {len(item['entry__vocab__word'])} chữ cái"
            })
            
        context['questions'] = questions
        context['questions_json'] = json.dumps(questions)
        context['total_count'] = len(questions)
        return context

class GameDictationView(LoginRequiredMixin, TemplateView):
    template_name = 'vocab/games/dictation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 5. Fetch entries with audio for dictation (include meaning for richer feedback)
        entries = list(WordEntry.objects.filter(
            Q(audio_us__startswith='http') | Q(audio_uk__startswith='http')
        ).select_related('vocab').values(
            'vocab__word', 'audio_us', 'audio_uk', 'ipa'
        ))

        if not entries:
            context['questions'] = []
            context['questions_json'] = '[]'
            context['total_count'] = 0
            return context

        random.shuffle(entries)
        selection = entries[:10]

        # Fetch meanings for selected words
        word_list = [item['vocab__word'] for item in selection]
        meanings_map = {}
        defs = WordDefinition.objects.filter(
            entry__vocab__word__in=word_list
        ).select_related('entry__vocab').values('entry__vocab__word', 'meaning')
        for d in defs:
            if d['entry__vocab__word'] not in meanings_map:
                meanings_map[d['entry__vocab__word']] = d['meaning']

        questions = []
        for item in selection:
            audio = item['audio_us'] if item['audio_us'] else item['audio_uk']
            word = item['vocab__word']
            questions.append({
                'audio': audio,
                'answer': word.lower(),
                'display_answer': word,
                'phonetic': item.get('ipa', ''),
                'meaning': meanings_map.get(word, ''),
            })
            
        context['questions'] = questions
        context['questions_json'] = json.dumps(questions)
        context['total_count'] = len(questions)
        return context


# ==========================
# GAME UTILITY APIS
# ==========================

@login_required
@require_POST
def api_buy_game_life(request):
    """
    API để mua thêm mạng trong game.
    POST /api/games/buy-life/
    Cost: 10 coins
    """
    from wallet.services import CoinService
    from wallet.models import CoinTransaction
    from wallet.exceptions import InsufficientCoinsError
    
    LIFE_COST = 10
    
    try:
        result = CoinService.execute_transaction(
            user=request.user,
            amount=-LIFE_COST,
            transaction_type=CoinTransaction.TransactionType.PURCHASE,
            description="Mua thêm mạng trong game"
        )
        return JsonResponse({
            'success': True,
            'new_balance': result['new_balance'],
            'message': 'Đã mua thêm 1 mạng!'
        })
    except InsufficientCoinsError as e:
        return JsonResponse({
            'success': False,
            'error': 'insufficient_coins',
            'message': f'Không đủ coin. Bạn cần {LIFE_COST} coin.',
            'current_balance': e.current_balance
        }, status=400)