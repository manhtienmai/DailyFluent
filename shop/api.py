"""
Shop API router.

Endpoints:
  GET  /api/v1/shop/frames          – List active avatar frames (with owned/equipped flags)
  POST /api/v1/shop/buy/{frame_id}  – Purchase a frame
  POST /api/v1/shop/equip/{frame_id}– Equip an owned frame
  POST /api/v1/shop/unequip         – Remove currently equipped frame
"""

from typing import List, Optional

from ninja import Router, Schema
from django.db import models as db_models
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import AvatarFrame, UserInventory

router = Router()


# ── Schemas ────────────────────────────────────────────────

class AvatarFrameOut(Schema):
    id: int
    name: str
    slug: str
    description: str
    price: int
    rarity: str
    css_gradient: str
    css_animation: str
    border_width: int
    preview_image: Optional[str] = None
    is_limited: bool
    owned: bool
    equipped: bool


class ShopActionOut(Schema):
    success: bool
    message: str


# ── Endpoints ──────────────────────────────────────────────

@router.get("/frames", response=List[AvatarFrameOut])
def list_frames(request):
    """Return all available frames with ownership and equipped status for the user."""
    now = timezone.now()
    frames = AvatarFrame.objects.filter(is_active=True).filter(
        db_models.Q(is_limited=False)
        | db_models.Q(is_limited=True, available_until__gt=now)
    )

    owned_ids: set[int] = set(
        UserInventory.objects.filter(user=request.user).values_list("frame_id", flat=True)
    )
    equipped_item = (
        UserInventory.objects.filter(user=request.user, is_equipped=True).first()
    )
    equipped_id: Optional[int] = equipped_item.frame_id if equipped_item else None

    return [
        AvatarFrameOut(
            id=frame.id,
            name=frame.name,
            slug=frame.slug,
            description=frame.description,
            price=frame.price,
            rarity=frame.rarity,
            css_gradient=frame.css_gradient,
            css_animation=frame.css_animation,
            border_width=frame.border_width,
            preview_image=str(frame.preview_image.url) if frame.preview_image else None,
            is_limited=frame.is_limited,
            owned=frame.id in owned_ids,
            equipped=frame.id == equipped_id,
        )
        for frame in frames
    ]


@router.post("/buy/{frame_id}", response={200: ShopActionOut, 400: ShopActionOut})
def buy_frame(request, frame_id: int):
    """Purchase an avatar frame. Returns 400 if already owned or expired."""
    frame = get_object_or_404(AvatarFrame, id=frame_id, is_active=True)

    if UserInventory.objects.filter(user=request.user, frame=frame).exists():
        return 400, ShopActionOut(success=False, message="Bạn đã sở hữu khung này rồi!")

    if frame.is_limited and frame.available_until and timezone.now() > frame.available_until:
        return 400, ShopActionOut(success=False, message="Sản phẩm này đã hết hạn!")

    UserInventory.objects.create(user=request.user, frame=frame)
    return 200, ShopActionOut(success=True, message=f'Đã mua "{frame.name}" thành công!')


@router.post("/equip/{frame_id}", response={200: ShopActionOut, 404: ShopActionOut})
def equip_frame(request, frame_id: int):
    """Equip an owned frame. Returns 404 if the user doesn't own it."""
    item = get_object_or_404(UserInventory, user=request.user, frame_id=frame_id)
    item.equip()
    return 200, ShopActionOut(success=True, message=f'Đã trang bị "{item.frame.name}"!')


@router.post("/unequip", response=ShopActionOut)
def unequip_frame(request):
    """Remove the currently equipped frame (revert to default avatar)."""
    UserInventory.objects.filter(user=request.user, is_equipped=True).update(
        is_equipped=False
    )
    return ShopActionOut(success=True, message="Đã bỏ trang bị khung avatar!")
