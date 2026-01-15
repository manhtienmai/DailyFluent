# wallet/admin.py
"""
Django Admin configuration cho wallet app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import UserWallet, CoinTransaction


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    """Admin cho UserWallet."""
    
    list_display = [
        'user',
        'coins_display',
        'checkin_streak',
        'last_checkin_date',
        'is_locked',
        'created_at',
    ]
    list_filter = ['is_locked', 'last_checkin_date']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin user', {
            'fields': ('user',)
        }),
        ('Số dư', {
            'fields': ('coins',)
        }),
        ('Điểm danh', {
            'fields': ('last_checkin_date', 'checkin_streak')
        }),
        ('Trạng thái', {
            'fields': ('is_locked',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def coins_display(self, obj):
        """Hiển thị coins với màu sắc."""
        if obj.coins >= 1000:
            color = 'green'
        elif obj.coins >= 100:
            color = 'blue'
        else:
            color = 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:,}</span>',
            color, obj.coins
        )
    coins_display.short_description = 'Coins'
    coins_display.admin_order_field = 'coins'


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    """
    Admin cho CoinTransaction.
    
    LƯU Ý: Model này là IMMUTABLE nên:
    - Không có nút Edit
    - Không có nút Delete
    - Chỉ view only
    """
    
    list_display = [
        'id',
        'user',
        'amount_display',
        'balance_after',
        'transaction_type',
        'description_short',
        'created_at',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'description', 'reference_id']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    # Chỉ cho phép xem, không cho sửa/xóa
    readonly_fields = [
        'user', 'amount', 'balance_after', 'transaction_type',
        'description', 'reference_id', 'created_at'
    ]
    
    def has_add_permission(self, request):
        """Không cho phép tạo transaction từ admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Không cho phép sửa transaction."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Không cho phép xóa transaction."""
        return False
    
    def amount_display(self, obj):
        """Hiển thị amount với màu sắc (xanh cho +, đỏ cho -)."""
        if obj.amount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">+{:,}</span>',
                obj.amount
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,}</span>',
                obj.amount
            )
    amount_display.short_description = 'Số coin'
    amount_display.admin_order_field = 'amount'
    
    def description_short(self, obj):
        """Hiển thị description ngắn gọn."""
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = 'Mô tả'
