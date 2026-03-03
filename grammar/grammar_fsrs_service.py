"""
Grammar FSRS Service — spaced repetition for grammar flashcards.

Reuses the same FSRS core (vocab/fsrs_bridge.py) with grammar-specific logic.
"""

from django.db import transaction
from django.db.models import F, Exists, OuterRef
from django.utils import timezone

from vocab.fsrs_bridge import (
    review_card,
    preview_intervals,
    create_new_card_state,
    card_data_to_dict,
    should_requeue_in_session,
    CARD_STATE_NEW,
    CARD_STATE_LEARNING,
    CARD_STATE_REVIEW,
    CARD_STATE_RELEARNING,
)


class GrammarFsrsService:
    """Service class for grammar FSRS operations."""

    @staticmethod
    def get_or_create_card_state(user, grammar_point):
        from grammar.models import FsrsCardStateGrammar
        card_state, created = FsrsCardStateGrammar.objects.get_or_create(
            user=user,
            grammar_point=grammar_point,
            defaults={
                'card_data': card_data_to_dict(create_new_card_state()),
                'state': CARD_STATE_NEW,
                'due': timezone.now(),
            }
        )
        return card_state, created

    @staticmethod
    def get_due_cards(user, limit=None):
        """Get grammar cards that are due for review (including NEW)."""
        from grammar.models import FsrsCardStateGrammar
        qs = FsrsCardStateGrammar.objects.filter(
            user=user,
            state__in=[CARD_STATE_NEW, CARD_STATE_LEARNING, CARD_STATE_REVIEW, CARD_STATE_RELEARNING],
            due__lte=timezone.now(),
        ).select_related('grammar_point').order_by('due')
        if limit:
            qs = qs[:limit]
        return qs

    @staticmethod
    def get_new_grammar(user, level=None, limit=20):
        """Get grammar points the user has never studied."""
        from grammar.models import GrammarPoint, FsrsCardStateGrammar
        qs = GrammarPoint.objects.filter(is_active=True).annotate(
            has_state=Exists(
                FsrsCardStateGrammar.objects.filter(
                    user=user, grammar_point=OuterRef('pk')
                )
            )
        ).filter(has_state=False)
        if level:
            qs = qs.filter(level=level)
        return qs[:limit]

    @staticmethod
    def grade_card(user, grammar_point_id, rating):
        """Grade a grammar card and update FSRS state."""
        from grammar.models import GrammarPoint, FsrsCardStateGrammar

        if rating not in ('again', 'hard', 'good', 'easy'):
            return {'success': False, 'error': 'Invalid rating'}

        try:
            gp = GrammarPoint.objects.get(id=grammar_point_id)
        except GrammarPoint.DoesNotExist:
            return {'success': False, 'error': 'Grammar point not found'}

        with transaction.atomic():
            card_state, created = GrammarFsrsService.get_or_create_card_state(user, gp)
            if not created:
                card_state = FsrsCardStateGrammar.objects.select_for_update().get(pk=card_state.pk)

            # Perform FSRS review
            new_card_data, review_log_data, due_dt = review_card(
                card_state.card_data, rating
            )

            card_state.card_data = new_card_data
            card_state.due = due_dt
            card_state.state = new_card_data.get('state', 0)
            card_state.last_review = timezone.now()
            card_state.last_review_log = review_log_data

            card_state.total_reviews = F('total_reviews') + 1
            if rating in ('good', 'easy'):
                card_state.successful_reviews = F('successful_reviews') + 1
            card_state.save()
            card_state.refresh_from_db()

        # Requeue logic
        requeue = should_requeue_in_session(new_card_data, due_dt)
        requeue_delay_ms = 0
        if requeue:
            delta = (due_dt - timezone.now()).total_seconds() * 1000
            requeue_delay_ms = max(0, int(delta))

        new_intervals = preview_intervals(new_card_data)

        return {
            'success': True,
            'intervals': new_intervals,
            'requeue': requeue,
            'requeue_delay_ms': requeue_delay_ms,
            'new_state': card_state.state,
        }

    @staticmethod
    def format_card_for_ui(grammar_point, card_state=None):
        """Format a grammar point for the flashcard UI."""
        intervals = {}
        if card_state:
            try:
                intervals = preview_intervals(card_state.card_data)
            except Exception:
                pass

        return {
            'id': grammar_point.id,
            'grammar_point': grammar_point.title,
            'grammar_structure': grammar_point.formation,
            'grammar_meaning': grammar_point.meaning_vi,
            'grammar_note': grammar_point.notes or '',
            'grammar_furigana': grammar_point.reading,
            'level': grammar_point.level,
            'state_id': card_state.id if card_state else None,
            'is_new': card_state.state == CARD_STATE_NEW if card_state else True,
            'intervals': intervals,
        }

    @staticmethod
    def get_flashcard_session(user, level=None, new_limit=20, review_limit=100):
        """Get a complete grammar flashcard session with cards and stats."""
        from grammar.models import FsrsCardStateGrammar
        cards = []

        # 1. Due cards
        due_cards = GrammarFsrsService.get_due_cards(user, limit=review_limit)
        if level:
            due_cards = due_cards.filter(grammar_point__level=level)
        for cs in due_cards:
            cards.append(GrammarFsrsService.format_card_for_ui(cs.grammar_point, cs))

        # 2. New cards
        if len(cards) < new_limit:
            remaining = new_limit - len(cards)
            new_gps = GrammarFsrsService.get_new_grammar(user, level=level, limit=remaining)
            for gp in new_gps:
                cs, _ = GrammarFsrsService.get_or_create_card_state(user, gp)
                cards.append(GrammarFsrsService.format_card_for_ui(gp, cs))

        # Stats
        all_states = FsrsCardStateGrammar.objects.filter(user=user)
        now = timezone.now()
        stats = {
            'total': all_states.count(),
            'learning': all_states.filter(
                state__in=[CARD_STATE_LEARNING, CARD_STATE_RELEARNING]
            ).count(),
            'review': all_states.filter(
                state=CARD_STATE_REVIEW, due__lte=now
            ).count(),
            'new': GrammarFsrsService.get_new_grammar(user, level=level, limit=1000).count(),
        }

        return cards, stats
