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
from datetime import timedelta
from typing import Optional, Dict, Any, List, Tuple

from django.utils import timezone
from django.db import models
from django.db.models import Q

from vocab.models import Vocabulary, FsrsCardStateEn, WordDefinition
from vocab.fsrs_bridge import (
    review_card,
    preview_intervals,
    create_new_card_state,
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
                'card_data': json.loads(create_new_card_state().to_json()),
                'state': CARD_STATE_NEW,
                'due': timezone.now(),
            }
        )
        return card_state, created
    
    @staticmethod
    def get_due_cards(user, limit: int = None) -> models.QuerySet:
        """
        Get cards that are due for review (Learning + Review + Relearning).
        
        Args:
            user: The user
            limit: Maximum number of cards to return
            
        Returns:
            QuerySet of FsrsCardStateEn ordered by due date
        """
        limit = limit or FsrsService.DEFAULT_REVIEW_LIMIT
        now = timezone.now()
        
        return FsrsCardStateEn.objects.filter(
            user=user,
            due__lte=now,
            state__in=[CARD_STATE_LEARNING, CARD_STATE_REVIEW, CARD_STATE_RELEARNING]
        ).select_related('vocab').order_by('due')[:limit]
    
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
        
        Args:
            user: The user
            language: 'english' or other language code
            limit: Maximum number to return
            
        Returns:
            QuerySet of Vocabulary items
        """
        limit = limit or FsrsService.DEFAULT_NEW_LIMIT
        
        # Get vocab IDs that already have a card state for this user
        existing_vocab_ids = FsrsCardStateEn.objects.filter(
            user=user
        ).values_list('vocab_id', flat=True)
        
        return Vocabulary.objects.filter(
            language=language
        ).exclude(
            id__in=existing_vocab_ids
        ).select_related().order_by('?')[:limit]
    
    @staticmethod
    def get_session_stats(user) -> Dict[str, int]:
        """
        Get counts for learning, review, and new cards.
        
        Returns:
            Dict with 'learning_count', 'review_count', 'new_count'
        """
        now = timezone.now()
        
        learning_count = FsrsCardStateEn.objects.filter(
            user=user,
            state__in=[CARD_STATE_LEARNING, CARD_STATE_RELEARNING],
            due__lte=now
        ).count()
        
        review_count = FsrsCardStateEn.objects.filter(
            user=user,
            state=CARD_STATE_REVIEW,
            due__lte=now
        ).count()
        
        # New cards = vocab without any card state
        # This is expensive, so we cap it
        new_count = Vocabulary.objects.filter(
            language='english'
        ).exclude(
            id__in=FsrsCardStateEn.objects.filter(user=user).values_list('vocab_id', flat=True)
        ).count()
        
        return {
            'learning_count': learning_count,
            'review_count': review_count,
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
        
        # Get or create card state
        if create_if_missing:
            card_state, created = FsrsService.get_or_create_card_state(user, vocab)
        else:
            try:
                card_state = FsrsCardStateEn.objects.get(user=user, vocab=vocab)
                created = False
            except FsrsCardStateEn.DoesNotExist:
                return {'success': False, 'error': 'Card state not found'}
        
        # Perform FSRS review
        new_card_json, review_log_json, due_dt = review_card(
            card_state.card_data, 
            rating
        )
        
        # Parse JSON if needed
        if isinstance(new_card_json, str):
            new_card_json = json.loads(new_card_json)
        
        # Update card state
        card_state.card_data = new_card_json
        card_state.due = due_dt
        card_state.state = new_card_json.get('state', 0)
        card_state.last_review = timezone.now()
        card_state.total_reviews += 1
        if rating in ('good', 'easy'):
            card_state.successful_reviews += 1
        card_state.save()
        
        # Calculate requeue info
        requeue = should_requeue_in_session(new_card_json, due_dt)
        requeue_delay_ms = 0
        if requeue:
            delta = (due_dt - timezone.now()).total_seconds() * 1000
            requeue_delay_ms = max(0, int(delta))
        
        # Get new intervals for UI
        new_intervals = preview_intervals(new_card_json)
        
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
        
        return {
            # IDs
            'id': vocab.id,
            'state_id': state_id,
            'definition_id': definition.id if definition else None,
            
            # Card state
            'card_state': card_state_value,
            'intervals': intervals,
            
            # Content (consistent keys for JS)
            'en_word': vocab.word,
            'term': vocab.word,  # Alias for compatibility
            'phonetic': entry.ipa if entry else '',
            'ipa': entry.ipa if entry else '',  # Alias
            'pos': entry.part_of_speech if entry else '',
            
            'vi_meaning': definition.meaning if definition else '',
            'definition': definition.meaning if definition else '',  # Alias
            'en_definition': '',  # Could add English definition if available
            
            'example_en': definition.example_sentence if definition else '',
            'example': definition.example_sentence if definition else '',  # Alias
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
        
        # 1. Get due cards (Learning + Review + Relearning)
        due_cards = FsrsService.get_due_cards(user, limit=review_limit)
        for card_state in due_cards:
            vocab = card_state.vocab
            cards.append(FsrsService.format_card_for_ui(
                vocab=vocab,
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
