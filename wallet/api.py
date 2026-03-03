"""
Wallet API router (Django Ninja).

Endpoints:
  GET  /api/v1/wallet/balance       – Wallet balance + check-in streak
  POST /api/v1/wallet/check-in      – Daily check-in (earn coins)
  GET  /api/v1/wallet/transactions  – Paginated transaction history

Note: the original DRF endpoints at /api/wallet/* remain active during
the migration. These Ninja endpoints are the canonical API for the
Next.js frontend.
"""

import datetime
from typing import List, Optional

from ninja import Router, Schema

from .services import CoinService
from .models import CoinTransaction
from .exceptions import AlreadyCheckedInError, WalletLockedError

router = Router()


# ── Schemas ────────────────────────────────────────────────

class WalletBalanceOut(Schema):
    coins: int
    checkin_streak: int
    last_checkin_date: Optional[datetime.date] = None
    checked_in_today: bool
    is_locked: bool


class CheckInOut(Schema):
    success: bool
    coins_earned: int
    bonus_earned: int
    total_earned: int
    new_streak: int
    new_balance: int
    message: str


class ErrorOut(Schema):
    success: bool
    error: str
    message: str


class TransactionOut(Schema):
    id: int
    amount: int
    balance_after: int
    transaction_type: str
    description: str
    created_at: datetime.datetime


class TransactionsOut(Schema):
    count: int
    results: List[TransactionOut]


# ── Endpoints ──────────────────────────────────────────────

@router.get("/balance", response=WalletBalanceOut)
def wallet_balance(request):
    """Return wallet balance and check-in streak information."""
    info = CoinService.get_wallet_info(request.user)
    return WalletBalanceOut(**info)


@router.post("/check-in", response={200: CheckInOut, 400: ErrorOut, 403: ErrorOut})
def check_in(request):
    """
    Perform the daily check-in to earn coins.

    Returns 400 if already checked in today, 403 if the wallet is locked.
    """
    try:
        result = CoinService.daily_checkin(request.user)
        if result["bonus_earned"] > 0:
            message = (
                f"Bạn đã điểm danh {result['new_streak']} ngày liên tục "
                f"và nhận được thưởng {result['bonus_earned']} coin!"
            )
        else:
            message = f"Điểm danh thành công! Chuỗi {result['new_streak']} ngày."
        result["message"] = message
        return 200, CheckInOut(**result)
    except AlreadyCheckedInError as exc:
        return 400, ErrorOut(
            success=False, error="already_checked_in", message=str(exc)
        )
    except WalletLockedError as exc:
        return 403, ErrorOut(
            success=False, error="wallet_locked", message=str(exc)
        )


@router.get("/transactions", response=TransactionsOut)
def transactions(
    request,
    page: int = 1,
    page_size: int = 20,
    type: str = None,
):
    """
    Return a paginated list of coin transactions.

    Query params:
      page      – page number (default 1)
      page_size – items per page (default 20, max 100)
      type      – filter by transaction type (e.g. CHECK_IN, PURCHASE)
    """
    page_size = min(page_size, 100)
    qs = CoinTransaction.objects.filter(user=request.user).order_by("-created_at")
    if type:
        qs = qs.filter(transaction_type=type)

    count = qs.count()
    offset = (page - 1) * page_size
    items = list(qs[offset : offset + page_size])

    return TransactionsOut(
        count=count,
        results=[
            TransactionOut(
                id=tx.id,
                amount=tx.amount,
                balance_after=tx.balance_after,
                transaction_type=tx.transaction_type,
                description=tx.description,
                created_at=tx.created_at,
            )
            for tx in items
        ],
    )
