from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Case, When, Value, IntegerField, F
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
import json
import random
from .models import VocabularySet, SetItem, WordDefinition, WordEntry, Vocabulary, FsrsCardStateEn, UserSetProgress, Course
from .toeic_config import TOEIC_LEVELS, TOEIC_LEVEL_ORDER
from . import toeic_utils
from .fsrs_bridge import create_new_card_state, review_card, preview_intervals

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
        items = self.object.items.select_related('definition__entry__vocab').order_by('display_order', 'created_at')
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
        items = self.object.items.select_related('definition__entry__vocab').order_by('display_order', 'created_at')
        
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
                    'example_sentence': word_data.get('example', ''),
                    'example_trans': word_data.get('example_trans', ''),
                    'extra_data': def_extra,
                }
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


class EnglishListView(LoginRequiredMixin, ListView):
    model = WordDefinition
    template_name = 'vocab/english_list.html'
    context_object_name = 'words'
    paginate_by = 50

    def get_queryset(self):
        # Base queryset: words with English vocabulary
        queryset = WordDefinition.objects.filter(entry__vocab__language=Vocabulary.Language.ENGLISH).select_related('entry__vocab')
        
        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(entry__vocab__word__icontains=query) | 
                Q(entry__ipa__icontains=query) | 
                Q(meaning__icontains=query)
            )
            
        return queryset.order_by('entry__vocab__word')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.get_queryset().count()
        q = self.request.GET.get('q', '')
        context['q'] = q
        context['base_qs'] = f'q={q}' if q else ''

        # Build page_items for pagination component
        page_obj = context.get('page_obj')
        if page_obj:
            num_pages = page_obj.paginator.num_pages
            current = page_obj.number
            page_items = []
            for p in range(1, num_pages + 1):
                if p == 1 or p == num_pages or abs(p - current) <= 2:
                    page_items.append(p)
                elif page_items and page_items[-1] is not None:
                    page_items.append(None)
            context['page_items'] = page_items

        return context

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
        context['entries'] = self.object.entries.prefetch_related('definitions').order_by('part_of_speech')
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
        
        # Get active courses
        courses = Course.objects.filter(is_active=True).order_by('toeic_level')
        
        # Calculate stats for each course
        courses_data = []
        for course in courses:
            level = course.toeic_level
            if not level: continue
            
            completion = toeic_utils.get_level_completion_percent(user, level)
            learned_count = toeic_utils.get_level_words_learned_count(user, level)
            
            # Count sets (published)
            total_sets = VocabularySet.objects.filter(toeic_level=level, status='published').count()
            
            # Count total words (published)
            total_words = SetItem.objects.filter(
                vocabulary_set__toeic_level=level, 
                vocabulary_set__status='published'
            ).count()

            completed_sets = UserSetProgress.objects.filter(
                user=user, 
                vocabulary_set__toeic_level=level, 
                status=UserSetProgress.ProgressStatus.COMPLETED
            ).count()

            courses_data.append({
                'object': course,
                'slug': course.slug, 
                'completion': completion,
                'words_learned': learned_count,
                'total_sets': total_sets,
                'total_words': total_words,
                'completed_sets': completed_sets,
                # For compatibility with template that expects 'config' dict
                'config': {
                    'label': course.title,
                    'description': course.description,
                    'icon': course.icon,
                    'gradient': course.gradient,
                    'level': level
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
        
        # Attach course slugs by level
        # This is a quick fix. Ideally VocabularySet should have a FK to Course.
        courses = Course.objects.all()
        level_slug_map = {c.toeic_level: c.slug for c in courses}
        
        for progress in learning_sets:
            lvl = progress.vocabulary_set.toeic_level
            # Default fallback if map missing (e.g. custom sets) -> assume 'toeic-600-essential' or just string
            progress.course_slug = level_slug_map.get(lvl, 'toeic-600-essential')

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
        
        if not level:
             raise Http404("Course has no associated TOEIC level")

        # Config dict for template compatibility
        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level
        }
        
        sets = VocabularySet.objects.filter(
            toeic_level=level, status='published'
        ).order_by('chapter', 'set_number')

        # Group by chapter -> sets (no milestones)
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
            
            state = toeic_utils.get_set_state(user, level, s.set_number)
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
        learned_words = toeic_utils.get_level_words_learned_count(user, level)
        completion = toeic_utils.get_level_completion_percent(user, level)

        # Aggregate set stats for the level
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
            'review_count': toeic_utils.get_level_review_count(user, level),
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

        vocab_set = get_object_or_404(
            VocabularySet, toeic_level=level, set_number=set_number, status='published'
        )
        
        # Get items
        items = vocab_set.items.select_related(
            'definition__entry__vocab'
        ).order_by('display_order', 'created_at')

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
                status = 'known' if s['state'] > 0 else 'new'
                vocab_status_map[s['vocab_id']] = status

        items_data = []
        voice_pref = 'us'
        
        for item in items:
            d = item.definition
            e = d.entry
            v = e.vocab
            status = vocab_status_map.get(v.id, 'new')
            
            items_data.append({
                'word': v.word,
                'ipa': e.ipa,
                'meaning': d.meaning,
                'audio_url': e.get_audio_url(voice_pref),
                'status': status,
                'part_of_speech': e.part_of_speech,
            })
        
        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level
        }

        context.update({
            'course': course,
            'level': level,
            'set_number': set_number,
            'config': config,
            'vocab_set': vocab_set,
            'items': items_data,
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

        if not toeic_utils.is_set_accessible(user, level, set_number):
            # For backward compatibility with utilization
            raise Http404("Set is locked")

        vocab_set = get_object_or_404(
            VocabularySet, toeic_level=level, set_number=set_number, status='published'
        )
        items = vocab_set.items.select_related(
            'definition__entry__vocab'
        ).order_by('display_order', 'created_at')

        # Get user's voice preference
        voice_pref = 'us'
        try:
            from .models import UserStudySettings
            settings_obj = UserStudySettings.objects.filter(user=user).first()
            if settings_obj:
                voice_pref = settings_obj.english_voice_preference
        except Exception:
            pass

        items_data = []
        for item in items:
            d = item.definition
            e = d.entry
            v = e.vocab
            items_data.append({
                'id': v.id,
                'definition_id': d.id,
                'word': v.word,
                'ipa': e.ipa,
                'audio_url': e.get_audio_url(voice_pref),
                'meaning': d.meaning,
                'part_of_speech': e.part_of_speech,
                'example': d.example_sentence,
                'example_trans': d.example_trans,
            })
            
        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level
        }

        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level
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

        if not toeic_utils.is_set_accessible(user, level, set_number):
            raise Http404("Set is locked")

        vocab_set = get_object_or_404(
            VocabularySet, toeic_level=level, set_number=set_number, status='published'
        )
        items = vocab_set.items.select_related(
            'definition__entry__vocab'
        ).order_by('display_order', 'created_at')

        # Get all meanings from same level for distractors
        level_definitions = list(
            WordDefinition.objects.filter(
                included_in_sets__vocabulary_set__toeic_level=level,
                included_in_sets__vocabulary_set__status='published',
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

            questions.append({
                'vocab_id': v.id,
                'word': v.word,
                'ipa': e.ipa,
                'audio_url': e.get_audio_url('us'),
                'correct': d.meaning,
                'choices': choices,
            })

        config = {
            'label': course.title,
            'description': course.description,
            'icon': course.icon,
            'gradient': course.gradient,
            'level': level
        }

        context.update({
            'course': course, # Make sure course is passed
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

        cards_data = []
        for card_state in due_cards:
            vocab = card_state.vocab
            # Get first entry + definition for display
            entry = vocab.entries.first()
            if not entry:
                continue
            definition = entry.definitions.first()
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

    # Create/update FSRS cards for each word
    all_ids = known_ids + unknown_ids
    for vocab_id in all_ids:
        card_state, created = FsrsCardStateEn.objects.get_or_create(
            user=user, vocab_id=vocab_id,
            defaults={'card_data': create_new_card_state().to_json()}
        )
        if created or card_state.state == 0:  # New card
            rating = 'easy' if vocab_id in known_ids else 'again'
            new_card_json, _, due_dt = review_card(card_state.card_data, rating)
            if isinstance(new_card_json, str):
                import json as _json
                new_card_json = _json.loads(new_card_json)
            card_state.card_data = new_card_json
            card_state.due = due_dt
            card_state.state = new_card_json.get('state', 0)
            card_state.last_review = timezone.now()
            card_state.total_reviews += 1
            if vocab_id in known_ids:
                card_state.successful_reviews += 1
            card_state.save()

    # Update UserSetProgress by counting ACTUAL learned cards in DB
    # This prevents overwrite issues with partial/incremental updates
    vocab_ids_in_set = vocab_set.items.values_list('definition__entry__vocab_id', flat=True)
    learned_count = FsrsCardStateEn.objects.filter(
        user=user,
        vocab_id__in=vocab_ids_in_set,
        state__gt=0  # 0=New, >0 = Learned/Learning
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

    # Count mastered cards (State = 2, Review). 
    # State 1 (Learning) and 3 (Relearning) do not count as Mastered for set completion.
    mastered_count = FsrsCardStateEn.objects.filter(
        user=user,
        vocab_id__in=vocab_ids_in_set,
        state=2  # Strictly Review
    ).count()

    # NOTE: Relearning (3) implies they forgot. We treat only Review (2) as "Mastered/Completed".
    # Or should Relearning count? Usually Relearning means "learning again". 
    # For a stricter "Completed" status, we require Review state.
    
    if mastered_count >= total_items and total_items > 0:
        progress.status = UserSetProgress.ProgressStatus.COMPLETED
        if not progress.completed_at:
            progress.completed_at = timezone.now()
    else:
        progress.status = UserSetProgress.ProgressStatus.IN_PROGRESS
        progress.completed_at = None

    progress.save()

    # Check for badges
    from core.badge_service import check_and_award_badges
    new_badges = check_and_award_badges(request.user)
    
    badges_data = []
    for gb in new_badges:
        badges_data.append({
            "name": gb.name,
            "description": gb.description,
            "icon": gb.icon
        })

    # Determine redirect
    level = vocab_set.toeic_level
    set_number = vocab_set.set_number
    
    # Lookup proper slug
    try:
        course_slug = Course.objects.get(toeic_level=level).slug
    except Course.DoesNotExist:
        # Fallback or error, but let's assume it exists as migrated
        course_slug = f"toeic-{level}" 

    if progress.status == UserSetProgress.ProgressStatus.COMPLETED:
        # If completed, maybe go back to detail? Or maybe next set?
        # For now, back to detail
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
def api_toeic_quiz_result(request):
    """POST: receives set_id, score, total, wrong_word_ids[]."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    set_id = data.get('set_id')
    score = data.get('score', 0)
    total = data.get('total', 0)
    user = request.user

    vocab_set = get_object_or_404(VocabularySet, id=set_id)

    progress, _ = UserSetProgress.objects.get_or_create(
        user=user, vocabulary_set=vocab_set,
        defaults={'words_total': vocab_set.items.count()}
    )

    # Update best score (as percentage)
    score_pct = round(score / total * 100) if total > 0 else 0
    if score_pct > progress.quiz_best_score:
        progress.quiz_best_score = score_pct

    # If scored >= 80% and was in_progress, mark completed
    if score >= 8 and total >= 10 and progress.status == UserSetProgress.ProgressStatus.IN_PROGRESS:
        progress.status = UserSetProgress.ProgressStatus.COMPLETED
        progress.completed_at = timezone.now()
        progress.words_learned = progress.words_total

    progress.save()
    
    # Check for badges
    from core.badge_service import check_and_award_badges
    new_badges = check_and_award_badges(request.user)
    
    badges_data = []
    for gb in new_badges:
        badges_data.append({
            "name": gb.name,
            "description": gb.description,
            "icon": gb.icon
        })

    level = vocab_set.toeic_level
    set_number = vocab_set.set_number
    
    # Lookup proper slug
    try:
        course_slug = Course.objects.get(toeic_level=level).slug
    except Course.DoesNotExist:
        course_slug = f"toeic-{level}"

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
    
    result = FsrsService.grade_card(
        user=request.user,
        vocab_id=int(vocab_id),
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
                'answer': item['entry__vocab__word'],
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
        
        # 5. Fetch entries with audio for dictation
        entries = list(WordEntry.objects.filter(
            Q(audio_us__startswith='http') | Q(audio_uk__startswith='http')
        ).select_related('vocab').values(
            'vocab__word', 'audio_us', 'audio_uk'
        ))
        
        if not entries:
            context['questions'] = []
            context['questions_json'] = '[]'
            context['total_count'] = 0
            return context
            
        random.shuffle(entries)
        selection = entries[:10]
        
        questions = []
        for item in selection:
            audio = item['audio_us'] if item['audio_us'] else item['audio_uk']
            questions.append({
                'audio': audio,
                'answer': item['vocab__word']
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