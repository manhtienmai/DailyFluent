from django.shortcuts import render, get_object_or_404
from .models import GrammarPoint, GrammarLevel


def grammar_list(request):
    level = request.GET.get("level", "").upper()
    points = GrammarPoint.objects.filter(is_active=True)
    if level in dict(GrammarLevel.choices):
        points = points.filter(level=level)

    levels = [code for code, _ in GrammarLevel.choices]
    return render(
        request,
        "grammar/list.html",
        {
            "points": points.order_by("level", "title"),
            "level": level,
            "levels": levels,
        },
    )


def grammar_detail(request, slug):
    point = get_object_or_404(GrammarPoint, slug=slug, is_active=True)
    examples = [line.strip() for line in (point.examples or "").splitlines() if line.strip()]
    return render(
        request,
        "grammar/detail.html",
        {
            "point": point,
            "examples": examples,
        },
    )

