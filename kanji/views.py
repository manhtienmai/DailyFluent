import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import KanjiLesson, Kanji, KanjiVocab, UserKanjiProgress

# JLPT levels shown on the levels page, from easiest to hardest
JLPT_ORDER = ['N5', 'N4', 'N3', 'N2', 'N1', 'BT']

# Display labels for segment groupings
JLPT_LABELS = {
    'N5': 'N5',
    'N4': 'N4',
    'N3': 'N3',
    'N2': 'N2',
    'N1': 'N1',
}

JLPT_COLORS = {
    'N5': {'bg': 'bg-emerald-500', 'hover': 'hover:bg-emerald-600', 'badge': 'jb-n5'},
    'N4': {'bg': 'bg-blue-500',    'hover': 'hover:bg-blue-600',    'badge': 'jb-n4'},
    'N3': {'bg': 'bg-amber-500',   'hover': 'hover:bg-amber-600',   'badge': 'jb-n3'},
    'N2': {'bg': 'bg-violet-500',  'hover': 'hover:bg-violet-600',  'badge': 'jb-n2'},
    'N1': {'bg': 'bg-red-500',     'hover': 'hover:bg-red-600',     'badge': 'jb-n1'},
}


def kanji_levels(request):
    """
    Trang Hán tự: chia theo cấp JLPT → bài học → danh sách Hán tự.
    """
    lessons = (
        KanjiLesson.objects
        .prefetch_related('kanjis')
        .order_by('jlpt_level', 'order', 'lesson_number')
    )

    # Group by JLPT level
    grouped = {lvl: [] for lvl in JLPT_ORDER}
    for lesson in lessons:
        if lesson.jlpt_level in grouped:
            grouped[lesson.jlpt_level].append(lesson)

    # Only include levels that have lessons
    jlpt_groups = [
        {
            'level': lvl,
            'label': JLPT_LABELS[lvl],
            'colors': JLPT_COLORS[lvl],
            'lessons': grouped[lvl],
            'total_kanji': sum(l.kanjis.count() for l in grouped[lvl]),
        }
        for lvl in JLPT_ORDER if grouped[lvl]
    ]

    # Active tab: use query param or default to first available
    active_level = request.GET.get('level', jlpt_groups[0]['level'] if jlpt_groups else 'N5')

    return render(request, "kanji/levels.html", {
        "jlpt_groups": jlpt_groups,
        "active_level": active_level,
        "jlpt_colors": JLPT_COLORS,
    })


def kanji_detail(request, char):
    """
    Trang chi tiết + luyện viết Hán tự (tích hợp Dmak).
    """
    kanji = get_object_or_404(Kanji, char=char)

    # Curated vocab examples from KanjiVocab
    kanji_vocab = kanji.vocab_examples.order_by('priority', 'id')[:8]

    progress = None
    if request.user.is_authenticated:
        progress, _ = UserKanjiProgress.objects.get_or_create(
            user=request.user, kanji=kanji,
        )

    return render(request, "kanji/detail.html", {
        "kanji": kanji,
        "kanji_vocab": kanji_vocab,
        "progress": progress,
        "mastered_threshold": 5,
    })


def kanji_practice(request, char="水"):
    """Redirect to detail page."""
    return redirect("kanji:detail", char=char)


@require_POST
@login_required
def update_kanji_progress(request):
    """
    API: POST /kanji/api/progress/update/
    Payload: { "kanji_id": <int>, "passed": <bool> }
    """
    try:
        data = json.loads(request.body)
        kanji_id = int(data["kanji_id"])
        passed = bool(data.get("passed", False))
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"error": f"Invalid payload: {exc}"}, status=400)

    kanji = get_object_or_404(Kanji, pk=kanji_id)
    progress, _ = UserKanjiProgress.objects.get_or_create(
        user=request.user, kanji=kanji,
    )
    progress.record_attempt(passed)

    return JsonResponse({
        "status": progress.status,
        "correct_streak": progress.correct_streak,
        "mastered": progress.status == UserKanjiProgress.STATUS_MASTERED,
    })
