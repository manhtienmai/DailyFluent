from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import PaymentPlan, Payment, Subscription
from .services import BankTransferService


@login_required
def payment_plans(request):
    """Danh sách các gói thanh toán"""
    plans = PaymentPlan.objects.filter(is_active=True).order_by('order', 'price')
    
    # Check user's current subscription
    current_subscription = None
    try:
        current_subscription = request.user.subscription
        current_subscription.check_and_update_status()
    except Subscription.DoesNotExist:
        pass
    
    context = {
        'plans': plans,
        'current_subscription': current_subscription,
    }
    return render(request, 'payment/plans.html', context)


@login_required
def create_payment(request, plan_slug):
    """Tạo payment mới"""
    plan = get_object_or_404(PaymentPlan, slug=plan_slug, is_active=True)
    
    # Check if user already has active subscription
    try:
        subscription = request.user.subscription
        if subscription.is_valid:
            return render(request, 'payment/already_subscribed.html', {
                'subscription': subscription
            })
    except Subscription.DoesNotExist:
        pass
    
    # Create payment
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price,
        payment_method=Payment.PaymentMethod.BANK
    )
    
    # Show bank transfer info with QR code
    bank_info = BankTransferService.get_bank_info()
    transfer_content = BankTransferService.get_transfer_content(payment)
    
    return render(request, 'payment/bank_transfer.html', {
        'payment': payment,
        'plan': plan,
        'bank_info': bank_info,
        'transfer_content': transfer_content
    })


@login_required
def payment_status(request, payment_id):
    """Xem trạng thái payment"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
        'plan': payment.plan,
    }
    return render(request, 'payment/status.html', context)


@login_required
@require_http_methods(["POST"])
def submit_bank_transfer(request, payment_id):
    """Submit thông tin chuyển khoản ngân hàng"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status != Payment.PaymentStatus.PENDING:
        return JsonResponse({
            'success': False,
            'error': 'Payment đã được xử lý'
        })
    
    transfer_code = request.POST.get('transfer_code', '').strip()
    bank_account_name = request.POST.get('bank_account_name', '').strip()
    bank_account_number = request.POST.get('bank_account_number', '').strip()
    bank_name = request.POST.get('bank_name', '').strip()
    
    if not transfer_code:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập mã giao dịch'
        })
    
    # Handle uploaded image
    transfer_image = request.FILES.get('transfer_image')
    
    # Update payment
    payment.bank_transfer_code = transfer_code
    payment.bank_account_name = bank_account_name
    payment.bank_account_number = bank_account_number
    payment.bank_name = bank_name
    
    if transfer_image:
        payment.bank_transfer_image = transfer_image
    
    result = BankTransferService.verify_bank_transfer(payment, transfer_code, transfer_image)
    
    if result.get('success'):
        return JsonResponse({
            'success': True,
            'message': result.get('message'),
            'redirect_url': payment.get_absolute_url() if hasattr(payment, 'get_absolute_url') else f'/payment/{payment.id}/status/'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': result.get('error', 'Có lỗi xảy ra')
        })


@login_required
def qr_code_image(request, payment_id):
    """Trả về QR code image cho payment"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return BankTransferService.get_qr_code_image_response(payment)


@login_required
def my_subscription(request):
    """Xem thông tin subscription của user"""
    try:
        subscription = request.user.subscription
        subscription.check_and_update_status()
    except Subscription.DoesNotExist:
        subscription = None
    
    # Get payment history
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'subscription': subscription,
        'payments': payments,
    }
    return render(request, 'payment/my_subscription.html', context)
