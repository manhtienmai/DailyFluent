from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    Thông báo cho người dùng.
    Hỗ trợ phân loại (study, system, social, assignment) và deep-link.
    """

    CATEGORY_CHOICES = [
        ("study", "Study Alert"),
        ("system", "System Alert"),
        ("social", "Social / Interaction"),
        ("assignment", "Teacher Assignment"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="system",
        db_index=True,
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField(
        max_length=500,
        blank=True,
        help_text="Deep-link URL, e.g. /exam/english/grammar/present-simple",
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} [{self.category}] {self.title} → {self.user}"


class Assignment(models.Model):
    """
    Bài tập được giáo viên giao cho học sinh.
    Khi tạo, hệ thống tự sinh Notification cho mỗi học sinh.
    """

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assignments",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(
        max_length=50,
        help_text='E.g. "grammar", "vocab", "exam", "bunpou"',
    )
    quiz_id = models.CharField(
        max_length=100,
        help_text="Topic slug, e.g. present-simple, N3:day01",
    )
    link = models.CharField(
        max_length=500,
        blank=True,
        help_text="Where the student should go to do this assignment",
    )
    due_date = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assignments",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def __str__(self):
        return f"{self.title} (by {self.teacher})"

    def create_notifications(self):
        """Create a Notification for each assigned student."""
        notifications = []
        for student in self.assigned_to.all():
            notifications.append(
                Notification(
                    user=student,
                    category="assignment",
                    title=f"📝 Bài tập mới: {self.title}",
                    message=self.description,
                    link=self.link,
                )
            )
        if notifications:
            Notification.objects.bulk_create(notifications)
        return len(notifications)
