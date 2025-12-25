from django.conf import settings
from django.db import models
from django.utils import timezone
from utils.slug import to_romaji_slug


class ExamLevel(models.TextChoices):
    N5 = "N5", "JLPT N5"
    N4 = "N4", "JLPT N4"
    N3 = "N3", "JLPT N3"
    N2 = "N2", "JLPT N2"
    N1 = "N1", "JLPT N1"


class ExamCategory(models.TextChoices):
    MOJIGOI = "MOJI", "Moji・Goi"
    BUNPOU = "BUN", "Bunpou"
    DOKKAI = "DOKKAI", "Dokkai"
    CHOUKAI = "CHOUKAI", "Choukai"
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


# ============
#  ĐỌC HIỂU
# ============

class ReadingFormat(models.TextChoices):
    """Kiểu unit đọc hiểu (1 passage + các câu hỏi)."""
    SHORT = "SHORT", "短文"          # đoạn ngắn
    MIDDLE = "MIDDLE", "中文"        # đoạn trung văn
    LONG = "LONG", "長文"            # trường văn
    MAIL = "MAIL", "メール文"        # email / tin nhắn
    INFO = "INFO", "情報検索"        # đọc hiểu tìm kiếm thông tin


# ======================
#  EXAM BOOK / TEMPLATE
# ======================

class ExamBook(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=120, blank=True)
    level = models.CharField(max_length=2, choices=ExamLevel.choices)
    category = models.CharField(max_length=10, choices=ExamCategory.choices)

    description = models.TextField(blank=True)

    # Ảnh bìa sách (optional)
    cover_image = models.ImageField(
        upload_to="exam/book_covers/",
        blank=True,
        null=True,
        help_text="Ảnh bìa sách hiển thị trên UI (tùy chọn).",
    )

    # Dùng cho UI filter: tổng số bài (day / pattern) trong sách
    total_lessons = models.PositiveIntegerField(
        default=0,
        help_text="Số bài / ngày (optional)",
    )

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = to_romaji_slug(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ExamTemplate(models.Model):
    """
    1 bài test / set bài tập.

    - Có thể thuộc 1 ExamBook (bài trong sách)
    - Hoặc đứng 1 mình: đề MOGI / bài lẻ.

    Với DOKKAI:
    - MỖI ExamTemplate chính là 1 “unit đọc hiểu”:
        + 1 ReadingPassage (order=1) = đoạn văn
        + N ExamQuestion gắn với passage đó
    """

    # Liên kết (optional) tới book (nguồn, ví dụ Power Drill N2 Dokkai)
    book = models.ForeignKey(
        ExamBook,
        related_name="tests",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Để trống nếu là bài lẻ / đề MOGI",
    )

    # Tên bài / unit
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=120, blank=True)

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

    # ===== Định nghĩa rõ unit đọc hiểu =====
    # Chỉ dùng cho category = DOKKAI hoặc MIX
    # 1 template = 1 unit đọc hiểu nếu reading_format != "" và có đúng 1 passage chính (order=1).
    reading_format = models.CharField(
        max_length=10,
        choices=ReadingFormat.choices,
        blank=True,
        help_text="Dùng cho đọc hiểu: 短文 / 中文 / 長文 / メール / 情報検索",
    )
    dokkai_skill = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tag skill đọc hiểu (VD: 内容理解 / 情報検索 / 主旨把握...)",
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

    def _slug_base(self) -> str:
        # gộp title sách + title bài để slug dễ đọc và ít trùng
        if self.book:
            return f"{self.book.title} {self.title}"
        return self.title

    def save(self, *args, **kwargs):
        """
        - Khi tạo mới (pk is None) hoặc slug đang rỗng → generate slug từ romaji.
        - Đảm bảo unique: nếu trùng thì thêm -2, -3, ...
        - Không tự động đổi slug khi update (chỉ set lúc tạo).
        """
        # Tạo slug khi tạo mới hoặc khi slug đang trống
        if not self.pk or not self.slug:
            base = self._slug_base()
            self.slug = to_romaji_slug(base)

        # Đảm bảo slug là unique (nếu lỡ trùng do title giống nhau)
        original = self.slug
        counter = 2

        qs = self.__class__.objects.filter(slug=self.slug)
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        while qs.exists():
            self.slug = f"{original}-{counter}"
            counter += 1
            qs = self.__class__.objects.filter(slug=self.slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)

        return super().save(*args, **kwargs)

    def __str__(self):
        if self.book:
            return f"{self.book.title} – {self.title}"
        return self.title

    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def is_reading_unit(self) -> bool:
        """
        Helper: cho UI/filter.
        1 template là unit đọc hiểu nếu:
        - category là DOKKAI hoặc MIX
        - có reading_format
        """
        return self.category in {ExamCategory.DOKKAI, ExamCategory.MIX} and bool(
            self.reading_format
        )


class ReadingPassage(models.Model):
    """
    Đoạn văn gắn với 1 ExamTemplate.

    Với đọc hiểu:
    - Bạn nên thiết kế 1 template chỉ có 1 passage chính (order=1) để đúng nghĩa 1 unit.
    - Nếu thật sự cần nhiều passage (multi-passage set) thì vẫn hỗ trợ, nhưng
      concept “unit đọc hiểu” nên map 1-1 với ExamTemplate.
    """
    template = models.ForeignKey(
        ExamTemplate,
        related_name="passages",
        on_delete=models.CASCADE,
        help_text="Passage thuộc bài test nào",
    )
    order = models.PositiveIntegerField(default=1, help_text="Thứ tự passage trong bài")
    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(help_text="Đoạn văn JP đầy đủ")

    image = models.ImageField(
        upload_to="exam/dokkai_passages/",
        blank=True,
        null=True,
        help_text="Ảnh poster / bảng thông tin cho dokkai (nếu có).",
    )
    # Chỗ này tùy nhu cầu: audio, chú thích, highlight...
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["template_id", "order", "id"]

    def __str__(self):
        return self.title or f"Passage {self.order} – {self.template}"


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

    # Nếu là dokkai thì bắt buộc có passage;
    # nếu là moji/goi bình thường thì để trống.
    passage = models.ForeignKey(
        ReadingPassage,
        related_name="questions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Nếu là câu dokkai thì gắn với passage tương ứng",
    )

    audio = models.FileField(
        upload_to="exam/listening/",
        blank=True,
        null=True,
        help_text="File audio cho câu hỏi nghe (nếu có).",
    )
    audio_meta = models.JSONField(
        default=dict,
        blank=True,
        help_text='VD: {"cd": "CD1", "track": "03"}',
    )

    order = models.PositiveIntegerField(default=1)

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )

    # Câu hỏi JP     text = câu hỏi JP, KHÔNG phải passage
    text = models.TextField(
        help_text="Câu hỏi JP. Với sắp xếp câu có thể dùng ( ) (＊) để minh hoạ.",
        blank=True,
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
