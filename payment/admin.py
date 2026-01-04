from django.contrib import admin
from .models import PaymentPlan, Payment, Subscription


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'is_active', 'is_popular', 'order']
    list_filter = ['is_active', 'is_popular']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'plan', 'amount', 'payment_method', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'user__email', 'bank_transfer_code']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('id', 'user', 'plan', 'amount', 'payment_method', 'status')
        }),
        ('Chuyển khoản ngân hàng', {
            'fields': ('bank_account_name', 'bank_account_number', 'bank_name', 'bank_transfer_code', 'bank_transfer_image'),
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active', 'is_valid']
    list_filter = ['is_active', 'plan', 'start_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Còn hiệu lực'
