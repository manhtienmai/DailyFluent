# streak/models.py
from django.conf import settings
from django.db import models


class DailyActivity(models.Model):
    """
    Lưu hoạt động học của user theo từng ngày.
    Có thể là số bài học, phút học, điểm, v.v.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()  # Ngày theo timezone hệ thống (TIME_ZONE) hoặc user
    lessons_completed = models.PositiveIntegerField(default=0)
    minutes_studied = models.PositiveIntegerField(default=0)
    points_earned = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.date}"


class StreakStat(models.Model):
    """
    Lưu trạng thái streak hiện tại và kỷ lục của user.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)

    # Nếu sau này muốn làm Freeze thì thêm trường ở đây
    freezes_left = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Streak'
        verbose_name_plural = 'Streaks'

    def __str__(self):
        return f"{self.user} streak: {self.current_streak} (longest {self.longest_streak})"
