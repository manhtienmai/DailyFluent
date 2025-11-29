from django.db import models
from django.conf import settings
from django.utils import timezone


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

    example_jp = models.TextField("Ví dụ tiếng Nhật", blank=True)
    example_vi = models.TextField("Nghĩa câu ví dụ", blank=True)

    # Liên kết các Hán tự đơn xuất hiện trong từ này, ví dụ 割合 -> {割, 合}
    kanji_chars = models.ManyToManyField(
        "kanji.Kanji",              # <--- chú ý: "kanji.Kanji" (app.model)
        related_name="vocabulary_items",
        blank=True,
        help_text="Các Hán tự có mặt trong từ vựng này",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Từ vựng"
        verbose_name_plural = "Từ vựng"
        ordering = ['jp_kana']

    def __str__(self):
        return f"{self.jp_kana} - {self.vi_meaning}"

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
        % nhớ “thực tế” hơn:
        - Dựa trên tỉ lệ Good/Easy.
        - Giới hạn max theo số lần review (mới học không lên 100% ngay).
        - Phạt nếu lần cuối là Again/Hard.
        """
        if self.total_reviews == 0:
            return 0

        # Tỉ lệ Good/Easy trên tất cả các lần review
        base_ratio = self.successful_reviews / self.total_reviews

        # Giới hạn max theo số lần review
        #  1–2 lần: max 50%
        #  3–4 lần: max 75%
        #  >=5 lần: max 100%
        if self.total_reviews < 3:
            cap = 0.5
        elif self.total_reviews < 5:
            cap = 0.75
        else:
            cap = 1.0

        ratio = min(base_ratio, cap)

        # Phạt nếu lần gần nhất là Again/Hard
        if self.last_rating == "again":
            ratio *= 0.3
        elif self.last_rating == "hard":
            ratio *= 0.7

        # Đảm bảo nằm trong 0–100
        ratio = max(0.0, min(ratio, 1.0))
        return int(ratio * 100)

