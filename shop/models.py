# shop/models.py
"""
Models cho hệ thống Cửa hàng.

Bao gồm:
- AvatarFrame: Khung avatar với CSS gradient/styling
- UserInventory: Các item user đã mua
"""

from django.conf import settings
from django.db import models


class AvatarFrame(models.Model):
    """
    Khung avatar có thể mua bằng coin.
    """
    class Rarity(models.TextChoices):
        COMMON = 'COMMON', 'Thường'
        RARE = 'RARE', 'Hiếm'
        EPIC = 'EPIC', 'Sử thi'
        LEGENDARY = 'LEGENDARY', 'Huyền thoại'
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    # Giá coin
    price = models.PositiveIntegerField(default=100)
    
    # Rarity/Tier
    rarity = models.CharField(
        max_length=20,
        choices=Rarity.choices,
        default=Rarity.COMMON
    )
    
    # CSS cho frame (gradient, border, animation, etc.)
    css_gradient = models.CharField(
        max_length=500,
        default="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        help_text="CSS gradient cho viền khung"
    )
    css_animation = models.CharField(
        max_length=200,
        blank=True,
        help_text="Tên CSS animation (vd: pulse, glow, rainbow)"
    )
    border_width = models.PositiveIntegerField(default=3)
    
    # Preview image (optional)
    preview_image = models.ImageField(
        upload_to="shop/frames/",
        blank=True,
        null=True,
        help_text="Ảnh preview của khung"
    )
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_limited = models.BooleanField(
        default=False,
        help_text="Sản phẩm giới hạn thời gian"
    )
    available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Chỉ hiển thị nếu is_limited=True"
    )
    
    # Ordering
    display_order = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Khung Avatar"
        verbose_name_plural = "Khung Avatar"
        ordering = ['display_order', 'rarity', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()}) - {self.price} coins"


class UserInventory(models.Model):
    """
    Lưu các item user đã mua.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    frame = models.ForeignKey(
        AvatarFrame,
        on_delete=models.CASCADE,
        related_name='owners'
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_equipped = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"
        unique_together = ('user', 'frame')
    
    def __str__(self):
        equipped = " [Đang dùng]" if self.is_equipped else ""
        return f"{self.user.username} - {self.frame.name}{equipped}"
    
    def equip(self):
        """Trang bị frame này và bỏ trang bị frame cũ."""
        # Bỏ trang bị frame cũ
        UserInventory.objects.filter(
            user=self.user, 
            is_equipped=True
        ).update(is_equipped=False)
        # Trang bị frame mới
        self.is_equipped = True
        self.save()
