from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


# ======================
#  ENUM / CHOICES
# ======================

class ExamLevel(models.TextChoices):
    N5 = "N5", "JLPT N5"
    N4 = "N4", "JLPT N4"
    N3 = "N3", "JLPT N3"
    N2 = "N2", "JLPT N2"
    N1 = "N1", "JLPT N1"


class ExamCategory(models.TextChoices):
    MOJIGOI = "MOJI", "Moji・Goi"
    BUNPOU = "BUN", "Bunpou"
    MIX = "MIX", "Mixed"


class ExamGroupType(models.TextChoices):
    STANDALONE = "SINGLE", "Bài lẻ / đề MOGI"
    BY_PATTERN = "PATTERN", "Theo dạng câu (Kanji đọc, từ cận nghĩa...)"
    BY_DAY = "DAY", "Học theo ngày (Day 01, Day 02...)"


class QuestionType(models.TextChoices):
    MCQ = "MCQ", "Trắc nghiệm 4 lựa chọn"
    SENTENCE_ORDER = "ORDER", "Sắp xếp câu"
    FILL_BLANK = "FILL", "Điền chỗ trống"
    WORD_PAIR = "PAIR", "Ghép từ"
    NEAR_SYNONYM = "NEAR", "Từ cận nghĩa"
    USAGE = "USAGE", "Cách dùng từ"
    PARAGRAPH = "PARA", "Đoạn văn"


# ======================
#  EXAM BOOK / TEMPLATE
# ======================

class ExamBook(models.Model):
    """1 quyển sách / series, ví dụ:
    - Power Drill Mojigoi N2
    - Power Drill Bunpou N2
    - JLPT MOGI N2
    """

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=2, choices=ExamLevel.choices)
    category = models.CharField(max_length=10, choices=ExamCategory.choices)

    description = models.TextField(blank=True)

    # Dùng cho UI filter: tổng số bài (day / pattern) trong sách
    total_lessons = models.PositiveIntegerField(
        default=0,
        help_text="Số bài / ngày (optional)",
    )

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ExamTemplate(models.Model):
    """1 bài test / set bài tập.

    - Có thể thuộc 1 ExamBook (bài trong sách)
    - Hoặc đứng 1 mình: đề MOGI / bài lẻ.
    """

    # Liên kết (optional) tới book
    book = models.ForeignKey(
        ExamBook,
        related_name="tests",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Để trống nếu là bài lẻ / đề MOGI",
    )

    # Tên bài
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    # Mô tả thêm nếu cần
    description = models.TextField(blank=True)

    level = models.CharField(max_length=2, choices=ExamLevel.choices)
    category = models.CharField(max_length=10, choices=ExamCategory.choices)

    group_type = models.CharField(
        max_length=20,
        choices=ExamGroupType.choices,
        default=ExamGroupType.STANDALONE,
        help_text="Bài lẻ / theo dạng / theo ngày",
    )

    # Dùng để sắp xếp trong sách:
    #   - Nếu group_type = BY_DAY    → lesson_index = day (1..30)
    #   - Nếu group_type = BY_PATTERN→ lesson_index = bài số 1..n trong dạng đó
    lesson_index = models.PositiveIntegerField(default=1)

    # Subtitle hiển thị trên UI: "Day 01 – Học theo ngày", "Bài 01 – Kanji: Cách đọc"
    subtitle = models.CharField(max_length=255, blank=True)

    # Nếu 1 bài chỉ chứa 1 loại câu (thường là vậy)
    main_question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        blank=True,
        help_text="Loại câu chính của bài (nếu đồng nhất)",
    )

    # Giới hạn thời gian
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Giới hạn thời gian (phút). Để trống nếu không giới hạn.",
    )

    # Active / hide
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["book_id", "group_type", "lesson_index", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.title if not self.book else f"{self.book.title}-{self.title}"
            self.slug = slugify(base)
        return super().save(*args, **kwargs)

    def __str__(self):
        if self.book:
            return f"{self.book.title} – {self.title}"
        return self.title

    @property
    def total_questions(self):
        return self.questions.count()
    

# ======================
#  EXAM QUESTION
# ======================

class ExamQuestion(models.Model):
    """1 câu hỏi cụ thể, data flexible bằng JSON."""

    template = models.ForeignKey(
        ExamTemplate,
        related_name="questions",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )

    # Câu hỏi JP
    text = models.TextField(
        help_text="Câu hỏi JP. Với sắp xếp câu có thể dùng ( ) (＊) để minh hoạ."
    )
    explanation_vi = models.TextField(blank=True)

    # Data đặc thù từng type
    # - MCQ  : {"choices": [{"key": "1","text":"..."}, ...]}
    # - ORDER: {"tokens":  [{"key": "1","text":"..."}, ...]}
    data = models.JSONField(default=dict, blank=True)

    # Đáp án đúng:
    # - MCQ  : "3"
    # - ORDER: "3,1,4,2"
    correct_answer = models.CharField(max_length=100)

    # ====== JLPT meta (optional, để giữ được info cũ) ======
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="VD: Power Drill N2 DAY 01",
    )
    mondai = models.CharField(
        max_length=20,
        blank=True,
        help_text="VD: '01', '02'...",
    )
    order_in_mondai = models.PositiveIntegerField(default=1)

    # Liên kết với vocab app hiện tại (giống code cũ)
    vocab_items = models.ManyToManyField(
        "vocab.Vocabulary",
        blank=True,
        related_name="exam_questions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["template_id", "order", "id"]

    def __str__(self):
        return f"{self.template} – Q{self.order}"

    # Helper cho UI MCQ
    @property
    def mcq_choices(self):
        """
        Trả về list choices cho MCQ.
        Mặc định format:
        [
          {"key": "1", "text": "..."},
          {"key": "2", "text": "..."},
          {"key": "3", "text": "..."},
          {"key": "4", "text": "..."},
        ]
        """
        return self.data.get("choices", [])

    @property
    def sentence_tokens(self):
        """Dùng cho sắp xếp câu."""
        return self.data.get("tokens", [])


# ======================
#  ATTEMPT & ANSWER
# ======================

class ExamAttempt(models.Model):
    """1 lần làm bài của user trên 1 ExamTemplate."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "Đang làm"
        SUBMITTED = "submitted", "Đã nộp"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="exam_attempts",
    )
    template = models.ForeignKey(
        ExamTemplate,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)

    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} – {self.template} – {self.started_at:%Y-%m-%d}"

    @property
    def score_percent(self):
        if not self.total_questions:
            return 0
        return round(self.correct_count * 100 / self.total_questions)

    @property
    def rating_label(self):
        if not self.total_questions:
            return "Chưa có"
        ratio = self.correct_count / self.total_questions
        if ratio >= 0.8:
            return "TỐT"
        elif ratio >= 0.6:
            return "TRUNG BÌNH"
        return "CẦN CỐ GẮNG"


class QuestionAnswer(models.Model):
    """Đáp án user cho 1 câu trong 1 lần làm bài."""

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE)

    # raw_answer flexible tuỳ loại câu:
    # - MCQ  : {"selected_key": "3"}
    # - ORDER: {"order": ["3","1","2","4"]}
    raw_answer = models.JSONField(default=dict)

    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"{self.attempt} – {self.question_id}"
