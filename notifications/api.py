"""
Notification & Assignment API endpoints.

All endpoints require JWT authentication.
Teacher-only endpoints check request.user.is_staff.
"""

from datetime import datetime
from typing import List, Optional

from django.contrib.auth import get_user_model
from ninja import Router, Schema

from .models import Assignment, Notification

User = get_user_model()

router = Router()


# ── Schemas ────────────────────────────────────────────────


class NotificationOut(Schema):
    id: int
    category: str
    title: str
    message: str
    link: str
    is_read: bool
    created_at: datetime


class NotificationListOut(Schema):
    items: List[NotificationOut]
    total: int
    page: int
    has_more: bool


class UnreadCountOut(Schema):
    count: int


class SuccessOut(Schema):
    success: bool
    message: str = ""


class AssignmentIn(Schema):
    title: str
    description: str = ""
    quiz_type: str
    quiz_id: str
    link: str = ""
    due_date: Optional[datetime] = None
    student_ids: List[int] = []  # empty = ALL students


class AssignmentOut(Schema):
    id: int
    title: str
    description: str
    quiz_type: str
    quiz_id: str
    link: str
    due_date: Optional[datetime] = None
    teacher_name: str
    created_at: datetime


# ── Notification endpoints ─────────────────────────────────


@router.get("/", response=NotificationListOut)
def list_notifications(request, page: int = 1, category: str = ""):
    """List notifications for the current user (paginated, 20/page)."""
    PAGE_SIZE = 20

    qs = Notification.objects.filter(user=request.user)
    if category:
        qs = qs.filter(category=category)

    total = qs.count()
    offset = (page - 1) * PAGE_SIZE
    items = list(qs[offset : offset + PAGE_SIZE])

    return {
        "items": [
            {
                "id": n.id,
                "category": n.category,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in items
        ],
        "total": total,
        "page": page,
        "has_more": offset + PAGE_SIZE < total,
    }


@router.get("/unread-count", response=UnreadCountOut)
def unread_count(request):
    """Get count of unread notifications."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {"count": count}


@router.post("/{notification_id}/read", response=SuccessOut)
def mark_read(request, notification_id: int):
    """Mark a single notification as read."""
    updated = Notification.objects.filter(
        id=notification_id, user=request.user
    ).update(is_read=True)
    if updated:
        return {"success": True}
    return {"success": False, "message": "Notification not found."}


@router.post("/read-all", response=SuccessOut)
def mark_all_read(request):
    """Mark all unread notifications as read."""
    count = Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True
    )
    return {"success": True, "message": f"Marked {count} notifications as read."}


# ── Assignment endpoints ───────────────────────────────────


@router.get("/assignments", response=List[AssignmentOut])
def list_assignments(request):
    """List assignments for the current user."""
    qs = Assignment.objects.filter(assigned_to=request.user).select_related("teacher")
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "quiz_type": a.quiz_type,
            "quiz_id": a.quiz_id,
            "link": a.link,
            "due_date": a.due_date,
            "teacher_name": a.teacher.get_full_name() or a.teacher.username,
            "created_at": a.created_at,
        }
        for a in qs
    ]


@router.post("/assignments", response={201: SuccessOut, 403: SuccessOut})
def create_assignment(request, payload: AssignmentIn):
    """Create an assignment (teacher/staff only). Generates notifications."""
    if not request.user.is_staff:
        return 403, {"success": False, "message": "Only teachers can create assignments."}

    assignment = Assignment.objects.create(
        teacher=request.user,
        title=payload.title,
        description=payload.description,
        quiz_type=payload.quiz_type,
        quiz_id=payload.quiz_id,
        link=payload.link,
        due_date=payload.due_date,
    )

    # Assign to specific students or ALL
    if payload.student_ids:
        students = User.objects.filter(id__in=payload.student_ids, is_active=True)
    else:
        students = User.objects.filter(is_active=True, is_staff=False)

    assignment.assigned_to.set(students)
    count = assignment.create_notifications()

    return 201, {
        "success": True,
        "message": f"Assignment created. Notified {count} students.",
    }
