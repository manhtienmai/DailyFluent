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
    TOEIC = "TOEIC", "TOEIC"


class ExamCategory(models.TextChoices):
    MOJIGOI = "MOJI", "Moji・Goi"
    BUNPOU = "BUN", "Bunpou"
    DOKKAI = "DOKKAI", "Dokkai"
    CHOUKAI = "CHOUKAI", "Choukai"
    MIX = "MIX", "Mixed"
    LISTENING = "LISTENING", "TOEIC Listening"
    READING = "READING", "TOEIC Reading"
    TOEIC_FULL = "TOEIC_FULL", "TOEIC Full Test"


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
#  TOEIC
# ============

class TOEICPart(models.TextChoices):
    """Các phần của bài thi TOEIC"""
    LISTENING_1 = "L1", "Listening Part 1: Mô tả hình ảnh"
    LISTENING_2 = "L2", "Listening Part 2: Câu hỏi-Đáp án"
    LISTENING_3 = "L3", "Listening Part 3: Hội thoại ngắn"
    LISTENING_4 = "L4", "Listening Part 4: Bài nói ngắn"
    READING_5 = "R5", "Reading Part 5: Điền từ vào câu"
    READING_6 = "R6", "Reading Part 6: Điền từ vào đoạn văn"
    READING_7 = "R7", "Reading Part 7: Đọc hiểu"


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
    level = models.CharField(max_length=10, choices=ExamLevel.choices)
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

    level = models.CharField(max_length=10, choices=ExamLevel.choices)
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

    # ===== TOEIC specific fields =====
    is_full_toeic = models.BooleanField(
        default=False,
        help_text="True nếu là full test TOEIC (200 câu: Listening + Reading)",
    )
    listening_time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=45,
        help_text="Giới hạn thời gian cho phần Listening (phút). Mặc định 45 phút.",
    )
    reading_time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=75,
        help_text="Giới hạn thời gian cho phần Reading (phút). Mặc định 75 phút.",
    )

    # Audio trọn bài (cho Full Test hoặc bài Test lẻ)
    audio_file = models.FileField(
        upload_to="exam/audio/",
        blank=True,
        null=True,
        help_text="File audio trọn bài (dùng cho TOEIC Full Test hoặc bài nghe dài).",
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
    text = models.TextField(help_text="Đoạn văn JP đầy đủ", blank=True)
    instruction = models.TextField(help_text="Hướng dẫn đọc hiểu (optional)", blank=True)
    # Nội dung JSON (ưu tiên render nếu có), cho phép lưu cấu trúc phong phú
    # Ví dụ: {"html": "<p>...</p>"} hoặc {"content": "plain text"} hoặc {"content_segments": [...]}.
    content_json = models.JSONField(default=dict, blank=True)

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


class ReadingPassageImage(models.Model):
    """
    Nhiều ảnh cho 1 passage (đặc biệt hữu ích cho TOEIC Part 6/7: email + bill + schedule...).
    """
    passage = models.ForeignKey(
        ReadingPassage,
        related_name="images",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1, help_text="Thứ tự hiển thị ảnh trong passage")
    image = models.ImageField(
        upload_to="exam/reading_passages/",
        help_text="Ảnh thuộc passage (có thể upload nhiều ảnh).",
    )
    caption = models.CharField(max_length=255, blank=True, help_text="Chú thích (optional)")

    class Meta:
        ordering = ["passage_id", "order", "id"]
        unique_together = ("passage", "order")
        verbose_name = "Reading Passage Image"
        verbose_name_plural = "Reading Passage Images"

    def __str__(self):
        return f"PassageImage #{self.order} – Passage {self.passage_id}"


# ======================
#  LISTENING CONVERSATION (TOEIC)
# ======================

class ListeningConversation(models.Model):
    """
    Hội thoại / Bài nói cho Listening Part 3, 4.
    
    Part 3: 13 đoạn hội thoại, mỗi đoạn 3 câu hỏi
    Part 4: 10 đoạn bài nói, mỗi đoạn 3 câu hỏi
    
    Mỗi đoạn có:
    - 1 file audio
    - Có thể có hình/biểu đồ (optional)
    - Transcript (optional, hiển thị sau khi submit)
    - N câu hỏi (ExamQuestion) gắn với conversation này
    """
    
    template = models.ForeignKey(
        ExamTemplate,
        related_name="listening_conversations",
        on_delete=models.CASCADE,
        help_text="Template chứa đoạn hội thoại này",
    )
    
    toeic_part = models.CharField(
        max_length=2,
        choices=[(TOEICPart.LISTENING_3, "Part 3"), (TOEICPart.LISTENING_4, "Part 4")],
        help_text="Part 3 (hội thoại) hoặc Part 4 (bài nói)",
    )
    
    order = models.PositiveIntegerField(
        default=1,
        help_text="Thứ tự đoạn trong Part (1-13 cho Part 3, 1-10 cho Part 4)",
    )
    
    audio = models.FileField(
        upload_to="exam/toeic/listening/",
        help_text="File audio cho đoạn hội thoại/bài nói",
    )
    
    # Có thể có hình/biểu đồ (optional)
    image = models.ImageField(
        upload_to="exam/toeic/listening_images/",
        blank=True,
        null=True,
        help_text="Hình/biểu đồ kèm theo (nếu có)",
    )
    
    # Context/transcript (optional, để hiển thị sau khi làm xong)
    transcript = models.TextField(
        blank=True,
        help_text="Transcript của đoạn audio (hiển thị sau khi submit)",
    )
    transcript_vi = models.TextField(
        blank=True,
        help_text="Bản dịch tiếng Việt của transcript",
    )
    
    # Structured transcript data (for interactive bilingual display)
    transcript_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Bilingual transcript: {"lines": [{"speaker": "M", "text": "...", "text_vi": "..."}]}',
    )
    
    # Metadata
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text='VD: {"speakers": 2, "topic": "office meeting", "duration_seconds": 45}',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["template_id", "toeic_part", "order", "id"]
        unique_together = ("template", "toeic_part", "order")
        verbose_name = "Listening Conversation"
        verbose_name_plural = "Listening Conversations"
    
    def __str__(self):
        return f"{self.template} – {self.get_toeic_part_display()} – Conversation {self.order}"


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

    # ===== TOEIC specific fields =====
    toeic_part = models.CharField(
        max_length=2,
        choices=TOEICPart.choices,
        blank=True,
        null=True,
        help_text="Phần TOEIC (L1-L4, R5-R7). Để trống nếu không phải TOEIC.",
    )
    
    image = models.ImageField(
        upload_to="exam/toeic/images/",
        blank=True,
        null=True,
        help_text="Hình ảnh cho Listening Part 1 hoặc Reading Part 7 (nếu có).",
    )
    
    listening_conversation = models.ForeignKey(
        "ListeningConversation",
        related_name="questions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Đoạn hội thoại/bài nói cho Listening Part 3, 4 (nếu có).",
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

    # Câu hỏi (text = câu hỏi tiếng Anh/JP)
    text = models.TextField(
        help_text="Câu hỏi. Với sắp xếp câu có thể dùng ( ) (＊) để minh hoạ.",
        blank=True,
    )
    text_vi = models.TextField(
        blank=True,
        help_text="Bản dịch tiếng Việt của câu hỏi",
    )
    
    # Audio transcript for Listening Part 1/2 (single questions)
    audio_transcript = models.TextField(
        blank=True,
        help_text="Transcript của audio (cho Part 1/2)",
    )
    audio_transcript_vi = models.TextField(
        blank=True,
        help_text="Bản dịch tiếng Việt của audio transcript",
    )
    
    explanation_vi = models.TextField(blank=True)
    explanation_json = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "JSON giải thích chi tiết đáp án (dùng cho UI kết quả/giải thích). "
            "Gợi ý schema: meta, correct_option, content_translation, overall_analysis, options_breakdown, vocabulary_extraction."
        ),
    )

    # Data đặc thù từng type
    # - MCQ  : {"choices": [{"key": "1","text":"...","text_vi":"..."}, ...]}
    # - ORDER: {"tokens":  [{"key": "1","text":"..."}, ...]}
    data = models.JSONField(default=dict, blank=True)
    
    # Transcript data for structured bilingual display
    transcript_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Bilingual options/transcript: {"options": [{"label":"A","text":"...","text_vi":"..."}]}',
    )

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
    
    # Metadata để lưu thông tin về mode, selected_parts, time_limit, etc.
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Lưu metadata như mode, selected_parts, time_limit_minutes"
    )

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


# ======================
#  EXAM COMMENT
# ======================

class ExamComment(models.Model):
    """
    Comment/Thảo luận cho đề thi.
    Chỉ hỗ trợ text, không có media.
    """
    template = models.ForeignKey(
        ExamTemplate,
        related_name="comments",
        on_delete=models.CASCADE,
        help_text="Đề thi được comment",
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="exam_comments",
        on_delete=models.CASCADE,
        help_text="User đã comment",
    )
    
    content = models.TextField(
        max_length=2000,
        help_text="Nội dung comment (tối đa 2000 ký tự)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Admin có thể ẩn comment không phù hợp",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["template", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.user.username} – {self.template.title} ({self.created_at.strftime('%Y-%m-%d')})"
