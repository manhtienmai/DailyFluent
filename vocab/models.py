from django.db import models
from django.conf import settings
from django.utils import timezone
import json
import math


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
