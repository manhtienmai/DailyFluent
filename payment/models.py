from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
import uuid


class PaymentPlan(models.Model):
    """Gói thanh toán/premium"""
    name = models.CharField(max_length=100, help_text="Tên gói (VD: Premium 1 tháng)")
    slug = models.SlugField(unique=True, help_text="Slug cho URL")
    description = models.TextField(blank=True, help_text="Mô tả gói")
    
    # Giá tiền (VND)
    price = models.DecimalField(max_digits=12, decimal_places=0, help_text="Giá tiền (VND)")
    
    # Thời gian hiệu lực (ngày)
    duration_days = models.PositiveIntegerField(help_text="Số ngày hiệu lực")
    
    # Features
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="Danh sách tính năng (JSON array)"
    )
    
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Đánh dấu gói phổ biến")
    order = models.PositiveIntegerField(default=0, help_text="Thứ tự hiển thị")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'price']
        verbose_name = "Gói thanh toán"
        verbose_name_plural = "Gói thanh toán"
    
    def __str__(self):
        return f"{self.name} - {self.price:,.0f} VND"


class Payment(models.Model):
    """Giao dịch thanh toán"""
    
    class PaymentMethod(models.TextChoices):
        BANK = 'bank', 'Chuyển khoản ngân hàng'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Chờ thanh toán'
        PROCESSING = 'processing', 'Đang xử lý'
        COMPLETED = 'completed', 'Đã thanh toán'
        FAILED = 'failed', 'Thất bại'
        CANCELLED = 'cancelled', 'Đã hủy'
    
    # Thông tin cơ bản
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.PROTECT, related_name='payments')
    
    # Số tiền
    amount = models.DecimalField(max_digits=12, decimal_places=0, help_text="Số tiền (VND)")
    
    # Phương thức thanh toán
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK
    )
    
    # Trạng thái
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Bank transfer specific fields
    bank_account_name = models.CharField(max_length=200, blank=True, help_text="Tên chủ tài khoản")
    bank_account_number = models.CharField(max_length=50, blank=True, help_text="Số tài khoản")
    bank_name = models.CharField(max_length=100, blank=True, help_text="Tên ngân hàng")
    bank_transfer_code = models.CharField(max_length=100, blank=True, help_text="Mã giao dịch chuyển khoản")
    bank_transfer_image = models.ImageField(
        upload_to='payments/bank_transfers/',
        blank=True,
        null=True,
        help_text="Ảnh chụp biên lai chuyển khoản"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Thông tin bổ sung (JSON)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Giao dịch thanh toán"
        verbose_name_plural = "Giao dịch thanh toán"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['bank_transfer_code']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - {self.amount:,.0f} VND ({self.get_status_display()})"
    
    def get_absolute_url(self):
        """URL để xem chi tiết payment"""
        return reverse('payment:status', kwargs={'payment_id': self.id})
    
    def mark_completed(self):
        """Đánh dấu thanh toán thành công"""
        self.status = self.PaymentStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()
        
        # Tạo hoặc cập nhật subscription
        subscription, created = Subscription.objects.get_or_create(
            user=self.user,
            defaults={
                'plan': self.plan,
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timezone.timedelta(days=self.plan.duration_days),
                'is_active': True,
            }
        )
        
        if not created:
            # Nếu đã có subscription, gia hạn thêm
            if subscription.is_active:
                # Gia hạn từ ngày kết thúc hiện tại
                subscription.end_date += timezone.timedelta(days=self.plan.duration_days)
            else:
                # Bắt đầu lại từ hôm nay
                subscription.start_date = timezone.now().date()
                subscription.end_date = timezone.now().date() + timezone.timedelta(days=self.plan.duration_days)
                subscription.is_active = True
            subscription.plan = self.plan
            subscription.save()


class Subscription(models.Model):
    """Subscription của user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.PROTECT, related_name='subscriptions')
    
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Gói đăng ký"
        verbose_name_plural = "Gói đăng ký"
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({'Active' if self.is_active else 'Inactive'})"
    
    @property
    def is_valid(self):
        """Kiểm tra subscription còn hiệu lực không"""
        if not self.is_active:
            return False
        today = timezone.now().date()
        return today <= self.end_date
    
    def check_and_update_status(self):
        """Kiểm tra và cập nhật trạng thái subscription"""
        if self.is_active and timezone.now().date() > self.end_date:
            self.is_active = False
            self.save()
        return self.is_active
