from django.db import models
from django.utils.text import slugify


class Course(models.Model):
    """
    Khóa học tối giản: chỉ cần xuất hiện để gán vocab/grammar vào.
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

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
