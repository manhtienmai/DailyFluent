from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PageView(models.Model):
    """Track individual page views"""
    path = models.CharField(max_length=500, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    referer = models.URLField(max_length=1000, blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Parsed user agent info
    browser = models.CharField(max_length=100, blank=True, default="")
    device = models.CharField(max_length=100, blank=True, default="")
    os = models.CharField(max_length=100, blank=True, default="")
    
    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["path", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.path} - {self.timestamp}"


class DailyStats(models.Model):
    """Aggregated daily statistics"""
    date = models.DateField(unique=True, db_index=True)
    total_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    unique_users = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Daily stats"

    def __str__(self):
        return f"{self.date}: {self.total_views} views, {self.unique_visitors} visitors"


class PopularPage(models.Model):
    """Track popular pages by day"""
    date = models.DateField(db_index=True)
    path = models.CharField(max_length=500)
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["-date", "-views"]
        unique_together = ["date", "path"]

    def __str__(self):
        return f"{self.path}: {self.views} views on {self.date}"
