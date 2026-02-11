from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import os
import uuid

# Helper functions for UserStudySettings (if needed for older migrations compatibility or logic)
# But UserStudySettings logic seems self-contained or simple fields.

class UserStudySettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_settings',
    )
    
    # Daily limits
    new_cards_per_day = models.PositiveIntegerField(
        default=20,
        help_text="Số từ mới tối đa mỗi ngày"
    )
    reviews_per_day = models.PositiveIntegerField(
        default=200,
        help_text="Số lượt ôn tập tối đa mỗi ngày"
    )
    
    # Tracking cho ngày hiện tại
    new_cards_today = models.PositiveIntegerField(default=0)
    reviews_today = models.PositiveIntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)

    class EnglishVoice(models.TextChoices):
        US = "us", "US"
        UK = "uk", "UK"

    english_voice_preference = models.CharField(
        "Giọng tiếng Anh ưa thích (EN)",
        max_length=2,
        choices=EnglishVoice.choices,
        default=EnglishVoice.US,
        help_text="Dùng để chọn audio US/UK. Nếu thiếu giọng ưa thích, hệ thống sẽ fallback sang giọng còn lại.",
    )
    
    class Meta:
        verbose_name = "Cài đặt học tập"
        verbose_name_plural = "Cài đặt học tập"
    
    def __str__(self):
        return f"{self.user} - {self.new_cards_per_day} new/day"
    
    def reset_daily_counts_if_needed(self):
        """Reset counters nếu đã sang ngày mới."""
        today = timezone.localdate()
        if self.last_study_date != today:
            self.new_cards_today = 0
            self.reviews_today = 0
            self.last_study_date = today
            self.save(update_fields=['new_cards_today', 'reviews_today', 'last_study_date'])
    
    def can_study_new(self) -> bool:
        self.reset_daily_counts_if_needed()
        return self.new_cards_today < self.new_cards_per_day
    
    def can_review(self) -> bool:
        self.reset_daily_counts_if_needed()
        return self.reviews_today < self.reviews_per_day


class Vocabulary(models.Model):
    """
    Vocabulary Core - Tầng 1: Mặt chữ (Spelling).
    Chỉ lưu trữ từ vựng để phục vụ tìm kiếm.
    IPA và Audio đã chuyển sang WordEntry.
    """
    class Language(models.TextChoices):
        ENGLISH = 'en', _('English')
        JAPANESE = 'jp', _('Japanese')

    word = models.CharField(max_length=255, unique=True, db_index=True, help_text="Từ vựng (VD: record)")
    
    # Language support
    language = models.CharField(
        max_length=10, 
        choices=Language.choices, 
        default=Language.ENGLISH, 
        db_index=True,
        help_text="Ngôn ngữ của từ vựng"
    )
    extra_data = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Dữ liệu bổ sung (VD: Kanji, Romaji cho tiếng Nhật)"
    )

    def __str__(self):
        return f"[{self.get_language_display()}] {self.word}"

    class Meta:
        verbose_name = "Vocabulary"
        verbose_name_plural = "Vocabularies"


class WordEntry(models.Model):
    """
    Word Entry - Tầng 2: Lexical Entry.
    Đại diện cho một "loại từ" của từ đó với IPA và Audio riêng.
    VD: "record" có 2 entries: noun (/ˈrek.ɚd/) + verb (/rɪˈkɔːrd/).
    """
    vocab = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='entries')
    part_of_speech = models.CharField(max_length=50, help_text="noun, verb, adj...")
    ipa = models.CharField(max_length=100, blank=True, help_text="Phiên âm (VD: /ˈrek.ɚd/)")
    audio_us = models.CharField(max_length=500, blank=True, help_text="Audio URL (US)")
    audio_uk = models.CharField(max_length=500, blank=True, help_text="Audio URL (UK)")

    class Meta:
        verbose_name = "Word Entry"
        verbose_name_plural = "Word Entries"
        unique_together = ('vocab', 'part_of_speech')

    def __str__(self):
        return f"{self.vocab.word} ({self.part_of_speech})"
    
    def get_audio_url(self, preference='us'):
        """Get audio URL based on preference, with fallback."""
        if preference == 'uk':
            return self.audio_uk or self.audio_us
        return self.audio_us or self.audio_uk


