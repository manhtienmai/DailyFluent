# shop/views.py
"""
Views cho Cửa hàng.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import AvatarFrame, UserInventory
from wallet.services import CoinService
from wallet.models import CoinTransaction, UserWallet


@login_required
def shop_list(request):
    """
    Trang hiển thị danh sách sản phẩm trong cửa hàng.
    """
    # Lấy tất cả frames đang active
    frames = AvatarFrame.objects.filter(is_active=True)
    
    # Lọc limited items đã hết hạn
    now = timezone.now()
    frames = frames.filter(
        models.Q(is_limited=False) | 
        models.Q(is_limited=True, available_until__gt=now)
    )
    
    # Lấy danh sách frame user đã mua
    owned_frame_ids = []
    equipped_frame_id = None
    if request.user.is_authenticated:
        user_inventory = UserInventory.objects.filter(user=request.user)
        owned_frame_ids = list(user_inventory.values_list('frame_id', flat=True))
        equipped = user_inventory.filter(is_equipped=True).first()
        if equipped:
            equipped_frame_id = equipped.frame_id
    
    # Lấy wallet info
    wallet = UserWallet.get_or_create_for_user(request.user)
    
    context = {
        'frames': frames,
        'owned_frame_ids': owned_frame_ids,
        'equipped_frame_id': equipped_frame_id,
        'wallet': wallet,
    }
    return render(request, 'shop/shop_list.html', context)


@login_required
@require_POST
def buy_frame(request, frame_id):
    """
    API để mua khung avatar (bypass coin check for demo).
    """
    frame = get_object_or_404(AvatarFrame, id=frame_id, is_active=True)
    
    # Kiểm tra đã mua chưa
    if UserInventory.objects.filter(user=request.user, frame=frame).exists():
        return JsonResponse({
            'success': False,
            'error': 'already_owned',
            'message': 'Bạn đã sở hữu khung này rồi!'
        }, status=400)
    
    # Kiểm tra limited
    if frame.is_limited and frame.available_until:
        if timezone.now() > frame.available_until:
            return JsonResponse({
                'success': False,
                'error': 'expired',
                'message': 'Sản phẩm này đã hết hạn!'
            }, status=400)
    
    # Tạo inventory entry (bypass coin check)
    UserInventory.objects.create(
        user=request.user,
        frame=frame
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Đã mua "{frame.name}" thành công!',
        'frame_id': frame.id
    })


@login_required
@require_POST
def equip_frame(request, frame_id):
    """
    API để trang bị khung avatar.
    """
    inventory_item = get_object_or_404(
        UserInventory, 
        user=request.user, 
        frame_id=frame_id
    )
    inventory_item.equip()
    
    return JsonResponse({
        'success': True,
        'message': f'Đã trang bị "{inventory_item.frame.name}"!',
        'frame_id': frame_id
    })


@login_required
@require_POST
def unequip_frame(request):
    """
    API để bỏ trang bị khung avatar (quay về mặc định).
    """
    UserInventory.objects.filter(
        user=request.user, 
        is_equipped=True
    ).update(is_equipped=False)
    
    return JsonResponse({
        'success': True,
        'message': 'Đã bỏ trang bị khung avatar!'
    })


# Fix import for Q
from django.db import models
