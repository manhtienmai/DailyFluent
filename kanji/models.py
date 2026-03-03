from django.conf import settings
from django.db import models
from django.utils import timezone


class KanjiLesson(models.Model):
    """Bài học Kanji trong một cấp JLPT."""

    JLPT_CHOICES = [
        ('N5', 'N5'),
        ('N4', 'N4'),
        ('N3', 'N3'),
        ('N2', 'N2'),
        ('N1', 'N1'),
        ('BT', '214 Bộ thủ'),
    ]

    jlpt_level = models.CharField(
        "Cấp JLPT", max_length=3, choices=JLPT_CHOICES, default='N5'
    )
    lesson_number = models.PositiveIntegerField("Số bài")
    topic = models.CharField("Chủ đề bài học", max_length=200)
    order = models.PositiveIntegerField("Thứ tự hiển thị", default=0)

    class Meta:
        verbose_name = "Bài học Kanji"
        verbose_name_plural = "Bài học Kanji"
        ordering = ['jlpt_level', 'order', 'lesson_number']
        unique_together = [('jlpt_level', 'lesson_number')]

    def __str__(self):
        return f"[{self.jlpt_level}] Bài {self.lesson_number}: {self.topic}"


class Kanji(models.Model):
    """Một Hán tự đơn."""

    char = models.CharField("Hán tự", max_length=1, unique=True)
    lesson = models.ForeignKey(
        KanjiLesson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kanjis',
        verbose_name="Bài học",
    )
    order = models.PositiveIntegerField("Thứ tự trong bài", default=0)

    sino_vi = models.CharField("Âm Hán Việt", max_length=50, blank=True)
    keyword = models.CharField(
        "Keyword", max_length=100, blank=True,
        help_text="Từ khóa để nhớ nghĩa, vd: Sun, Moon, Gold …"
    )
    onyomi = models.CharField("Âm on", max_length=100, blank=True)
    kunyomi = models.CharField("Âm kun", max_length=100, blank=True)
    meaning_vi = models.CharField("Nghĩa tiếng Việt", max_length=200, blank=True)
    strokes = models.PositiveIntegerField("Số nét", null=True, blank=True)
    note = models.TextField("Ghi chú / câu chuyện nhớ", blank=True)
    formation = models.CharField(
        "Phương pháp hình thành",
        max_length=500, blank=True,
        help_text="VD: Hình thanh: 糸(ý: sợi chỉ) + 泉(âm: セン) → tuyến, dây"
    )

    class Meta:
        verbose_name = "Hán tự"
        verbose_name_plural = "Hán tự"
        ordering = ['lesson', 'order', 'char']

    def __str__(self):
        return f"{self.char} ({self.sino_vi or self.keyword or '?'})"

    @property
    def jlpt_level(self):
        return self.lesson.jlpt_level if self.lesson else ''


class KanjiVocab(models.Model):
    """Từ vựng phổ biến chứa một Hán tự, hiển thị trong trang chi tiết."""

    kanji = models.ForeignKey(
        Kanji,
        on_delete=models.CASCADE,
        related_name='vocab_examples',
        verbose_name="Hán tự",
    )
    word = models.CharField("Từ vựng", max_length=100)
    reading = models.CharField("Cách đọc (hiragana)", max_length=200, blank=True)
    meaning = models.CharField("Nghĩa tiếng Việt", max_length=200, blank=True)
    priority = models.PositiveIntegerField(
        "Ưu tiên", default=0,
        help_text="Số nhỏ hơn hiển thị trước (0 = ưu tiên cao nhất)"
    )
    # Optional link to vocab app
    vocabulary = models.ForeignKey(
        'vocab.Vocabulary',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='kanji_vocab_examples',
        verbose_name="Liên kết Vocabulary",
    )
    jlpt_level = models.CharField(
        "Cấp JLPT",
        max_length=5,
        blank=True,
        default="",
        help_text="N5, N4, N3, N2, N1",
    )

    class Meta:
        verbose_name = "Từ vựng mẫu Kanji"
        verbose_name_plural = "Từ vựng mẫu Kanji"
        ordering = ['priority', 'id']
        unique_together = [('kanji', 'word')]

    def __str__(self):
        parts = [self.word]
        if self.reading:
            parts.append(f"({self.reading})")
        if self.meaning:
            parts.append(f"– {self.meaning}")
        return ' '.join(parts)


class UserKanjiProgress(models.Model):
    """Theo dõi tiến trình luyện viết Kanji của từng user."""

    STATUS_LEARNING = "learning"
    STATUS_MASTERED = "mastered"
    STATUS_CHOICES = [
        (STATUS_LEARNING, "Đang học"),
        (STATUS_MASTERED, "Đã thuộc"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="kanji_progress",
        verbose_name="Người dùng",
    )
    kanji = models.ForeignKey(
        Kanji,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name="Hán tự",
    )
    status = models.CharField(
        "Trạng thái",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_LEARNING,
    )
    correct_streak = models.PositiveIntegerField("Chuỗi đúng", default=0)
    last_practiced = models.DateTimeField("Lần cuối luyện", null=True, blank=True)

    class Meta:
        unique_together = ("user", "kanji")
        verbose_name = "Tiến trình học Hán tự"
        verbose_name_plural = "Tiến trình học Hán tự"
        ordering = ["-last_practiced"]

    def __str__(self):
        return f"{self.user} – {self.kanji.char} ({self.status})"

    def record_attempt(self, passed: bool) -> None:
        """Cập nhật streak và status sau một lần luyện viết."""
        if passed:
            self.correct_streak += 1
            if self.correct_streak >= 5:
                self.status = self.STATUS_MASTERED
        else:
            self.correct_streak = 0
            self.status = self.STATUS_LEARNING
        self.last_practiced = timezone.now()
        self.save(update_fields=["status", "correct_streak", "last_practiced"])


class KanjiQuizQuestion(models.Model):
    """Pre-generated quiz question for a single Kanji character."""

    class QuestionType(models.TextChoices):
        MEANING = 'meaning', 'Nghĩa'
        READING = 'reading', 'Cách đọc'
        KANJI = 'kanji', 'Hán tự'

    kanji = models.ForeignKey(
        Kanji,
        on_delete=models.CASCADE,
        related_name='quiz_questions',
        verbose_name="Hán tự",
    )
    question_type = models.CharField(
        "Loại câu hỏi",
        max_length=10,
        choices=QuestionType.choices,
    )
    correct_answer = models.CharField("Đáp án đúng", max_length=255)
    distractors = models.JSONField(
        "Đáp án nhiễu",
        default=list,
        help_text='["wrong1", "wrong2", "wrong3"]',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('kanji', 'question_type')
        verbose_name = "Câu hỏi Quiz Kanji"
        verbose_name_plural = "Câu hỏi Quiz Kanji"

    def __str__(self):
        return f"{self.kanji.char} – {self.question_type}: {self.correct_answer}"
