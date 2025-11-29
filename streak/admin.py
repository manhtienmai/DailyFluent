# streak/admin.py
from django.contrib import admin

from .models import DailyActivity, StreakStat


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "lessons_completed", "minutes_studied", "points_earned")
    list_filter = ("date",)
    search_fields = ("user__username", "user__email")
    ordering = ("-date",)


@admin.register(StreakStat)
class StreakStatAdmin(admin.ModelAdmin):
    list_display = ("user", "current_streak", "longest_streak", "last_active_date", "freezes_left")
    search_fields = ("user__username", "user__email")
