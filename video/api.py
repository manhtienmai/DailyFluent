"""Video API — list & detail endpoints."""

from ninja import Router, Schema
from typing import List, Optional

router = Router()


class CategoryOut(Schema):
    id: int
    name: str
    slug: str


class VideoOut(Schema):
    id: int
    title: str
    slug: str
    level: str
    category: Optional[CategoryOut] = None
    description: str
    youtube_id: str
    thumbnail: Optional[str] = None
    duration_seconds: int
    duration_label: str
    view_count: int


class TranscriptLineOut(Schema):
    id: int
    start_time: int
    text: str


class VideoDetailOut(VideoOut):
    transcript_lines: List[TranscriptLineOut] = []


@router.get("", response=List[VideoOut])
def list_videos(request, category: str = None, level: str = None):
    """List all videos, optionally filtered by category or level."""
    from video.models import Video
    qs = Video.objects.select_related("category").all()
    if category:
        qs = qs.filter(category__slug=category)
    if level:
        qs = qs.filter(level=level)
    return [_video_out(v) for v in qs]


@router.get("/categories", response=List[CategoryOut])
def list_categories(request):
    """List all video categories."""
    from video.models import Category
    return list(Category.objects.all())


@router.get("/{slug}", response=VideoDetailOut)
def video_detail(request, slug: str):
    """Get video detail with transcript."""
    from video.models import Video
    v = Video.objects.select_related("category").prefetch_related("transcript_lines").get(slug=slug)
    data = _video_out(v)
    data["transcript_lines"] = [
        {"id": t.id, "start_time": t.start_time, "text": t.text}
        for t in v.transcript_lines.all()
    ]
    return data


def _video_out(v):
    return {
        "id": v.id,
        "title": v.title,
        "slug": v.slug,
        "level": v.level,
        "category": {"id": v.category.id, "name": v.category.name, "slug": v.category.slug} if v.category else None,
        "description": v.description,
        "youtube_id": v.youtube_id,
        "thumbnail": v.thumbnail.url if v.thumbnail else None,
        "duration_seconds": v.duration_seconds,
        "duration_label": v.duration_label,
        "view_count": v.view_count,
    }
