from collections import defaultdict

from django.shortcuts import get_object_or_404, render
from .models import Kanji


def kanji_levels(request):
    """
    Trang giống screenshot: group Kanji theo level.
    """
    kanji_qs = Kanji.objects.all().order_by("level", "char")

    levels = defaultdict(list)
    for k in kanji_qs:
        levels[k.level].append(k)

    sorted_levels = sorted(levels.items(), key=lambda x: x[0])

    return render(request, "kanji/levels.html", {
        "levels": sorted_levels,
    })


def kanji_detail(request, char):
    """
    Trang chi tiết 1 kanji: chữ to, keyword, list từ vựng liên quan.
    """
    kanji = get_object_or_404(Kanji, char=char)
    vocab_qs = kanji.vocabulary_items.filter(is_active=True).order_by("jp_kana")

    return render(request, "kanji/detail.html", {
        "kanji": kanji,
        "vocab_list": vocab_qs,
    })
