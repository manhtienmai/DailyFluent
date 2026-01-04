from django.contrib import admin
from .models import TodoItem


@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'completed', 'priority', 'due_date', 'created_at')
    list_filter = ('completed', 'priority', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('completed',)
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'title', 'description')
        }),
        ('Trạng thái', {
            'fields': ('completed', 'priority', 'due_date')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at')
        }),
    )
