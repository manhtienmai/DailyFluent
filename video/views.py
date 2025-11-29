from django.shortcuts import render, get_object_or_404
from .models import Video, Category


def video_list(request):
    category_slug = request.GET.get("category")

    categories = Category.objects.all()
    videos = Video.objects.select_related("category").order_by("-created_at")

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        videos = videos.filter(category=active_category)

    context = {
        "categories": categories,
        "videos": videos,
        "active_category": active_category,
    }
    return render(request, "video/video_list.html", context)


def video_detail(request, slug):
    video = get_object_or_404(
        Video.objects.select_related("category").prefetch_related("transcript_lines"),
        slug=slug,
    )
    categories = Category.objects.all()

    return render(
        request,
        "video/video_detail.html",
        {"video": video, "categories": categories},
    )
