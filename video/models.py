from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Video(models.Model):
    LEVEL_CHOICES = [
        ("N5", "N5"),
        ("N4", "N4"),
        ("N3", "N3"),
        ("N2", "N2"),
        ("N1", "N1"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default="N5")
    category = models.ForeignKey(
        Category, related_name="videos", on_delete=models.SET_NULL, null=True, blank=True
    )

    description = models.TextField(blank=True)

    youtube_id = models.CharField(max_length=50)

    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)

    duration_seconds = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("video:detail", args=[self.slug])

    @property
    def duration_label(self):
        m, s = divmod(self.duration_seconds, 60)
        return f"{m:02d}:{s:02d}"

    def __str__(self):
        return self.title


class TranscriptLine(models.Model):
    video = models.ForeignKey(
        Video, related_name="transcript_lines", on_delete=models.CASCADE
    )
    start_time = models.PositiveIntegerField(
        help_text="Thời gian bắt đầu (giây) từ đầu video"
    )
    text = models.TextField()

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.video.title} @ {self.start_time}s"
