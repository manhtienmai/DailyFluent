from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class GrammarLevel(models.TextChoices):
    N1 = "N1", "N1"
    N2 = "N2", "N2"
    N3 = "N3", "N3"
    N4 = "N4", "N4"
    N5 = "N5", "N5"


class GrammarBook(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    level = models.CharField(max_length=2, choices=GrammarLevel.choices, default=GrammarLevel.N5)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="grammar/books/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["level", "title"]
        verbose_name = "Sách ngữ pháp"
        verbose_name_plural = "Sách ngữ pháp"

    def __str__(self):
        return f"{self.title} ({self.level})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class GrammarPoint(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    level = models.CharField(max_length=2, choices=GrammarLevel.choices, default=GrammarLevel.N5)
    reading = models.CharField(max_length=255, blank=True, help_text="Furigana / cách đọc")
    meaning_vi = models.CharField(max_length=500, blank=True, help_text="Nghĩa tiếng Việt ngắn")
    formation = models.CharField(max_length=500, blank=True, help_text="Cấu trúc: N + に反して")
    summary = models.TextField(blank=True, help_text="Mô tả ngắn / ý chính")
    explanation = models.TextField(blank=True, help_text="Giải thích chi tiết")
    details = models.TextField(blank=True, help_text="Giải thích chi tiết (plain text hoặc Markdown)")
    notes = models.TextField(blank=True, null=True, help_text="Lưu ý thêm")
    examples = models.TextField(blank=True, help_text="Ví dụ, mỗi dòng một câu")
    book = models.ForeignKey(
        GrammarBook,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grammar_points",
    )
    order = models.PositiveIntegerField(default=0, help_text="Thứ tự trong sách/level")
    # Gán theo khóa/bài (optional)
    course = models.ForeignKey(
        "core.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grammar_points",
    )
    section = models.ForeignKey(
        "core.Section",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grammar_points",
    )
    lesson = models.ForeignKey(
        "core.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grammar_points",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["level", "order", "title"]
        verbose_name = "Ngữ pháp"
        verbose_name_plural = "Ngữ pháp"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_exercise_sets(self):
        return self.exercise_sets.filter(is_active=True)


class GrammarExample(models.Model):
    grammar_point = models.ForeignKey(
        GrammarPoint,
        on_delete=models.CASCADE,
        related_name="structured_examples",
    )
    sentence_jp = models.TextField(help_text="Câu tiếng Nhật")
    sentence_vi = models.TextField(help_text="Dịch tiếng Việt")
    highlight_start = models.PositiveIntegerField(null=True, blank=True, help_text="Vị trí bắt đầu highlight (char index)")
    highlight_end = models.PositiveIntegerField(null=True, blank=True, help_text="Vị trí kết thúc highlight (char index)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Ví dụ ngữ pháp"
        verbose_name_plural = "Ví dụ ngữ pháp"

    def __str__(self):
        return f"{self.grammar_point.title}: {self.sentence_jp[:40]}"

    def highlighted_jp(self):
        """Return sentence_jp with highlight markers if positions set."""
        if self.highlight_start is not None and self.highlight_end is not None:
            s = self.sentence_jp
            return (
                s[: self.highlight_start]
                + "<mark>"
                + s[self.highlight_start : self.highlight_end]
                + "</mark>"
                + s[self.highlight_end :]
            )
        return self.sentence_jp


class GrammarExerciseSet(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    grammar_point = models.ForeignKey(
        GrammarPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exercise_sets",
    )
    book = models.ForeignKey(
        GrammarBook,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exercise_sets",
    )
    level = models.CharField(max_length=2, choices=GrammarLevel.choices, default=GrammarLevel.N5)
    description = models.TextField(blank=True)
    question_count = models.PositiveIntegerField(default=0, help_text="Tự cập nhật")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["level", "title"]
        verbose_name = "Bộ bài tập"
        verbose_name_plural = "Bộ bài tập"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def update_question_count(self):
        self.question_count = self.questions.count()
        self.save(update_fields=["question_count"])


class GrammarQuestion(models.Model):
    MCQ = "MCQ"
    SENTENCE_ORDER = "SENTENCE_ORDER"
    QUESTION_TYPE_CHOICES = [
        (MCQ, "Trắc nghiệm (MCQ)"),
        (SENTENCE_ORDER, "Xếp thứ tự câu (★)"),
    ]

    exercise_set = models.ForeignKey(
        GrammarExerciseSet,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default=MCQ)
    order = models.PositiveIntegerField(default=0)

    # Chung
    question_text = models.TextField(blank=True, help_text="Phần câu hỏi (dấu ___ cho chỗ trống)")
    explanation_jp = models.TextField(blank=True, help_text="Giải thích đáp án (tiếng Nhật)")
    explanation_vi = models.TextField(blank=True, help_text="Giải thích đáp án (tiếng Việt)")

    # MCQ-only
    choices = models.JSONField(
        null=True, blank=True,
        help_text='[{"key":"1","text":"〜ので"}, {"key":"2","text":"〜ながら"}, ...]'
    )
    correct_answer = models.CharField(
        max_length=50, blank=True,
        help_text='MCQ: "1"|"2"|"3"|"4"'
    )

    # SENTENCE_ORDER (★)-only
    sentence_prefix = models.CharField(max_length=255, blank=True, help_text="Phần đầu câu: '彼女は'")
    sentence_suffix = models.CharField(max_length=255, blank=True, help_text="Phần cuối câu: '人だ。'")
    tokens = models.JSONField(
        null=True, blank=True,
        help_text='["きれいな","とても","優しくて","そして"]'
    )
    correct_order = models.JSONField(
        null=True, blank=True,
        help_text='[1,0,2,3] — index vào tokens cho box 1,2,3,4'
    )
    star_position = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Box nào có ★ (1-4)"
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Câu hỏi"
        verbose_name_plural = "Câu hỏi"

    def __str__(self):
        return f"[{self.question_type}] {self.question_text[:60] or 'Câu hỏi #' + str(self.order)}"

    def get_star_answer(self):
        """Return the correct token for the ★ box."""
        if self.question_type == self.SENTENCE_ORDER and self.tokens and self.correct_order and self.star_position:
            idx = self.correct_order[self.star_position - 1]
            return self.tokens[idx]
        return None


class UserGrammarProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="grammar_progress")
    grammar_point = models.ForeignKey(GrammarPoint, on_delete=models.CASCADE, related_name="user_progress")
    best_score = models.PositiveIntegerField(default=0, help_text="% đúng tốt nhất")
    studied_at = models.DateTimeField(null=True, blank=True, help_text="Lần đầu xem lý thuyết")
    last_practiced = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "grammar_point")
        verbose_name = "Tiến độ ngữ pháp"
        verbose_name_plural = "Tiến độ ngữ pháp"

    def __str__(self):
        return f"{self.user} – {self.grammar_point} ({self.best_score}%)"


class GrammarAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="grammar_attempts")
    exercise_set = models.ForeignKey(GrammarExerciseSet, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        verbose_name = "Lần làm bài"
        verbose_name_plural = "Lần làm bài"

    def __str__(self):
        return f"{self.user} – {self.exercise_set} ({self.score}/{self.total})"

    @property
    def percentage(self):
        if self.total:
            return round(self.score / self.total * 100)
        return 0


class GrammarQuestionAnswer(models.Model):
    attempt = models.ForeignKey(GrammarAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(GrammarQuestion, on_delete=models.CASCADE, related_name="answers")
    user_answer = models.JSONField(help_text="MCQ: key string; SENTENCE_ORDER: [idx,idx,idx,idx]")
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Câu trả lời"
        verbose_name_plural = "Câu trả lời"

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} – Q#{self.question_id}"


class FsrsCardStateGrammar(models.Model):
    """
    FSRS card state for grammar flashcards.
    Same pattern as FsrsCardStateEn but linked to GrammarPoint.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fsrs_states_grammar')
    grammar_point = models.ForeignKey(GrammarPoint, on_delete=models.CASCADE, related_name='fsrs_states')

    # FSRS core data (JSON dump of FSRS Card object)
    card_data = models.JSONField(default=dict)

    # Denormalized fields for faster querying
    state = models.IntegerField(default=0, db_index=True, help_text="0=New, 1=Learning, 2=Review, 3=Relearning")
    due = models.DateTimeField(null=True, blank=True, db_index=True)
    last_review = models.DateTimeField(null=True, blank=True)

    # Stats
    total_reviews = models.PositiveIntegerField(default=0)
    successful_reviews = models.PositiveIntegerField(default=0)
    last_review_log = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('user', 'grammar_point')
        verbose_name = "FSRS Card State (Grammar)"
        verbose_name_plural = "FSRS Card States (Grammar)"

    def __str__(self):
        return f"{self.user.username} - {self.grammar_point.title} (State: {self.state})"
