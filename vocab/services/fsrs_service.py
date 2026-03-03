"""
FSRS Service Layer (Single Responsibility Principle)

Provides unified FSRS operations for all vocabulary learning features:
- English Flashcards
- TOEIC Review
- Any future SRS-based features

This service encapsulates all FSRS-related logic, ensuring:
- Consistent card state management
- Proper upsert behavior for new cards
- Unified grading logic with requeue support
"""

import json
import random
from datetime import timedelta
from typing import Optional, Dict, Any, List, Tuple

from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q, F, Count, Exists, OuterRef

from vocab.models import (
    Vocabulary, FsrsCardStateEn, WordDefinition,
    UserStudySettings, UserSetProgress, SetItem,
)
from vocab.fsrs_bridge import (
    review_card,
    preview_intervals,
    create_new_card_state,
    card_data_to_dict,
    should_requeue_in_session,
    get_card_state,
    CARD_STATE_NEW,
    CARD_STATE_LEARNING,
    CARD_STATE_REVIEW,
    CARD_STATE_RELEARNING,
)


class FsrsService:
    """
    Service class for FSRS operations.
    
    Follows Single Responsibility Principle:
    - Only handles FSRS card state operations
    - Does not handle HTTP request/response formatting
    """
    
    # Default limits
    DEFAULT_NEW_LIMIT = 20
    DEFAULT_REVIEW_LIMIT = 100
    
    @staticmethod
    def get_or_create_card_state(user, vocab: Vocabulary) -> Tuple[FsrsCardStateEn, bool]:
        """
        Get existing card state or create a new one.

        Returns:
            Tuple of (card_state, created)
        """
        card_state, created = FsrsCardStateEn.objects.get_or_create(
            user=user,
            vocab=vocab,
            defaults={
                'card_data': card_data_to_dict(create_new_card_state()),
                'state': CARD_STATE_NEW,
                'due': timezone.now(),
            }
        )
        return card_state, created
    
    @staticmethod
    def get_due_cards(user, limit: int = None, language: str = None) -> models.QuerySet:
        """
        Get cards that are due for review (New + Learning + Review + Relearning).
        
        Args:
            user: The user
            limit: Maximum number of cards to return
            language: Optional language filter ('en', 'jp')
            
        Returns:
            QuerySet of FsrsCardStateEn ordered by due date
        """
        limit = limit or FsrsService.DEFAULT_REVIEW_LIMIT
        now = timezone.now()
        
        qs = FsrsCardStateEn.objects.filter(
            user=user,
            due__lte=now,
            state__in=[CARD_STATE_NEW, CARD_STATE_LEARNING, CARD_STATE_REVIEW, CARD_STATE_RELEARNING]
        ).select_related('vocab')
        if language:
            qs = qs.filter(vocab__language=language)
        return qs.order_by('due')[:limit]
    
    @staticmethod
    def get_learning_cards(user) -> models.QuerySet:
        """
        Get cards currently in Learning or Relearning state.
        These should be shown again within the same session.
        """
        return FsrsCardStateEn.objects.filter(
            user=user,
            state__in=[CARD_STATE_LEARNING, CARD_STATE_RELEARNING]
        ).select_related('vocab')
    
    @staticmethod
    def get_new_vocabs(user, language: str = 'english', limit: int = None) -> models.QuerySet:
        """
        Get vocabulary items that the user has never studied (no FsrsCardStateEn).
        Prioritizes words from user's in-progress sets before falling back to random.
        
        Args:
            user: The user
            language: 'english' or other language code
            limit: Maximum number to return
            
        Returns:
            QuerySet of Vocabulary items
        """
        limit = limit or FsrsService.DEFAULT_NEW_LIMIT
        
        # Check daily limit
        settings, _ = UserStudySettings.objects.get_or_create(user=user)
        settings.reset_daily_counts_if_needed()
        remaining_new = max(0, settings.new_cards_per_day - settings.new_cards_today)
        limit = min(limit, remaining_new)
        if limit <= 0:
            return Vocabulary.objects.none()
        
        # Base filter: vocabs user has NOT studied yet
        unstudied = Vocabulary.objects.annotate(
            has_card=Exists(
                FsrsCardStateEn.objects.filter(user=user, vocab=OuterRef('pk'))
            )
        ).filter(has_card=False, language=language)
        
        # Priority: words from user's in-progress sets
        in_progress_set_ids = UserSetProgress.objects.filter(
            user=user, status='in_progress'
        ).values_list('vocabulary_set_id', flat=True)
        
        if not in_progress_set_ids:
            return Vocabulary.objects.none()
        
        priority_vocab_ids = SetItem.objects.filter(
            vocabulary_set_id__in=in_progress_set_ids
        ).values_list('definition__entry__vocab_id', flat=True).distinct()
        
        priority_ids = list(
            unstudied.filter(id__in=priority_vocab_ids)
            .values_list('id', flat=True)[:limit]
        )
        if not priority_ids:
            return Vocabulary.objects.none()
        return Vocabulary.objects.filter(id__in=priority_ids)
    
    @staticmethod
    def get_session_stats(user) -> Dict[str, int]:
        """
        Get counts for learning, review, and new cards.
        Uses a single aggregate query for efficiency.
        
        Returns:
            Dict with 'learning_count', 'review_count', 'new_count'
        """
        now = timezone.now()
        
        # Single aggregate query for learning + review counts
        stats = FsrsCardStateEn.objects.filter(
            user=user, due__lte=now
        ).aggregate(
            learning_count=Count('id', filter=Q(
                state__in=[CARD_STATE_LEARNING, CARD_STATE_RELEARNING]
            )),
            review_count=Count('id', filter=Q(state=CARD_STATE_REVIEW)),
        )
        
        # New cards count — use Exists subquery
        new_count = Vocabulary.objects.annotate(
            has_card=Exists(
                FsrsCardStateEn.objects.filter(user=user, vocab=OuterRef('pk'))
            )
        ).filter(has_card=False, language='english').count()
        
        return {
            'learning_count': stats['learning_count'],
            'review_count': stats['review_count'],
            'new_count': min(new_count, 999),  # Cap display
        }
    
    @staticmethod
    def grade_card(
        user,
        vocab_id: int,
        rating: str,
        create_if_missing: bool = True
    ) -> Dict[str, Any]:
        """
        Grade a card and update its FSRS state.

        Uses select_for_update to prevent race conditions from double-clicks,
        and F() expressions for atomic counter increments.

        Args:
            user: The user
            vocab_id: ID of the Vocabulary
            rating: 'again', 'hard', 'good', or 'easy'
            create_if_missing: If True, create card state for new cards

        Returns:
            Dict with 'success', 'intervals', 'requeue', 'requeue_delay_ms', 'new_state'
        """
        if rating not in ('again', 'hard', 'good', 'easy'):
            return {'success': False, 'error': 'Invalid rating'}

        try:
            vocab = Vocabulary.objects.get(id=vocab_id)
        except Vocabulary.DoesNotExist:
            return {'success': False, 'error': 'Vocabulary not found'}

        with transaction.atomic():
            # Get or create card state with row-level lock
            if create_if_missing:
                card_state, created = FsrsService.get_or_create_card_state(user, vocab)
                if not created:
                    # Re-fetch with lock to prevent concurrent updates
                    card_state = FsrsCardStateEn.objects.select_for_update().get(pk=card_state.pk)
            else:
                try:
                    card_state = FsrsCardStateEn.objects.select_for_update().get(
                        user=user, vocab=vocab
                    )
                except FsrsCardStateEn.DoesNotExist:
                    return {'success': False, 'error': 'Card state not found'}

            was_new = card_state.state == CARD_STATE_NEW

            # Perform FSRS review (returns dict now, not string)
            new_card_data, review_log_data, due_dt = review_card(
                card_state.card_data,
                rating
            )

            # Update card state fields
            card_state.card_data = new_card_data
            card_state.due = due_dt
            card_state.state = new_card_data.get('state', 0)
            card_state.last_review = timezone.now()
            card_state.last_review_log = review_log_data  # Issue #6: save review log

            # Atomic counter increments via F() to prevent race conditions
            card_state.total_reviews = F('total_reviews') + 1
            if rating in ('good', 'easy'):
                card_state.successful_reviews = F('successful_reviews') + 1
            card_state.save()

            # Refresh to get actual counter values after F() expression
            card_state.refresh_from_db()

            # Issue #1: Increment daily counters
            settings, _ = UserStudySettings.objects.get_or_create(user=user)
            settings.reset_daily_counts_if_needed()
            if was_new:
                settings.new_cards_today = F('new_cards_today') + 1
            settings.reviews_today = F('reviews_today') + 1
            settings.last_study_date = timezone.localdate()
            settings.save(update_fields=['new_cards_today', 'reviews_today', 'last_study_date'])

            # Issue #5: Update UserSetProgress if vocab belongs to any user's in-progress sets
            if was_new or rating in ('good', 'easy'):
                user_set_ids = UserSetProgress.objects.filter(
                    user=user, status='in_progress'
                ).values_list('vocabulary_set_id', flat=True)
                if user_set_ids:
                    matching_sets = SetItem.objects.filter(
                        vocabulary_set_id__in=user_set_ids,
                        definition__entry__vocab=vocab
                    ).values_list('vocabulary_set_id', flat=True).distinct()
                    if matching_sets:
                        UserSetProgress.objects.filter(
                            user=user,
                            vocabulary_set_id__in=matching_sets
                        ).update(words_learned=F('words_learned') + 1)

        # Calculate requeue info (outside transaction — read-only)
        requeue = should_requeue_in_session(new_card_data, due_dt)
        requeue_delay_ms = 0
        if requeue:
            delta = (due_dt - timezone.now()).total_seconds() * 1000
            requeue_delay_ms = max(0, int(delta))

        # Get new intervals for UI
        new_intervals = preview_intervals(new_card_data)

        return {
            'success': True,
            'intervals': new_intervals,
            'requeue': requeue,
            'requeue_delay_ms': requeue_delay_ms,
            'new_state': card_state.state,
        }
    
    @staticmethod
    def format_card_for_ui(
        vocab: Vocabulary,
        definition: Optional[WordDefinition] = None,
        card_state: Optional[FsrsCardStateEn] = None,
        voice_pref: str = 'us'
    ) -> Dict[str, Any]:
        """
        Format a vocabulary item for the flashcard UI.
        
        Ensures consistent card data structure across all features.
        """
        # Get first definition if not provided
        if definition is None:
            entry = vocab.entries.first()
            if entry:
                definition = entry.definitions.first()
        else:
            entry = definition.entry
        
        # Get card state info
        state_id = card_state.id if card_state else None
        card_state_value = card_state.state if card_state else CARD_STATE_NEW
        intervals = {}
        if card_state and card_state.card_data:
            intervals = preview_intervals(card_state.card_data)
        
        extra = vocab.extra_data or {}
        return {
            # IDs
            'id': vocab.id,
            'state_id': state_id,
            'definition_id': definition.id if definition else None,
            
            # Card state
            'card_state': card_state_value,
            'intervals': intervals,
            
            # Content — Issue #3: include aliases matching frontend expectations
            'word': vocab.word,
            'en_word': vocab.word,
            'term': vocab.word,
            
            'reading': extra.get('reading', '') or (entry.ipa if entry else ''),
            'phonetic': entry.ipa if entry else '',
            'ipa': entry.ipa if entry else '',
            'pos': entry.part_of_speech if entry else '',
            
            'meaning': definition.meaning if definition else '',
            'vi_meaning': definition.meaning if definition else '',
            'definition': definition.meaning if definition else '',
            'en_definition': '',
            
            'sino_vi': extra.get('han_viet', ''),
            'language': vocab.language,
            
            'example_text': definition.example_sentence if definition else '',
            'example_en': definition.example_sentence if definition else '',
            'example': definition.example_sentence if definition else '',
            'example_translation': definition.example_trans if definition else '',
            'example_vi': definition.example_trans if definition else '',
            
            # Audio
            'audio': entry.get_audio_url(voice_pref) if entry else '',
            'audio_us': entry.audio_us if entry else '',
            'audio_uk': entry.audio_uk if entry else '',
        }
    
    @staticmethod
    def get_flashcard_session(
        user,
        new_limit: int = 20,
        review_limit: int = 100,
        language: str = 'english'
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Get a complete flashcard session with cards and stats.
        
        Returns:
            Tuple of (cards_list, stats_dict)
        """
        cards = []
        
        # 1. Get due cards — prefetch entries+definitions to avoid N+1
        due_cards = FsrsService.get_due_cards(user, limit=review_limit, language=language)
        # Prefetch vocab entries and definitions in batch
        vocab_ids = [cs.vocab_id for cs in due_cards]
        from vocab.models import WordEntry
        entries_map = {}  # vocab_id -> (entry, definition)
        if vocab_ids:
            for entry in WordEntry.objects.filter(
                vocab_id__in=vocab_ids
            ).select_related('vocab').prefetch_related('definitions'):
                if entry.vocab_id not in entries_map:
                    defn = entry.definitions.all()[:1]
                    entries_map[entry.vocab_id] = (entry, defn[0] if defn else None)
        
        for card_state in due_cards:
            vocab = card_state.vocab
            entry_data = entries_map.get(vocab.id)
            if entry_data:
                entry, definition = entry_data
            else:
                entry, definition = None, None
            cards.append(FsrsService.format_card_for_ui(
                vocab=vocab,
                definition=definition,
                card_state=card_state
            ))
        
        # 2. Get new cards (if room)
        remaining_slots = new_limit
        if remaining_slots > 0:
            new_vocabs = FsrsService.get_new_vocabs(
                user, 
                language=language, 
                limit=remaining_slots
            )
            for vocab in new_vocabs:
                # Create card state for new vocab
                card_state, _ = FsrsService.get_or_create_card_state(user, vocab)
                cards.append(FsrsService.format_card_for_ui(
                    vocab=vocab,
                    card_state=card_state
                ))
        
        # Get stats
        stats = FsrsService.get_session_stats(user)
        
        return cards, stats
