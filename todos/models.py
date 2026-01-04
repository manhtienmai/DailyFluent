from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TodoItem(models.Model):
    """Mục tiêu hàng ngày của user"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='todo_items'
    )
    title = models.CharField(
        max_length=255,
        help_text="Tiêu đề mục tiêu"
    )
    description = models.TextField(
        blank=True,
        help_text="Mô tả chi tiết (tùy chọn)"
    )
    completed = models.BooleanField(
        default=False,
        help_text="Đã hoàn thành chưa"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Thời gian tạo"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Thời gian cập nhật"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Hạn chót (tùy chọn)"
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Thấp'),
            ('medium', 'Trung bình'),
            ('high', 'Cao'),
        ],
        default='medium',
        help_text="Mức độ ưu tiên"
    )
    period_type = models.CharField(
        max_length=10,
        choices=[
            ('day', 'Ngày'),
            ('week', 'Tuần'),
            ('month', 'Tháng'),
            ('year', 'Năm'),
        ],
        default='day',
        help_text="Loại mục tiêu theo thời gian"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mục tiêu"
        verbose_name_plural = "Mục tiêu"

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def is_overdue(self):
        """Kiểm tra xem mục tiêu có quá hạn không"""
        if self.due_date and not self.completed:
            return timezone.now().date() > self.due_date
        return False
