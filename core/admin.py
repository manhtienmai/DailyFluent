from django.contrib import admin
from .models import (
    Course, Section, Lesson,
    DictationExercise, DictationSegment, DictationProgress,
    Enrollment,
    Badge, UserBadge,
    UserProfile,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'order']
    list_filter = ['section__course']
    search_fields = ['title', 'section__title']
    ordering = ['section', 'order']


@admin.register(DictationExercise)
class DictationExerciseAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'order']
    search_fields = ['title']
    ordering = ['order']


@admin.register(DictationSegment)
class DictationSegmentAdmin(admin.ModelAdmin):
    list_display = ['exercise', 'order', 'start_time', 'end_time']
    list_filter = ['exercise']
    ordering = ['exercise', 'order']


@admin.register(DictationProgress)
class DictationProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'current_segment', 'total_segments']
    raw_id_fields = ['user', 'exercise']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'progress']
    list_filter = ['course']
    search_fields = ['user__username', 'course__title']
    raw_id_fields = ['user', 'course']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'code', 'order']
    search_fields = ['name', 'code']
    ordering = ['order']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['badge']
    search_fields = ['user__username', 'badge__name']
    raw_id_fields = ['user', 'badge']
    ordering = ['-earned_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_title', 'created_at', 'updated_at']
    search_fields = ['user__username', 'display_title', 'bio']
    raw_id_fields = ['user', 'equipped_frame']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Người dùng', {'fields': ('user',)}),
        ('Thông tin cơ bản', {'fields': ('bio', 'display_title', 'subtitle')}),
        ('Hình ảnh', {'fields': ('avatar', 'cover_image', 'equipped_frame')}),
        ('Mạng xã hội', {'fields': ('social_links', 'info_items'), 'classes': ('collapse',)}),
        ('Skills', {'fields': ('skills', 'certificates', 'hobbies'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
