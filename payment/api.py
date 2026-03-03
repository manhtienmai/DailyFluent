"""Payment API — plans, create payment, status polling, subscription."""

from ninja import Router, Schema
from typing import List, Optional
from decimal import Decimal

router = Router()


class PlanOut(Schema):
    id: int
    name: str
    slug: str
    description: str
    price: float
    duration_days: int
    features: list
    is_popular: bool


class PaymentOut(Schema):
    id: str
    plan_name: str
    amount: float
    status: str
    status_display: str
    payment_method: str
    bank_account_name: str
    bank_account_number: str
    bank_name: str
    bank_transfer_code: str
    created_at: str


class SubscriptionOut(Schema):
    plan_name: str
    plan_slug: str
    start_date: str
    end_date: str
    is_active: bool
    is_valid: bool
    features: list


class CreatePaymentIn(Schema):
    plan_slug: str
    payment_method: str = "bank"


@router.get("/plans", response=List[PlanOut], auth=None)
def list_plans(request):
    """List all active payment plans."""
    from payment.models import PaymentPlan
    plans = PaymentPlan.objects.filter(is_active=True)
    return [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "price": float(p.price),
            "duration_days": p.duration_days,
            "features": p.features or [],
            "is_popular": p.is_popular,
        }
        for p in plans
    ]


@router.post("/create", response=PaymentOut)
def create_payment(request, payload: CreatePaymentIn):
    """Create a new payment."""
    from payment.models import PaymentPlan, Payment
    from django.conf import settings

    plan = PaymentPlan.objects.get(slug=payload.plan_slug, is_active=True)
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price,
        payment_method=payload.payment_method,
        bank_account_name=getattr(settings, "BANK_ACCOUNT_NAME", ""),
        bank_account_number=getattr(settings, "BANK_ACCOUNT_NUMBER", ""),
        bank_name=getattr(settings, "BANK_NAME", ""),
        bank_transfer_code=f"DF{str(payment.id)[:8].upper()}" if False else "",
    )
    # Generate transfer code from payment ID
    payment.bank_transfer_code = f"DF{str(payment.id).replace('-', '')[:8].upper()}"
    payment.save()
    return _payment_out(payment)


@router.get("/{payment_id}/status", response=PaymentOut)
def payment_status(request, payment_id: str):
    """Get payment status (for polling)."""
    from payment.models import Payment
    payment = Payment.objects.select_related("plan").get(id=payment_id, user=request.user)
    return _payment_out(payment)


@router.get("/my-subscription", response=Optional[SubscriptionOut])
def my_subscription(request):
    """Get current user's subscription."""
    from payment.models import Subscription
    try:
        sub = Subscription.objects.select_related("plan").get(user=request.user)
        sub.check_and_update_status()
        return {
            "plan_name": sub.plan.name,
            "plan_slug": sub.plan.slug,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "is_active": sub.is_active,
            "is_valid": sub.is_valid,
            "features": sub.plan.features or [],
        }
    except Subscription.DoesNotExist:
        return None


def _payment_out(p):
    return {
        "id": str(p.id),
        "plan_name": p.plan.name,
        "amount": float(p.amount),
        "status": p.status,
        "status_display": p.get_status_display(),
        "payment_method": p.payment_method,
        "bank_account_name": p.bank_account_name,
        "bank_account_number": p.bank_account_number,
        "bank_name": p.bank_name,
        "bank_transfer_code": p.bank_transfer_code,
        "created_at": p.created_at.isoformat(),
    }
