# wallet/exceptions.py
"""
Custom exceptions cho wallet app.
"""


class WalletException(Exception):
    """Base exception cho wallet"""
    pass


class InsufficientCoinsError(WalletException):
    """
    Không đủ coin để thực hiện giao dịch.
    Raise khi user cố trừ nhiều hơn số dư hiện có.
    """
    def __init__(self, current_balance, required_amount):
        self.current_balance = current_balance
        self.required_amount = required_amount
        super().__init__(
            f"Không đủ coin. Số dư hiện tại: {current_balance}, cần: {required_amount}"
        )


class AlreadyCheckedInError(WalletException):
    """
    User đã điểm danh trong ngày hôm nay.
    """
    def __init__(self):
        super().__init__("Bạn đã điểm danh hôm nay rồi!")


class WalletLockedError(WalletException):
    """
    Ví đang bị khóa (ví dụ: do vi phạm).
    """
    def __init__(self):
        super().__init__("Ví của bạn hiện đang bị khóa.")
