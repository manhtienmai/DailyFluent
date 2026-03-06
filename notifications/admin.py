from django.contrib import admin
from .models import Notification, Assignment


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "is_read", "created_at")
    list_filter = ("category", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "quiz_type", "quiz_id", "due_date", "created_at")
    list_filter = ("quiz_type", "created_at")
    search_fields = ("title", "description", "teacher__username")
    raw_id_fields = ("teacher",)
    filter_horizontal = ("assigned_to",)
    readonly_fields = ("created_at",)