class WordDefinition(models.Model):
    """
    Word Definition - Tầng 3: Nghĩa cụ thể.
    Một entry có thể có nhiều nghĩa.
    """
    entry = models.ForeignKey(WordEntry, on_delete=models.CASCADE, related_name='definitions')
    meaning = models.TextField(help_text="Nghĩa tiếng Việt")
    image_url = models.CharField(max_length=500, blank=True, null=True, help_text="Ảnh minh họa")
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dữ liệu bổ sung (VD: Furigana cho ví dụ)"
    )

    @property
    def primary_example(self):
        """Get the first ExampleSentence, prefetch-aware."""
        if 'examples' in getattr(self, '_prefetched_objects_cache', {}):
            examples = self.examples.all()
            return examples[0] if examples else None
        return self.examples.first()

    @property
    def example_sentence(self):
        """Backward-compatible: returns primary example sentence text."""
        ex = self.primary_example
        return ex.sentence if ex else ''

    @property
    def example_trans(self):
        """Backward-compatible: returns primary example translation."""
        ex = self.primary_example
        return ex.translation if ex else ''

    def __str__(self):
        return f"{self.entry.vocab.word} ({self.entry.part_of_speech}): {self.meaning}"

    class Meta:
        verbose_name = "Word Definition"
        verbose_name_plural = "Word Definitions"


class ExampleSentence(models.Model):
    """
    Câu ví dụ cho một nghĩa (WordDefinition).
    Hỗ trợ nhiều câu ví dụ từ nhiều nguồn khác nhau.
    """
    class Source(models.TextChoices):
        CAMBRIDGE = 'cambridge', 'Cambridge'
        TOEIC_600 = 'toeic_600', 'TOEIC 600'
        TOEIC_730 = 'toeic_730', 'TOEIC 730'
        TOEIC_860 = 'toeic_860', 'TOEIC 860'
        TOEIC_990 = 'toeic_990', 'TOEIC 990'
        MIMIKARA_N2 = 'mimikara_n2', 'Mimikara N2'
        OXFORD = 'oxford', 'Oxford'
        USER = 'user', 'User'
        OTHER = 'other', 'Other'

    definition = models.ForeignKey(
        WordDefinition, on_delete=models.CASCADE, related_name='examples'
    )
    sentence = models.TextField(help_text="Câu ví dụ tiếng Anh")
    translation = models.TextField(blank=True, help_text="Dịch câu ví dụ")
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.CAMBRIDGE, db_index=True
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Example Sentence"
        verbose_name_plural = "Example Sentences"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.definition} - {self.sentence[:50]}"


class Course(models.Model):
    """
    Khóa học (Course) - e.g. TOEIC 600, TOEIC 990.
    Replaces hardcoded TOEIC_LEVELS config.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)

    language = models.CharField(
        max_length=10,
        choices=Vocabulary.Language.choices,
        default=Vocabulary.Language.ENGLISH,
    )

    # Link to legacy integer level for compatibility with VocabularySet
    toeic_level = models.IntegerField(unique=True, null=True, blank=True)
    
    # UI config
    icon = models.TextField(help_text="SVG Icon or Emoji", blank=True)
    gradient = models.CharField(max_length=255, help_text="CSS Gradient value", default="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"



class VocabularySet(models.Model):
    """
    Bộ từ vựng (Vocabulary Set).
    Dùng chung cho cả System (owner_id=NULL) và User.
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')

    class ToeicLevel(models.IntegerChoices):
        LEVEL_600 = 600, _('TOEIC 600')
        LEVEL_730 = 730, _('TOEIC 730')
        LEVEL_860 = 860, _('TOEIC 860')
        LEVEL_990 = 990, _('TOEIC 990')

    title = models.CharField(max_length=255, help_text="Tên bộ (VD: TOEIC 600)")
    description = models.TextField(blank=True, help_text="Mô tả bộ từ vựng")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='vocabulary_sets', help_text="Null = System, ID = User")
    is_public = models.BooleanField(default=False, help_text="Công khai hay riêng tư")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # New field for set language
    language = models.CharField(
        max_length=10,
        choices=Vocabulary.Language.choices,
        default=Vocabulary.Language.ENGLISH,
        help_text="Ngôn ngữ của bộ từ vựng"
    )

    # TOEIC fields
    toeic_level = models.IntegerField(
        choices=ToeicLevel.choices,
        null=True, blank=True,
        db_index=True,
        help_text="TOEIC level (600/730/860/990). Null = not a TOEIC set."
    )
    set_number = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Set number within a TOEIC level (1-based)"
    )
    
    # Chapter/Milestone organization
    chapter = models.PositiveIntegerField(
        null=True, blank=True,
        db_index=True,
        help_text="Chapter number (1-4 for Level 600)"
    )
    chapter_name = models.CharField(
        max_length=100, blank=True,
        help_text="Chapter name (VD: 'Nền tảng cốt lõi')"
    )
    milestone = models.CharField(
        max_length=10, blank=True,
        db_index=True,
        help_text="Milestone code (VD: '1A', '1B', '2A')"
    )
    priority_range = models.CharField(
        max_length=20, blank=True,
        help_text="Priority range (VD: '1-10', '11-20')"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        owner_name = self.owner.username if self.owner else "System"
        return f"{self.title} ({owner_name})"

    class Meta:
        verbose_name = "Vocabulary Set"
        verbose_name_plural = "Vocabulary Sets"
        constraints = [
            models.UniqueConstraint(
                fields=['toeic_level', 'set_number'],
                name='unique_toeic_level_set_number',
                condition=models.Q(toeic_level__isnull=False),
            )
        ]


class SetItem(models.Model):
    """
    Bảng trung gian nối WordDefinition vào VocabularySet.
    """
    vocabulary_set = models.ForeignKey(VocabularySet, on_delete=models.CASCADE, related_name='items')
    definition = models.ForeignKey(WordDefinition, on_delete=models.CASCADE, related_name='included_in_sets')
    display_order = models.IntegerField(default=0, help_text="Thứ tự xuất hiện")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vocabulary_set.title} - {self.definition.entry.vocab.word}"

    class Meta:
        verbose_name = "Set Item"
        verbose_name_plural = "Set Items"
        ordering = ['display_order', 'created_at']


