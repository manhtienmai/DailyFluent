# wallet/services.py
"""
CoinService - Core business logic cho hệ thống Coin.

QUAN TRỌNG về bảo mật:
1. Tất cả giao dịch coin PHẢI đi qua CoinService.execute_transaction()
2. KHÔNG BAO GIỜ cập nhật trực tiếp wallet.coins ở ngoài service này.
3. Sử dụng transaction.atomic() và select_for_update() để chống Race Condition.

Race Condition là gì?
- Khi 2 requests đến cùng lúc, cả 2 đều đọc số dư = 100
- Cả 2 đều cộng 10 -> cả 2 ghi 110
- Kết quả: user chỉ được 110 thay vì 120
- select_for_update() khóa row lại, request 2 phải chờ request 1 xong mới được đọc
"""

from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import UserWallet, CoinTransaction
from .exceptions import (
    InsufficientCoinsError,
    AlreadyCheckedInError,
    WalletLockedError,
)


# =====================================================
# CONFIGURATION - Có thể move ra settings.py nếu cần
# =====================================================
DAILY_CHECKIN_REWARD = 10  # Coin cơ bản mỗi ngày
STREAK_MILESTONE = 7  # Mỗi 7 ngày liên tục
STREAK_BONUS = 100  # Thưởng thêm khi đạt milestone


