# shop/admin.py
from django.contrib import admin
from .models import AvatarFrame, UserInventory


@admin.register(AvatarFrame)
class AvatarFrameAdmin(admin.ModelAdmin):
    list_display = ['name', 'rarity', 'price', 'is_active', 'is_limited', 'display_order']
    list_filter = ['rarity', 'is_active', 'is_limited']
    list_editable = ['price', 'is_active', 'display_order']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'rarity', 'name']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'description', 'price', 'rarity')
        }),
        ('Giao diện', {
            'fields': ('css_gradient', 'css_animation', 'border_width', 'preview_image')
        }),
        ('Hiển thị', {
            'fields': ('is_active', 'is_limited', 'available_until', 'display_order')
        }),
    )


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'frame', 'is_equipped', 'purchased_at']
    list_filter = ['is_equipped', 'frame__rarity']
    search_fields = ['user__username', 'user__email', 'frame__name']
    readonly_fields = ['purchased_at']
