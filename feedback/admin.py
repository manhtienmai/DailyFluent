from django.contrib import admin
from .models import FeedbackItem, FeedbackComment


class FeedbackCommentInline(admin.TabularInline):
    model = FeedbackComment
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'content', 'is_admin_response', 'created_at')


@admin.register(FeedbackItem)
class FeedbackItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'status', 'user', 'total_votes', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('title', 'description', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total_votes')
    list_editable = ('status',)
    inlines = [FeedbackCommentInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'type', 'status')
        }),
        ('Thông tin', {
            'fields': ('user', 'total_votes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_votes(self, obj):
        return obj.total_votes()
    total_votes.short_description = 'Số vote'


@admin.register(FeedbackComment)
class FeedbackCommentAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'user', 'is_admin_response', 'created_at')
    list_filter = ('is_admin_response', 'created_at')
    search_fields = ('content', 'user__email', 'feedback__title')
    list_editable = ('is_admin_response',)
    raw_id_fields = ('feedback', 'user')
