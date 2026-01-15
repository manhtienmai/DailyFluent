from django.db import models
from django.conf import settings


class FeedbackItem(models.Model):
    """
    Model cho đề xuất tính năng hoặc báo lỗi.
    Users có thể tạo, upvote, và bình luận.
    """
    
    class Type(models.TextChoices):
        FEATURE = 'feature', 'Feature Request'
        BUG = 'bug', 'Bug Report'
    
    class Status(models.TextChoices):
        NEW = 'new', 'Mới'
        PLANNED = 'planned', 'Đã lên kế hoạch'
        IN_PROGRESS = 'in_progress', 'Đang làm'
        DONE = 'done', 'Đã xong'
    
    title = models.CharField(
        max_length=200,
        verbose_name='Tiêu đề',
        help_text='Tiêu đề ngắn gọn cho đề xuất'
    )
    description = models.TextField(
        verbose_name='Mô tả chi tiết',
        help_text='Mô tả chi tiết về đề xuất hoặc lỗi'
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.FEATURE,
        verbose_name='Loại'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Trạng thái'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedback_items',
        verbose_name='Người tạo'
    )
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='upvoted_feedback',
        blank=True,
        verbose_name='Lượt vote'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đề xuất'
        verbose_name_plural = 'Đề xuất'
    
    def __str__(self):
        return self.title
    
    def total_votes(self):
        """Trả về tổng số lượt upvote."""
        return self.upvotes.count()
    
    def get_type_display_vi(self):
        """Trả về loại bằng tiếng Việt."""
        return 'Tính năng mới' if self.type == self.Type.FEATURE else 'Báo lỗi'


class FeedbackComment(models.Model):
    """
    Model cho bình luận trên đề xuất.
    Admin responses sẽ được highlight đặc biệt.
    """
    
    feedback = models.ForeignKey(
        FeedbackItem,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Đề xuất'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedback_comments',
        verbose_name='Người bình luận'
    )
    content = models.TextField(
        verbose_name='Nội dung',
        help_text='Nội dung bình luận'
    )
    is_admin_response = models.BooleanField(
        default=False,
        verbose_name='Phản hồi chính thức',
        help_text='Đánh dấu nếu đây là phản hồi chính thức từ Admin'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        ordering = ['created_at']  # Timeline style - oldest first
        verbose_name = 'Bình luận'
        verbose_name_plural = 'Bình luận'
    
    def __str__(self):
        return f'{self.user.email} - {self.feedback.title[:30]}'
