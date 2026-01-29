"""
Utility functions for the TOEIC vocabulary learning system.
Handles unlock logic, progress tracking, and set state computation.
"""
from django.utils import timezone

from .models import VocabularySet, UserSetProgress, FsrsCardStateEn, SetItem
from .toeic_config import TOEIC_LEVELS, TOEIC_LEVEL_ORDER


def get_level_completion_percent(user, level):
    """Return the percentage of learned words for a TOEIC level (0-100)."""
    config = TOEIC_LEVELS.get(level)
    if not config:
        return 0
    
    # Count total words in all published sets for this level
    total_words = SetItem.objects.filter(
        vocabulary_set__toeic_level=level,
        vocabulary_set__status='published'
    ).count()
    
    if total_words == 0:
        return 0
        
    # Count learned words
    learned_words = get_level_words_learned_count(user, level)
    
    return round(learned_words / total_words * 100)


def get_level_words_learned(user, level):
    """Return total words learned across all sets in a TOEIC level."""
    return UserSetProgress.objects.filter(
        user=user,
        vocabulary_set__toeic_level=level,
    ).exclude(
        status=UserSetProgress.ProgressStatus.NOT_STARTED,
    ).values_list('words_learned', flat=True)


def get_level_words_learned_count(user, level):
    """
    Return the count of learned words (state > 0) in a level.
    Uses FsrsCardStateEn as the source of truth instead of UserSetProgress cache.
    """
    if not user.is_authenticated:
        return 0
        
    level_vocab_ids = SetItem.objects.filter(
        vocabulary_set__toeic_level=level,
        vocabulary_set__status='published'
    ).values_list('definition__entry__vocab_id', flat=True)
    
    return FsrsCardStateEn.objects.filter(
        user=user,
        vocab_id__in=level_vocab_ids,
        state__gt=0
    ).count()


def is_level_unlocked(user, level):
    """Check if a TOEIC level is unlocked for the user."""
    # Always unlocked
    return True


def is_set_accessible(user, level, set_number):
    """
    Check if a specific set is accessible (not locked).
    Always returns True as per user request to unlock everything.
    """
    return True


def get_set_state(user, level, set_number):
    """
    Get the display state for a set tile.
    Returns: 'available', 'in_progress', 'completed' (never 'locked')
    """
    # Always accessible
    vocab_set = VocabularySet.objects.filter(
        toeic_level=level, set_number=set_number
    ).first()
    if not vocab_set:
        return 'available' # Or maybe 'locked' if it doesn't exist? But logical to show available/placeholder
    
    progress = UserSetProgress.objects.filter(
        user=user, vocabulary_set=vocab_set
    ).first()
    
    if not progress or progress.status == UserSetProgress.ProgressStatus.NOT_STARTED:
        return 'available'
    if progress.status == UserSetProgress.ProgressStatus.IN_PROGRESS:
        return 'in_progress'
    return 'completed'


def get_review_count(user):
    """Count FSRS due cards for all TOEIC words."""
    now = timezone.now()
    toeic_vocab_ids = SetItem.objects.filter(
        vocabulary_set__toeic_level__isnull=False,
        vocabulary_set__status='published',
    ).values_list(
        'definition__entry__vocab_id', flat=True
    ).distinct()
    return FsrsCardStateEn.objects.filter(
        user=user,
        vocab_id__in=toeic_vocab_ids,
        due__lte=now,
    ).count()


def get_level_review_count(user, level):
    """Count FSRS due cards for a specific TOEIC level."""
    now = timezone.now()
    level_vocab_ids = SetItem.objects.filter(
        vocabulary_set__toeic_level=level,
        vocabulary_set__status='published',
    ).values_list(
        'definition__entry__vocab_id', flat=True
    ).distinct()
    return FsrsCardStateEn.objects.filter(
        user=user,
        vocab_id__in=level_vocab_ids,
        due__lte=now,
    ).count()
