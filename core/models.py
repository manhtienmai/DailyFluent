from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth.models import User


class Course(models.Model):
    """
    Khóa học tối giản: chỉ cần xuất hiện để gán vocab/grammar vào.
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(
        upload_to="courses/",
        blank=True,
        null=True,
        help_text="Ảnh đại diện cho khóa học"
    )
    description = models.TextField(
        blank=True,
        help_text="Mô tả ngắn về khóa học"
    )

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Section(models.Model):
    """
    Section/Part trong 1 Course.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["course__order", "order", "title"]
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        unique_together = ("course", "title")

    def __str__(self):
        return f"{self.course.title} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.course.title}-{self.title}")[:240]
        super().save(*args, **kwargs)


class Lesson(models.Model):
    """
    Bài học tối giản. Thuộc 1 Section (optional để migrate dữ liệu cũ).
    """
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    content = models.TextField(
        blank=True,
        help_text="Nội dung bài học (HTML). Hỗ trợ formatting với rich text editor."
    )

    class Meta:
        ordering = ["section__course__order", "section__order", "order", "title"]
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        unique_together = ("section", "title")

    def __str__(self):
        if self.section_id:
            return f"{self.section.course.title} — {self.section.title} — {self.title}"
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.title
            if self.section_id:
                base = f"{self.section.course.title}-{self.section.title}-{self.title}"
            self.slug = slugify(base)[:240]
        super().save(*args, **kwargs)


class DictationExercise(models.Model):
    """
    Bài tập nghe chép chính tả với audio và timestamp.
    Có thể liên kết với Lesson hoặc độc lập.
    """
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dictation_exercises",
        help_text="Bài tập này thuộc lesson nào (optional)"
    )
    title = models.CharField(max_length=200, help_text="Tiêu đề bài tập")
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Mô tả bài tập")
    
    # Audio file
    audio_file = models.FileField(
        upload_to="dictation/audio/",
        help_text="File audio cho bài dictation"
    )
    audio_duration = models.FloatField(
        null=True,
        blank=True,
        help_text="Độ dài audio (giây)"
    )
    
    # Transcript đầy đủ (để so sánh)
    full_transcript = models.TextField(
        help_text="Transcript đầy đủ của audio (để so sánh với câu trả lời)"
    )
    
    # Settings
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="intermediate"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Dictation Exercise"
        verbose_name_plural = "Dictation Exercises"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.title
            if self.lesson_id:
                base = f"{self.lesson.section.course.title}-{self.lesson.title}-{self.title}"
            self.slug = slugify(base)[:240]
        super().save(*args, **kwargs)


class DictationSegment(models.Model):
    """
    Các đoạn/câu trong bài dictation với timestamp.
    Mỗi segment có start_time và end_time để phát audio từng đoạn.
    """
    exercise = models.ForeignKey(
        DictationExercise,
        on_delete=models.CASCADE,
        related_name="segments"
    )
    order = models.PositiveIntegerField(
        help_text="Thứ tự segment trong bài"
    )
    
    # Timestamp (giây)
    start_time = models.FloatField(
        help_text="Thời điểm bắt đầu segment (giây)"
    )
    end_time = models.FloatField(
        help_text="Thời điểm kết thúc segment (giây)"
    )
    
    # Text của segment (đáp án đúng)
    correct_text = models.TextField(
        help_text="Text đúng của segment này"
    )
    
    # Hint (optional)
    hint = models.TextField(
        blank=True,
        help_text="Gợi ý cho segment này (optional)"
    )
    
    class Meta:
        ordering = ["exercise", "order"]
        unique_together = ("exercise", "order")
        verbose_name = "Dictation Segment"
        verbose_name_plural = "Dictation Segments"
    
    def __str__(self):
        return f"{self.exercise.title} - Segment {self.order}"
    
    @property
    def duration(self):
        """Độ dài segment (giây)"""
        return self.end_time - self.start_time


class DictationProgress(models.Model):
    """
    Tiến độ luyện tập dictation cho từng user/bài.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dictation_progresses",
    )
    exercise = models.ForeignKey(
        DictationExercise,
        on_delete=models.CASCADE,
        related_name="progresses",
    )
    current_segment = models.PositiveIntegerField(default=0)
    total_segments = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "exercise")
        verbose_name = "Dictation Progress"
        verbose_name_plural = "Dictation Progresses"

    @property
    def percent(self) -> float:
        if self.total_segments <= 0:
            return 0.0
        return min(100.0, max(0.0, (self.current_segment / self.total_segments) * 100))

    def __str__(self):
        return f"{self.user} - {self.exercise} ({self.percent:.1f}%)"


class Enrollment(models.Model):
    """
    Theo dõi người dùng đã đăng ký khóa học nào.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.PositiveIntegerField(
        default=0,
        help_text="Phần trăm hoàn thành khóa học (0-100)"
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Lần truy cập khóa học gần nhất"
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-enrolled_at"]
        unique_together = ("user", "course")
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"


class ExamGoal(models.Model):
    """
    Mục tiêu kỳ thi của người dùng.
    """
    EXAM_TYPE_CHOICES = [
        ("TOEIC", "TOEIC"),
        ("IELTS", "IELTS"),
        ("JLPT_N5", "JLPT N5"),
        ("JLPT_N4", "JLPT N4"),
        ("JLPT_N3", "JLPT N3"),
        ("JLPT_N2", "JLPT N2"),
        ("JLPT_N1", "JLPT N1"),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="exam_goal"
    )
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default="TOEIC",
        help_text="Loại kỳ thi"
    )
    target_score = models.PositiveIntegerField(
        default=600,
        help_text="Điểm mục tiêu"
    )
    exam_date = models.DateField(
        null=True,
        blank=True,
        help_text="Ngày dự kiến thi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Exam Goal"
        verbose_name_plural = "Exam Goals"

    def __str__(self):
        return f"{self.user.username} - {self.exam_type} - {self.target_score}"

    @property
    def days_until_exam(self):
        """Số ngày còn lại đến ngày thi"""
        if not self.exam_date:
            return None
        from django.utils import timezone
        today = timezone.localdate()
        delta = self.exam_date - today
        return max(0, delta.days)