class CoinService:
    """
    Service xử lý tất cả business logic liên quan đến Coin.
    Tất cả methods đều là staticmethod để dễ test và sử dụng.
    """

    @staticmethod
    def get_balance(user):
        """
        Lấy số dư coin hiện tại của user.
        
        Returns:
            int: Số coin hiện có
        """
        wallet = UserWallet.get_or_create_for_user(user)
        return wallet.coins

    @staticmethod
    def get_wallet_info(user):
        """
        Lấy thông tin đầy đủ của ví.
        
        Returns:
            dict: {
                'coins': int,
                'checkin_streak': int,
                'last_checkin_date': date or None,
                'checked_in_today': bool,
                'is_locked': bool
            }
        """
        wallet = UserWallet.get_or_create_for_user(user)
        today = timezone.localdate()
        
        return {
            'coins': wallet.coins,
            'checkin_streak': wallet.checkin_streak,
            'last_checkin_date': wallet.last_checkin_date,
            'checked_in_today': wallet.last_checkin_date == today,
            'is_locked': wallet.is_locked,
        }

    @staticmethod
    def execute_transaction(user, amount, transaction_type, description='', reference_id=None):
        """
        Thực hiện giao dịch coin AN TOÀN.
        
        ĐÂY LÀ METHOD DUY NHẤT ĐƯỢC PHÉP THAY ĐỔI SỐ DƯ COIN.
        
        Args:
            user: User object
            amount: int - Số coin (dương = cộng, âm = trừ)
            transaction_type: str - Loại giao dịch (từ CoinTransaction.TransactionType)
            description: str - Mô tả
            reference_id: str - ID tham chiếu (optional)
        
        Returns:
            dict: {
                'success': True,
                'new_balance': int,
                'amount': int,
                'transaction_id': int
            }
        
        Raises:
            InsufficientCoinsError: Khi trừ tiền mà không đủ số dư
            WalletLockedError: Khi ví bị khóa
        
        GIẢI THÍCH KỸ THUẬT:
        
        1. transaction.atomic():
           - Đảm bảo tất cả operations trong block này hoặc thành công hết, 
             hoặc rollback hết nếu có lỗi.
           - Ví dụ: nếu tạo được transaction record nhưng update wallet lỗi,
             cả 2 đều sẽ bị rollback.
        
        2. select_for_update():
           - Khóa row của wallet trong database.
           - Các requests khác muốn đọc/ghi row này phải CHỜ cho đến khi 
             transaction hiện tại kết thúc.
           - Đây là cách chống Race Condition hiệu quả nhất.
        """
        with transaction.atomic():
            # Bước 1: Lấy wallet và KHÓA ROW lại
            # nowait=False (default) = chờ nếu row đang bị lock
            wallet, created = UserWallet.objects.select_for_update().get_or_create(
                user=user,
                defaults={'coins': 0}
            )
            
            # Bước 2: Kiểm tra ví có bị khóa không
            if wallet.is_locked:
                raise WalletLockedError()
            
            # Bước 3: Kiểm tra số dư nếu đang trừ tiền
            if amount < 0:
                required = abs(amount)
                if wallet.coins < required:
                    raise InsufficientCoinsError(
                        current_balance=wallet.coins,
                        required_amount=required
                    )
            
            # Bước 4: Cập nhật số dư
            # Dùng F() expression để tránh race condition ở DB level
            # Hoặc có thể cộng trực tiếp vì đã lock row
            new_balance = wallet.coins + amount
            wallet.coins = new_balance
            wallet.save(update_fields=['coins', 'updated_at'])
            
            # Bước 5: Tạo transaction record (sổ cái)
            tx = CoinTransaction.objects.create(
                user=user,
                amount=amount,
                balance_after=new_balance,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
            )
            
            return {
                'success': True,
                'new_balance': new_balance,
                'amount': amount,
                'transaction_id': tx.id,
            }

    @staticmethod
    def daily_checkin(user):
        """
        Xử lý điểm danh hàng ngày.
        
        Logic:
        1. Kiểm tra đã điểm danh hôm nay chưa
        2. Tính streak:
           - Nếu điểm danh ngày liên tiếp: streak += 1
           - Nếu bỏ lỡ (gap > 1 ngày): reset streak = 1
        3. Tính thưởng:
           - Base: DAILY_CHECKIN_REWARD (10 coins)
           - Bonus: STREAK_BONUS (100 coins) mỗi STREAK_MILESTONE (7) ngày
        4. Cập nhật wallet và tạo transaction
        
        Returns:
            dict: {
                'success': True,
                'coins_earned': int,
                'bonus_earned': int (0 hoặc STREAK_BONUS),
                'new_streak': int,
                'new_balance': int,
            }
        
        Raises:
            AlreadyCheckedInError: Nếu đã điểm danh hôm nay
            WalletLockedError: Nếu ví bị khóa
        """
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        
        with transaction.atomic():
            # Khóa wallet row
            wallet, created = UserWallet.objects.select_for_update().get_or_create(
                user=user,
                defaults={'coins': 0}
            )
            
            # Kiểm tra ví bị khóa
            if wallet.is_locked:
                raise WalletLockedError()
            
            # Kiểm tra đã điểm danh hôm nay chưa
            if wallet.last_checkin_date == today:
                raise AlreadyCheckedInError()
            
            # Tính streak
            if wallet.last_checkin_date == yesterday:
                # Điểm danh liên tục -> tăng streak
                new_streak = wallet.checkin_streak + 1
            else:
                # Bỏ lỡ hoặc lần đầu -> reset streak
                new_streak = 1
            
            # Tính thưởng
            base_reward = DAILY_CHECKIN_REWARD
            bonus = 0
            
            # Kiểm tra milestone (mỗi 7 ngày)
            if new_streak > 0 and new_streak % STREAK_MILESTONE == 0:
                bonus = STREAK_BONUS
            
            total_reward = base_reward + bonus
            
            # Cập nhật wallet
            wallet.checkin_streak = new_streak
            wallet.last_checkin_date = today
            wallet.coins = wallet.coins + total_reward
            wallet.save(update_fields=['checkin_streak', 'last_checkin_date', 'coins', 'updated_at'])
            
            # Tạo transaction record
            description = f"Điểm danh ngày {today.strftime('%d/%m/%Y')} (chuỗi {new_streak} ngày)"
            if bonus > 0:
                description += f" - Thưởng milestone {STREAK_MILESTONE} ngày!"
            
            tx = CoinTransaction.objects.create(
                user=user,
                amount=total_reward,
                balance_after=wallet.coins,
                transaction_type=CoinTransaction.TransactionType.CHECK_IN,
                description=description,
            )
            
            return {
                'success': True,
                'coins_earned': base_reward,
                'bonus_earned': bonus,
                'total_earned': total_reward,
                'new_streak': new_streak,
                'new_balance': wallet.coins,
                'transaction_id': tx.id,
            }

    @staticmethod
    def get_transactions(user, limit=20, offset=0, transaction_type=None):
        """
        Lấy lịch sử giao dịch của user.
        
        Args:
            user: User object
            limit: Số records tối đa
            offset: Vị trí bắt đầu
            transaction_type: Filter theo loại (optional)
        
        Returns:
            QuerySet of CoinTransaction
        """
        qs = CoinTransaction.objects.filter(user=user)
        
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        
        return qs.order_by('-created_at')[offset:offset + limit]

    @staticmethod
    def admin_adjust(user, amount, reason, admin_user=None):
        """
        Admin điều chỉnh số dư (cộng hoặc trừ).
        
        Args:
            user: User cần điều chỉnh
            amount: Số coin (dương hoặc âm)
            reason: Lý do điều chỉnh
            admin_user: Admin thực hiện (optional, để log)
        
        Returns:
            dict: Kết quả giao dịch
        """
        description = f"Admin điều chỉnh: {reason}"
        if admin_user:
            description += f" (bởi {admin_user.email})"
        
        return CoinService.execute_transaction(
            user=user,
            amount=amount,
            transaction_type=CoinTransaction.TransactionType.ADMIN_ADJUST,
            description=description,
        )
