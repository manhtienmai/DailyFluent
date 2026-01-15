# wallet/models.py
"""
Models cho hệ thống Coin virtual currency.

Bao gồm:
- UserWallet: Ví tiền của user (1-1 relationship)
- CoinTransaction: Sổ cái giao dịch (Immutable - không thể sửa/xóa)
"""

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class UserWallet(models.Model):
    """
    Ví tiền của user.
    Mỗi user chỉ có 1 ví duy nhất (OneToOne relationship).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Số dư coin hiện tại
    coins = models.PositiveIntegerField(
        default=0,
        help_text="Số coin hiện có"
    )
    
    # Điểm danh hàng ngày
    last_checkin_date = models.DateField(
        null=True,
        blank=True,
        help_text="Ngày điểm danh cuối cùng"
    )
    checkin_streak = models.PositiveIntegerField(
        default=0,
        help_text="Số ngày điểm danh liên tục"
    )
    
    # Trạng thái ví
    is_locked = models.BooleanField(
        default=False,
        help_text="Ví có bị khóa không (do vi phạm, etc.)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ví tiền"
        verbose_name_plural = "Ví tiền"
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.coins} coins"

    @classmethod
    def get_or_create_for_user(cls, user):
        """
        Lấy hoặc tạo ví cho user.
        Sử dụng method này thay vì trực tiếp get_or_create để đảm bảo consistency.
        """
        wallet, created = cls.objects.get_or_create(user=user)
        return wallet


class CoinTransaction(models.Model):
    """
    Sổ cái giao dịch coin.
    
    QUAN TRỌNG: Model này là IMMUTABLE (bất biến).
    - Không được phép UPDATE sau khi tạo
    - Không được phép DELETE
    
    Điều này đảm bảo tính toàn vẹn của lịch sử giao dịch để đối soát.
    """
    
    class TransactionType(models.TextChoices):
        CHECK_IN = 'CHECK_IN', 'Điểm danh hàng ngày'
        PURCHASE = 'PURCHASE', 'Mua hàng'
        BONUS = 'BONUS', 'Thưởng'
        REFUND = 'REFUND', 'Hoàn tiền'
        ADMIN_ADJUST = 'ADMIN_ADJUST', 'Admin điều chỉnh'
        STREAK_BONUS = 'STREAK_BONUS', 'Thưởng chuỗi điểm danh'
        GIFT = 'GIFT', 'Quà tặng'
        EVENT = 'EVENT', 'Sự kiện'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Giữ CASCADE vì muốn xóa transactions khi xóa user
        related_name='coin_transactions'
    )
    
    # Số coin thay đổi (có thể âm hoặc dương)
    amount = models.IntegerField(
        help_text="Số coin thay đổi. Dương = nhận, Âm = trừ"
    )
    
    # Số dư SAU giao dịch (để đối soát)
    balance_after = models.PositiveIntegerField(
        help_text="Số dư sau khi giao dịch hoàn tất"
    )
    
    # Loại giao dịch
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True
    )
    
    # Mô tả chi tiết
    description = models.TextField(
        blank=True,
        help_text="Mô tả chi tiết về giao dịch"
    )
    
    # Reference ID (link đến payment, order, etc.)
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="ID tham chiếu (order_id, payment_id, etc.)"
    )
    
    # Timestamp - không dùng auto_now để tránh bị update
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False
    )
    
    class Meta:
        verbose_name = "Giao dịch coin"
        verbose_name_plural = "Giao dịch coin"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.user.email}: {sign}{self.amount} ({self.get_transaction_type_display()})"

    def save(self, *args, **kwargs):
        """
        Override save để đảm bảo tính bất biến (immutable).
        Chỉ cho phép tạo mới, không cho phép update.
        """
        if self.pk is not None:
            # Record đã tồn tại -> đang cố update -> chặn
            raise ValidationError(
                "CoinTransaction là bất biến. Không được phép sửa đổi sau khi tạo."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete để chặn xóa.
        Nếu cần "xóa" thì nên tạo transaction đảo ngược thay vì xóa thật.
        """
        raise ValidationError(
            "CoinTransaction là bất biến. Không được phép xóa. "
            "Hãy tạo giao dịch đảo ngược nếu cần hoàn tiền."
        )
