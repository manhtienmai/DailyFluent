from collections import defaultdict

from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from .models import Kanji
from vocab.models import Vocabulary


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
    # Find vocab containing this Kanji (search in Vocabulary table), limit 5
    vocab_qs = (
        Vocabulary.objects
        .filter(is_active=True)
        .filter(Q(jp_kanji__contains=kanji.char) | Q(jp_kana__contains=kanji.char))
        .order_by("-created_at", "-id")[:5]
    )

    return render(request, "kanji/detail.html", {
        "kanji": kanji,
        "vocab_list": vocab_qs,
    })