class SetItemExample(models.Model):
    """
    Liên kết ExampleSentence với SetItem cụ thể.
    Cho phép mỗi bộ từ vựng chọn riêng ví dụ nào hiển thị cho từng từ.
    - Khi có set context: dùng set_item.set_examples
    - Khi không có set context: fallback về definition.examples
    """
    set_item = models.ForeignKey(SetItem, on_delete=models.CASCADE, related_name='set_examples')
    example = models.ForeignKey(ExampleSentence, on_delete=models.CASCADE, related_name='set_item_links')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Set Item Example"
        verbose_name_plural = "Set Item Examples"
        unique_together = ('set_item', 'example')
        ordering = ['order']

    def __str__(self):
        return f"{self.set_item} → {self.example.sentence[:40]}"


class FsrsCardStateEn(models.Model):
    """
    Lưu trạng thái FSRS cho từ vựng tiếng Anh của user.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fsrs_states_en')
    vocab = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='fsrs_states')
    
    # FSRS core data (JSON dump of FSRS Card object)
    card_data = models.JSONField(default=dict)
    
    # Denormalized fields for faster querying
    state = models.IntegerField(default=0, db_index=True, help_text="0=New, 1=Learning, 2=Review, 3=Relearning")
    due = models.DateTimeField(null=True, blank=True, db_index=True)
    last_review = models.DateTimeField(null=True, blank=True)
    
    # Stats inferred from review history or FSRS object
    total_reviews = models.PositiveIntegerField(default=0)
    successful_reviews = models.PositiveIntegerField(default=0) # Reviews with rate >= Good

    class Meta:
        unique_together = ('user', 'vocab')
        verbose_name = "FSRS Card State (EN)"
        verbose_name_plural = "FSRS Card States (EN)"

    def __str__(self):
        return f"{self.user.username} - {self.vocab.word} (State: {self.state})"


class UserSetProgress(models.Model):
    """
    Tracks a user's progress through a VocabularySet (especially TOEIC sets).
    """
    class ProgressStatus(models.TextChoices):
        NOT_STARTED = 'not_started', _('Not Started')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='set_progress',
    )
    vocabulary_set = models.ForeignKey(
        VocabularySet,
        on_delete=models.CASCADE,
        related_name='user_progress',
    )
    status = models.CharField(
        max_length=20,
        choices=ProgressStatus.choices,
        default=ProgressStatus.NOT_STARTED,
    )
    words_learned = models.PositiveIntegerField(default=0)
    words_total = models.PositiveIntegerField(default=0)
    quiz_best_score = models.PositiveIntegerField(
        default=0,
        help_text="Best quiz score as percentage (0-100)"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'vocabulary_set')
        verbose_name = "User Set Progress"
        verbose_name_plural = "User Set Progress"

    def __str__(self):
        return f"{self.user.username} - {self.vocabulary_set.title} ({self.status})"
