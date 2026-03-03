"""Feedback API — list, create, detail, vote, comment."""

from ninja import Router, Schema
from typing import List, Optional

router = Router()


class UserBrief(Schema):
    id: int
    username: str
    email: str


class CommentOut(Schema):
    id: int
    user: UserBrief
    content: str
    is_admin_response: bool
    created_at: str


class FeedbackOut(Schema):
    id: int
    title: str
    description: str
    type: str
    type_display: str
    status: str
    status_display: str
    user: UserBrief
    total_votes: int
    has_voted: bool
    comment_count: int
    created_at: str


class FeedbackDetailOut(FeedbackOut):
    comments: List[CommentOut] = []


class FeedbackIn(Schema):
    title: str
    description: str
    type: str = "feature"


class CommentIn(Schema):
    content: str


@router.get("", response=List[FeedbackOut])
def list_feedback(request, type: str = None, status: str = None, sort: str = "popular"):
    """List feedback items."""
    from feedback.models import FeedbackItem
    qs = FeedbackItem.objects.select_related("user").all()
    if type and type != "all":
        qs = qs.filter(type=type)
    if status and status != "all":
        qs = qs.filter(status=status)
    if sort == "newest":
        qs = qs.order_by("-created_at")
    else:
        # popular = most votes (default)
        from django.db.models import Count
        qs = qs.annotate(vote_count=Count("upvotes")).order_by("-vote_count", "-created_at")
    return [_feedback_out(f, request.user) for f in qs]


@router.post("", response=FeedbackOut)
def create_feedback(request, payload: FeedbackIn):
    """Create a new feedback item."""
    from feedback.models import FeedbackItem
    item = FeedbackItem.objects.create(
        user=request.user,
        title=payload.title,
        description=payload.description,
        type=payload.type,
    )
    return _feedback_out(item, request.user)


@router.get("/{feedback_id}", response=FeedbackDetailOut)
def feedback_detail(request, feedback_id: int):
    """Get feedback detail with comments."""
    from feedback.models import FeedbackItem
    item = FeedbackItem.objects.select_related("user").prefetch_related(
        "comments__user", "upvotes"
    ).get(id=feedback_id)
    data = _feedback_out(item, request.user)
    data["comments"] = [
        {
            "id": c.id,
            "user": {"id": c.user.id, "username": c.user.username, "email": c.user.email},
            "content": c.content,
            "is_admin_response": c.is_admin_response,
            "created_at": c.created_at.isoformat(),
        }
        for c in item.comments.all()
    ]
    return data


@router.post("/{feedback_id}/vote")
def toggle_vote(request, feedback_id: int):
    """Toggle upvote on a feedback item."""
    from feedback.models import FeedbackItem
    item = FeedbackItem.objects.get(id=feedback_id)
    if request.user in item.upvotes.all():
        item.upvotes.remove(request.user)
        voted = False
    else:
        item.upvotes.add(request.user)
        voted = True
    return {"success": True, "has_voted": voted, "total_votes": item.total_votes()}


@router.post("/{feedback_id}/comment", response=CommentOut)
def add_comment(request, feedback_id: int, payload: CommentIn):
    """Add a comment to feedback item."""
    from feedback.models import FeedbackItem, FeedbackComment
    item = FeedbackItem.objects.get(id=feedback_id)
    comment = FeedbackComment.objects.create(
        feedback=item,
        user=request.user,
        content=payload.content,
        is_admin_response=request.user.is_staff,
    )
    return {
        "id": comment.id,
        "user": {"id": request.user.id, "username": request.user.username, "email": request.user.email},
        "content": comment.content,
        "is_admin_response": comment.is_admin_response,
        "created_at": comment.created_at.isoformat(),
    }


def _feedback_out(f, user):
    return {
        "id": f.id,
        "title": f.title,
        "description": f.description,
        "type": f.type,
        "type_display": f.get_type_display_vi(),
        "status": f.status,
        "status_display": f.get_status_display(),
        "user": {"id": f.user.id, "username": f.user.username, "email": f.user.email},
        "total_votes": f.total_votes(),
        "has_voted": user in f.upvotes.all() if hasattr(f, '_prefetched_objects_cache') else f.upvotes.filter(id=user.id).exists(),
        "comment_count": f.comments.count(),
        "created_at": f.created_at.isoformat(),
    }
