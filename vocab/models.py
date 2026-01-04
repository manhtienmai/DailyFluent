from django.db import models
from django.conf import settings
from django.utils import timezone
import json
import math
import uuid
import os


def en_vocab_image_upload_to(_instance, filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or "").lower()
    return f"en_vocab/images/{uuid.uuid4().hex}{ext}"


def en_vocab_audio_us_upload_to(_instance, filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or "").lower()
    return f"en_vocab/audio/us/{uuid.uuid4().hex}{ext}"


def en_vocab_audio_uk_upload_to(_instance, filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or "").lower()
    return f"en_vocab/audio/uk/{uuid.uuid4().hex}{ext}"


def en_example_audio_us_upload_to(_instance, filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or "").lower()
    return f"en_vocab/examples/audio/us/{uuid.uuid4().hex}{ext}"


def en_example_audio_uk_upload_to(_instance, filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    ext = (ext or "").lower()
    return f"en_vocab/examples/audio/uk/{uuid.uuid4().hex}{ext}"


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
        help_text="Dùng để chọn audio US/UK (từ vựng + ví dụ). Nếu thiếu giọng ưa thích, hệ thống sẽ fallback sang giọng còn lại.",
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
    
    def remaining_new(self) -> int:
        self.reset_daily_counts_if_needed()
        return max(0, self.new_cards_per_day - self.new_cards_today)
    
    def remaining_reviews(self) -> int:
        self.reset_daily_counts_if_needed()
        return max(0, self.reviews_per_day - self.reviews_today)


class Vocabulary(models.Model):
    class JLPTLevel(models.TextChoices):
        N5 = 'N5', 'N5'
        N4 = 'N4', 'N4'
        N3 = 'N3', 'N3'
        N2 = 'N2', 'N2'
        N1 = 'N1', 'N1'
        NONE = '', 'Không rõ'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='vocab_items'
    )

    jp_kanji = models.CharField("Tiếng Nhật (kanji)", max_length=100, blank=True)
    jp_kana = models.CharField("Tiếng Nhật (kana)", max_length=100)

    sino_vi = models.CharField(
        "Hán tự",
        max_length=100,
        blank=True,
        help_text="Ví dụ: Cát hợp, Nhân lực..."
    )

    vi_meaning = models.CharField("Nghĩa tiếng Việt", max_length=255)
    en_meaning = models.CharField(
        "Meaning (English)",
        max_length=255,
        blank=True,
        help_text="Optional English meaning (if available)",
    )

    jlpt_level = models.CharField(
        "Cấp JLPT",
        max_length=4,
        choices=JLPTLevel.choices,
        blank=True,
        help_text="Ví dụ: N5, N4..."
    )

    topic = models.CharField(
        "Chủ đề",
        max_length=100,
        blank=True,
        help_text="Ví dụ: Chào hỏi, Gia đình, Mua sắm..."
    )

    # Gán theo khóa/bài (optional)
    course = models.ForeignKey(
        "core.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jp_vocab_items",
    )
    section = models.ForeignKey(
        "core.Section",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jp_vocab_items",
    )
    lesson = models.ForeignKey(
        "core.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jp_vocab_items",
    )

    example_jp = models.TextField("Ví dụ tiếng Nhật", blank=True)
    example_vi = models.TextField("Nghĩa câu ví dụ", blank=True)

    notes = models.TextField(
        "Ghi chú / giải thích",
        blank=True,
        help_text="Ghi chú thêm (mẹo nhớ, phân biệt nghĩa, ngữ cảnh sử dụng...)",
    )

    # Liên kết các Hán tự đơn xuất hiện trong từ này, ví dụ 割合 -> {割, 合}
    kanji_chars = models.ManyToManyField(
        "kanji.Kanji",
        related_name="vocabulary_items",
        blank=True,
        help_text="Các Hán tự có mặt trong từ vựng này",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(
        "Đã kiểm tra",
        default=False,
        help_text="Tick khi bạn đã rà soát & sửa đúng dữ liệu từ này trong admin.",
    )

    class Meta:
        verbose_name = "Từ vựng"
        verbose_name_plural = "Từ vựng"
        ordering = ['jp_kana']

    def __str__(self):
        return f"{self.jp_kana} - {self.vi_meaning}"


class EnglishVocabulary(models.Model):
    """
    Từ vựng tiếng Anh (tách riêng khỏi Vocabulary tiếng Nhật).
    """
    en_word = models.CharField("Từ vựng tiếng Anh", max_length=200)
    phonetic = models.CharField("Phiên âm", max_length=200, blank=True)
    vi_meaning = models.CharField("Nghĩa tiếng Việt", max_length=255)
    en_definition = models.TextField("Định nghĩa tiếng Anh", blank=True)
    example_en = models.TextField("Câu ví dụ tiếng Anh", blank=True)
    example_vi = models.TextField("Nghĩa câu ví dụ (VI)", blank=True)
    notes = models.TextField("Ghi chú", blank=True)
    
    # New fields for enhanced vocabulary data
    pos = models.CharField(
        "Part of Speech",
        max_length=50,
        blank=True,
        help_text="Từ loại (noun, verb, adjective, adverb, etc.)",
    )
    pos_candidates = models.JSONField(
        "POS Candidates",
        default=list,
        blank=True,
        help_text="Danh sách các từ loại có thể (JSON array)",
    )
    audio_pack_uuid = models.CharField(
        "Audio Pack UUID",
        max_length=100,
        blank=True,
        help_text="UUID của audio pack để tải về sau",
    )

    image = models.ImageField(
        "Ảnh minh hoạ",
        upload_to=en_vocab_image_upload_to,
        null=True,
        blank=True,
        help_text="Ảnh minh hoạ cho từ vựng (upload lên Azure).",
    )

    audio_us = models.FileField(
        "Audio (US)",
        upload_to=en_vocab_audio_us_upload_to,
        null=True,
        blank=True,
        help_text="File phát âm giọng US (mp3/wav...).",
    )
    audio_uk = models.FileField(
        "Audio (UK)",
        upload_to=en_vocab_audio_uk_upload_to,
        null=True,
        blank=True,
        help_text="File phát âm giọng UK (mp3/wav...).",
    )

    # Không bắt buộc, để nhóm theo bài/khóa (text legacy)
    lesson = models.CharField("Lesson", max_length=100, blank=True)
    course = models.CharField("Course", max_length=100, blank=True)

    # Gán theo khóa/bài (optional, dropdown trong admin)
    course_ref = models.ForeignKey(
        "core.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="en_vocab_items",
    )
    section = models.CharField("Section/Part", max_length=100, blank=True)
    section_ref = models.ForeignKey(
        "core.Section",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="en_vocab_items",
    )
    lesson_ref = models.ForeignKey(
        "core.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="en_vocab_items",
    )

    import_order = models.PositiveIntegerField(
        "Import Order",
        null=True,
        blank=True,
        help_text="Thứ tự import từ JSON (để giữ nguyên thứ tự ban đầu)",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Từ vựng tiếng Anh"
        verbose_name_plural = "Từ vựng tiếng Anh"
        ordering = ["en_word"]

    def __str__(self):
        return self.en_word


class EnglishVocabularyExample(models.Model):
    """
    Nhiều câu ví dụ cho từ vựng tiếng Anh (EN + VI).
    """
    vocab = models.ForeignKey(
        EnglishVocabulary,
        on_delete=models.CASCADE,
        related_name="examples",
    )
    order = models.PositiveIntegerField(default=0)
    en = models.TextField("Câu ví dụ tiếng Anh")
    vi = models.TextField("Dịch tiếng Việt", blank=True)
    
    # New fields for enhanced example data
    sentence_marked = models.TextField(
        "Câu ví dụ có đánh dấu",
        blank=True,
        help_text="Câu ví dụ với từ vựng được đánh dấu (ví dụ: ⟦word⟧)",
    )
    sentence_en = models.TextField(
        "Câu ví dụ tiếng Anh (plain)",
        blank=True,
        help_text="Câu ví dụ tiếng Anh không có đánh dấu",
    )
    context = models.CharField(
        "Context",
        max_length=200,
        blank=True,
        help_text="Ngữ cảnh sử dụng (ví dụ: system update, order processing)",
    )
    word_count = models.PositiveIntegerField(
        "Word Count",
        null=True,
        blank=True,
        help_text="Số từ trong câu ví dụ",
    )

    audio_us = models.FileField(
        "Audio ví dụ (US)",
        upload_to=en_example_audio_us_upload_to,
        null=True,
        blank=True,
        help_text="Audio cho câu ví dụ giọng US (optional).",
    )
    audio_uk = models.FileField(
        "Audio ví dụ (UK)",
        upload_to=en_example_audio_uk_upload_to,
        null=True,
        blank=True,
        help_text="Audio cho câu ví dụ giọng UK (optional).",
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Ví dụ EN"
        verbose_name_plural = "Ví dụ EN"

    def __str__(self):
        return f"EN Example for {self.vocab_id} ({self.order})"

class VocabularyExample(models.Model):
    """
    Example sentences for a vocabulary word (JP + VI).
    Using a separate model makes it easy to add/edit multiple examples in admin.
    """
    vocab = models.ForeignKey(
        Vocabulary,
        on_delete=models.CASCADE,
        related_name="examples",
    )
    order = models.PositiveIntegerField(default=0)
    jp = models.TextField("Ví dụ tiếng Nhật")
    vi = models.TextField("Dịch tiếng Việt", blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Ví dụ"
        verbose_name_plural = "Ví dụ"

    def __str__(self):
        return f"Example for {self.vocab_id} ({self.order})"


class FixedPhrase(models.Model):
    """
    Cụm từ cố định / idiom / collocation.
    Tách riêng khỏi Vocabulary để dễ quản lý nội dung dài và nhiều ví dụ.
    """
    jp_text = models.CharField("Cụm từ (JP)", max_length=200)
    jp_kana = models.CharField("Hiragana/Kana", max_length=200, blank=True)

    vi_meaning = models.CharField("Nghĩa tiếng Việt", max_length=255, blank=True)
    en_meaning = models.CharField("Meaning (English)", max_length=255, blank=True)

    notes = models.TextField("Ghi chú / giải thích", blank=True)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(
        "Đã kiểm tra",
        default=False,
        help_text="Tick khi bạn đã rà soát & sửa đúng dữ liệu cụm từ trong admin.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cụm từ cố định"
        verbose_name_plural = "Cụm từ cố định"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.jp_text


class FixedPhraseExample(models.Model):
    phrase = models.ForeignKey(
        FixedPhrase,
        on_delete=models.CASCADE,
        related_name="examples",
    )
    order = models.PositiveIntegerField(default=0)
    jp = models.TextField("Ví dụ tiếng Nhật")
    vi = models.TextField("Dịch tiếng Việt", blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Ví dụ cụm từ"
        verbose_name_plural = "Ví dụ cụm từ"

    def __str__(self):
        return f"Phrase example {self.phrase_id} ({self.order})"


class FsrsCardState(models.Model):
    """
    Trạng thái FSRS cho từng cặp (user, từ vựng).
    card_json: state nội bộ của FSRS.Card (stability, difficulty, due,...)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fsrs_cards",
    )
    vocab = models.ForeignKey(
        Vocabulary,
        on_delete=models.CASCADE,
        related_name="fsrs_states",
    )

    card_json = models.JSONField()
    due = models.DateTimeField(default=timezone.now)
    last_reviewed = models.DateTimeField(null=True, blank=True)

    # === Thống kê thêm ===
    total_reviews = models.PositiveIntegerField(default=0)
    successful_reviews = models.PositiveIntegerField(default=0)
    last_rating = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ("user", "vocab")
        verbose_name = "Trạng thái FSRS"
        verbose_name_plural = "Trạng thái FSRS"

    def __str__(self):
        return f"{self.user} - {self.vocab} (due: {self.due})"

    @property
    def progress_percent(self) -> int:
        """
        Ước lượng retrievability (khả năng nhớ lại) theo chuẩn FSRS.
        Giống như Anki hiển thị "Average Retrievability" cho từng card.
        
        Công thức: R(t) = e^(-t/S × ln(0.9))
        - t: thời gian từ lần review gần nhất (days)
        - S: stability từ FSRS (days)
        - 0.9: retrievability tại thời điểm due (chuẩn FSRS)
        """
        if self.total_reviews == 0:
            return 0

        card_data = json.loads(self.card_json) if isinstance(self.card_json, str) else self.card_json
        
        # Lấy stability từ FSRS (số ngày để retention = 90%)
        stability = card_data.get('stability', 0.0)
        
        if stability <= 0 or not self.last_reviewed:
            # Card mới hoặc chưa có dữ liệu đủ
            return 50
        
        # Tính elapsed time (t) từ lần review gần nhất
        now = timezone.now()
        elapsed_days = (now - self.last_reviewed).total_seconds() / 86400
        
        # FSRS retrievability formula: R(t) = e^(-t/S × ln(0.9))
        # Đây là công thức chính xác mà Anki/FSRS sử dụng
        try:
            retrievability = math.exp((-elapsed_days / stability) * math.log(0.9))
        except (ValueError, ZeroDivisionError, OverflowError):
            retrievability = 0.5
        
        # Clamp trong khoảng hợp lý (0-100%)
        retrievability = max(0.0, min(retrievability, 1.0))
        
        return int(retrievability * 100)


class FsrsCardStateEn(models.Model):
    """
    Trạng thái FSRS cho từng cặp (user, EnglishVocabulary).
    Tách riêng để không ảnh hưởng bảng tiếng Nhật hiện có.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fsrs_cards_en",
    )
    vocab = models.ForeignKey(
        EnglishVocabulary,
        on_delete=models.CASCADE,
        related_name="fsrs_states_en",
    )

    card_json = models.JSONField()
    due = models.DateTimeField(default=timezone.now)
    last_reviewed = models.DateTimeField(null=True, blank=True)

    total_reviews = models.PositiveIntegerField(default=0)
    successful_reviews = models.PositiveIntegerField(default=0)
    last_rating = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ("user", "vocab")
        verbose_name = "FSRS EN"
        verbose_name_plural = "FSRS EN"

    def __str__(self):
        return f"{self.user} - {self.vocab} (due: {self.due})"
