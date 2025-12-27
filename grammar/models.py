from django.db import models
from django.utils.text import slugify


class GrammarLevel(models.TextChoices):
    N1 = "N1", "N1"
    N2 = "N2", "N2"
    N3 = "N3", "N3"
    N4 = "N4", "N4"
    N5 = "N5", "N5"


class GrammarPoint(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    level = models.CharField(max_length=2, choices=GrammarLevel.choices, default=GrammarLevel.N5)
    summary = models.TextField(blank=True, help_text="Mô tả ngắn / ý chính")
    details = models.TextField(blank=True, help_text="Giải thích chi tiết (plain text hoặc Markdown)")
    examples = models.TextField(blank=True, help_text="Ví dụ, mỗi dòng một câu")
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
        ordering = ["level", "title"]
        verbose_name = "Ngữ pháp"
        verbose_name_plural = "Ngữ pháp"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

