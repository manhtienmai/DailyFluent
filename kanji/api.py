"""
Kanji API router.

Endpoints:
  GET  /api/v1/kanji/levels       – All JLPT levels with lessons (public)
  GET  /api/v1/kanji/{char}       – Kanji detail + vocab + progress (public)
  POST /api/v1/kanji/progress     – Record a practice attempt (auth required)
"""

from typing import List, Optional

from ninja import Router, Schema
from django.shortcuts import get_object_or_404

from .models import Kanji, KanjiLesson, KanjiVocab, UserKanjiProgress

router = Router()

JLPT_ORDER = ["N5", "N4", "N3", "N2", "N1", "BT"]
# N1 entries are multi-character vocabulary, not single kanji → exclude from kanji grid
KANJI_LEVELS_ORDER = ["N5", "N4", "N3", "N2", "BT"]


# ── Schemas ────────────────────────────────────────────────

class KanjiSummaryOut(Schema):
    id: int
    char: str
    keyword: str
    sino_vi: str
    order: int


class KanjiLessonOut(Schema):
    id: int
    jlpt_level: str
    lesson_number: int
    topic: str
    order: int
    kanjis: List[KanjiSummaryOut]


class JLPTGroupOut(Schema):
    level: str
    lessons: List[KanjiLessonOut]
    total_kanji: int


class KanjiVocabOut(Schema):
    id: int
    word: str
    reading: str
    meaning: str
    priority: int
    vocabulary_id: Optional[int] = None
    jlpt_level: str = ""


class KanjiOut(Schema):
    id: int
    char: str
    sino_vi: str
    keyword: str
    onyomi: str
    kunyomi: str
    meaning_vi: str
    strokes: Optional[int] = None
    note: str
    formation: str = ""
    jlpt_level: str


class KanjiProgressOut(Schema):
    status: str
    correct_streak: int
    mastered: bool


class KanjiSiblingOut(Schema):
    char: str
    sino_vi: str


class KanjiDetailOut(Schema):
    kanji: KanjiOut
    vocab: List[KanjiVocabOut]
    kanji_map: dict = {}  # char -> sino_vi for kanji breakdown
    lesson_label: str = ""
    kanji_index: int = 0  # 1-based
    kanji_total: int = 0
    progress: Optional[KanjiProgressOut] = None
    prev_kanji: Optional[KanjiSiblingOut] = None
    next_kanji: Optional[KanjiSiblingOut] = None


class ProgressIn(Schema):
    kanji_id: int
    passed: bool


class AddToStudyIn(Schema):
    kanji_vocab_ids: List[int]


class AddToStudyOut(Schema):
    added: int
    already: int


class AddAllByLevelIn(Schema):
    jlpt_level: str


class AddAllByLevelOut(Schema):
    added: int
    already: int
    total: int


class RemoveFromStudyIn(Schema):
    kanji_vocab_ids: List[int]


class RemoveFromStudyOut(Schema):
    removed: int


# ── Endpoints ──────────────────────────────────────────────


class N1VocabItemOut(Schema):
    id: int
    char: str
    sino_vi: str
    onyomi: str
    kunyomi: str
    meaning_vi: str
    order: int
    lesson_number: int
    lesson_topic: str


@router.get("/n1-vocab", response=list[dict], auth=None)
def n1_vocab_list(request):
    """Return all N1 vocabulary grouped by lesson for the /jlpt/n1/vocabulary page."""
    lessons = (
        KanjiLesson.objects
        .filter(jlpt_level="N1")
        .prefetch_related("kanjis")
        .order_by("lesson_number")
    )
    result = []
    global_order = 1
    for lesson in lessons:
        for k in lesson.kanjis.order_by("order", "id"):
            result.append({
                "id": k.id,
                "stt": global_order,
                "char": k.char,
                "onyomi": k.onyomi,
                "kunyomi": k.kunyomi,
                "sino_vi": k.sino_vi,
                "meaning_vi": k.meaning_vi,
                "lesson_number": lesson.lesson_number,
                "lesson_topic": lesson.topic,
            })
            global_order += 1
    return result

@router.get("/levels", response=List[JLPTGroupOut], auth=None)
def kanji_levels(request):
    """Return all JLPT levels grouped with their lessons and kanji characters."""
    from django.core.cache import cache

    cache_key = "kanji_levels_v2"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    lessons = (
        KanjiLesson.objects
        .prefetch_related("kanjis")
        .order_by("jlpt_level", "order", "lesson_number")
    )

    grouped: dict[str, list] = {lvl: [] for lvl in KANJI_LEVELS_ORDER}
    for lesson in lessons:
        if lesson.jlpt_level in grouped:
            grouped[lesson.jlpt_level].append(lesson)

    result = [
        JLPTGroupOut(
            level=lvl,
            lessons=[
                KanjiLessonOut(
                    id=lesson.id,
                    jlpt_level=lesson.jlpt_level,
                    lesson_number=lesson.lesson_number,
                    topic=lesson.topic,
                    order=lesson.order,
                    kanjis=[
                        KanjiSummaryOut(
                            id=k.id,
                            char=k.char,
                            keyword=k.keyword,
                            sino_vi=k.sino_vi,
                            order=k.order,
                        )
                        for k in lesson.kanjis.all()
                    ],
                )
                for lesson in grouped[lvl]
            ],
            total_kanji=sum(len(lesson.kanjis.all()) for lesson in grouped[lvl]),
        )
        for lvl in KANJI_LEVELS_ORDER
        if grouped[lvl]
    ]
    cache.set(cache_key, result, 3600)  # 1 hour
    return result


class UserProgressItemOut(Schema):
    kanji_id: int
    status: str
    correct_streak: int


@router.get("/my-progress", response=List[UserProgressItemOut])
def my_kanji_progress(request):
    """Return all kanji progress for the current user."""
    entries = UserKanjiProgress.objects.filter(user=request.user)
    return [
        UserProgressItemOut(
            kanji_id=e.kanji_id,
            status=e.status,
            correct_streak=e.correct_streak,
        )
        for e in entries
    ]


@router.post("/progress", response=KanjiProgressOut)
def update_progress(request, payload: ProgressIn):
    """Record the result of a kanji practice attempt."""
    kanji = get_object_or_404(Kanji, pk=payload.kanji_id)
    progress, _ = UserKanjiProgress.objects.get_or_create(
        user=request.user, kanji=kanji
    )
    progress.record_attempt(payload.passed)
    return KanjiProgressOut(
        status=progress.status,
        correct_streak=progress.correct_streak,
        mastered=progress.status == UserKanjiProgress.STATUS_MASTERED,
    )


@router.get("/{char}", response=KanjiDetailOut, auth=None)
def kanji_detail(request, char: str):
    """
    Return detail for a single kanji character.
    Includes progress if the user is authenticated.
    """
    kanji = get_object_or_404(Kanji, char=char)
    vocab = list(kanji.vocab_examples.order_by("priority", "id")[:8])

    progress_out: Optional[KanjiProgressOut] = None
    if request.user.is_authenticated:
        progress, _ = UserKanjiProgress.objects.get_or_create(
            user=request.user, kanji=kanji
        )
        progress_out = KanjiProgressOut(
            status=progress.status,
            correct_streak=progress.correct_streak,
            mastered=progress.status == UserKanjiProgress.STATUS_MASTERED,
        )

    # ── Siblings + position (prev / next in same lesson) ──
    prev_out: Optional[KanjiSiblingOut] = None
    next_out: Optional[KanjiSiblingOut] = None
    lesson_label = ""
    kanji_index = 0
    kanji_total = 0
    if kanji.lesson:
        lesson_label = f"{kanji.lesson.jlpt_level} Bài {kanji.lesson.lesson_number}"
        siblings = list(
            kanji.lesson.kanjis.order_by("order", "id").values_list("id", "char", "sino_vi")
        )
        kanji_total = len(siblings)
        idx = next((i for i, s in enumerate(siblings) if s[0] == kanji.id), None)
        if idx is not None:
            kanji_index = idx + 1  # 1-based
            if idx > 0:
                prev_out = KanjiSiblingOut(char=siblings[idx - 1][1], sino_vi=siblings[idx - 1][2])
            if idx < len(siblings) - 1:
                next_out = KanjiSiblingOut(char=siblings[idx + 1][1], sino_vi=siblings[idx + 1][2])

    # ── Build kanji_map: all unique kanji chars in vocab → sino_vi ──
    all_chars = set()
    for v in vocab:
        for ch in v.word:
            if '\u4e00' <= ch <= '\u9fff':  # CJK Unified Ideographs
                all_chars.add(ch)
    # Remove current kanji since it's already shown
    all_chars.discard(kanji.char)
    kanji_map_data = {kanji.char: kanji.sino_vi}
    if all_chars:
        from kanji.models import Kanji as KanjiModel
        for k in KanjiModel.objects.filter(char__in=all_chars).values_list('char', 'sino_vi'):
            kanji_map_data[k[0]] = k[1]

    return KanjiDetailOut(
        kanji=KanjiOut(
            id=kanji.id,
            char=kanji.char,
            sino_vi=kanji.sino_vi,
            keyword=kanji.keyword,
            onyomi=kanji.onyomi,
            kunyomi=kanji.kunyomi,
            meaning_vi=kanji.meaning_vi,
            strokes=kanji.strokes,
            note=kanji.note,
            formation=kanji.formation,
            jlpt_level=kanji.jlpt_level,
        ),
        vocab=[
            KanjiVocabOut(
                id=v.id,
                word=v.word,
                reading=v.reading,
                meaning=v.meaning,
                priority=v.priority,
                vocabulary_id=v.vocabulary_id,
                jlpt_level=v.jlpt_level or "",
            )
            for v in vocab
        ],
        kanji_map=kanji_map_data,
        lesson_label=lesson_label,
        kanji_index=kanji_index,
        kanji_total=kanji_total,
        progress=progress_out,
        prev_kanji=prev_out,
        next_kanji=next_out,
    )






@router.post("/vocab/add-to-study", response=AddToStudyOut)
def add_vocab_to_study(request, payload: AddToStudyIn):
    """Add selected kanji vocab words to the user's study set."""
    from vocab.models import (
        Vocabulary, WordEntry, WordDefinition,
        VocabularySet, SetItem,
    )

    # Get or create user's "Từ vựng Kanji" set
    study_set, _ = VocabularySet.objects.get_or_create(
        owner=request.user,
        title="Từ vựng Kanji",
        defaults={
            'language': 'jp',
            'status': 'published',
            'is_public': False,
        },
    )

    added = 0
    already = 0

    kanji_vocabs = list(KanjiVocab.objects.filter(id__in=payload.kanji_vocab_ids))

    # Batch: pre-create Vocabulary chain for items without vocabulary_id
    unlinked = [kv for kv in kanji_vocabs if not kv.vocabulary_id]
    if unlinked:
        for kv in unlinked:
            vocab_obj, _ = Vocabulary.objects.get_or_create(
                word=kv.word,
                defaults={
                    'language': 'jp',
                    'extra_data': {'reading': kv.reading},
                },
            )
            entry, _ = WordEntry.objects.get_or_create(
                vocab=vocab_obj,
                part_of_speech='',
                defaults={'ipa': kv.reading},
            )
            WordDefinition.objects.get_or_create(
                entry=entry,
                meaning=kv.meaning,
            )
            kv.vocabulary = vocab_obj
            kv.save(update_fields=['vocabulary'])

    # Batch: get all definitions in one query
    vocab_ids = [kv.vocabulary_id for kv in kanji_vocabs if kv.vocabulary_id]
    definitions_map = {}
    if vocab_ids:
        for defn in WordDefinition.objects.filter(
            entry__vocab_id__in=vocab_ids
        ).select_related('entry'):
            if defn.entry.vocab_id not in definitions_map:
                definitions_map[defn.entry.vocab_id] = defn

    # Batch: get existing set items to avoid individual get_or_create
    existing_defn_ids = set(
        SetItem.objects.filter(
            vocabulary_set=study_set
        ).values_list('definition_id', flat=True)
    )

    items_to_create = []
    current_count = len(existing_defn_ids)
    for kv in kanji_vocabs:
        definition = definitions_map.get(kv.vocabulary_id)
        if not definition:
            continue
        if definition.id in existing_defn_ids:
            already += 1
        else:
            items_to_create.append(SetItem(
                vocabulary_set=study_set,
                definition=definition,
                display_order=current_count,
            ))
            existing_defn_ids.add(definition.id)
            current_count += 1
            added += 1

    if items_to_create:
        SetItem.objects.bulk_create(items_to_create, ignore_conflicts=True)

    return AddToStudyOut(added=added, already=already)


@router.post("/vocab/add-all-by-level", response=AddAllByLevelOut)
def add_all_vocab_by_level(request, payload: AddAllByLevelIn):
    """Add ALL vocab from all kanji lessons of a JLPT level to user's study set."""
    # Get all KanjiVocab IDs for this level
    all_vocab_ids = list(
        KanjiVocab.objects.filter(
            kanji__lesson__jlpt_level=payload.jlpt_level
        ).values_list('id', flat=True)
    )
    total = len(all_vocab_ids)
    if total == 0:
        return AddAllByLevelOut(added=0, already=0, total=0)

    # Reuse existing add_vocab_to_study logic
    result = add_vocab_to_study(request, AddToStudyIn(kanji_vocab_ids=all_vocab_ids))
    return AddAllByLevelOut(added=result.added, already=result.already, total=total)


@router.post("/vocab/remove-from-study", response=RemoveFromStudyOut)
def remove_vocab_from_study(request, payload: RemoveFromStudyIn):
    """Remove selected kanji vocab words from the user's study set."""
    from vocab.models import VocabularySet, SetItem

    try:
        study_set = VocabularySet.objects.get(
            owner=request.user, title="Từ vựng Kanji"
        )
    except VocabularySet.DoesNotExist:
        return RemoveFromStudyOut(removed=0)

    # Get the vocabulary_ids for the given kanji_vocab_ids
    vocab_ids = list(
        KanjiVocab.objects.filter(
            id__in=payload.kanji_vocab_ids,
            vocabulary_id__isnull=False,
        ).values_list('vocabulary_id', flat=True)
    )
    if not vocab_ids:
        return RemoveFromStudyOut(removed=0)

    # Delete SetItems that match
    deleted_count, _ = SetItem.objects.filter(
        vocabulary_set=study_set,
        definition__entry__vocab_id__in=vocab_ids,
    ).delete()

    return RemoveFromStudyOut(removed=deleted_count)


class VocabKanjiBreakdownOut(Schema):
    char: str
    sino_vi: str
    meaning_vi: str
    formation: str = ""


class VocabWordDetailOut(Schema):
    word: str
    reading: str
    meaning: str
    kanji_breakdown: List[VocabKanjiBreakdownOut]
    related_vocab: List[KanjiVocabOut]


@router.get("/vocab/word/{word}", response=VocabWordDetailOut)
def vocab_word_detail(request, word: str):
    """Get detailed info for a vocab word, including kanji breakdown."""
    kv = get_object_or_404(KanjiVocab, word=word)

    # Build kanji breakdown
    kanji_chars = [ch for ch in word if '\u4e00' <= ch <= '\u9fff']
    breakdown = []
    if kanji_chars:
        kanji_objs = {k.char: k for k in Kanji.objects.filter(char__in=kanji_chars)}
        for ch in kanji_chars:
            if ch in kanji_objs:
                k = kanji_objs[ch]
                breakdown.append(VocabKanjiBreakdownOut(
                    char=k.char, sino_vi=k.sino_vi,
                    meaning_vi=k.meaning_vi, formation=k.formation,
                ))

    # Related vocab: other words from the same kanji
    related = (
        KanjiVocab.objects
        .filter(kanji=kv.kanji)
        .exclude(id=kv.id)
        .order_by('priority', 'id')[:8]
    )

    return VocabWordDetailOut(
        word=kv.word,
        reading=kv.reading,
        meaning=kv.meaning,
        kanji_breakdown=breakdown,
        related_vocab=[
            KanjiVocabOut(
                id=rv.id, word=rv.word, reading=rv.reading,
                meaning=rv.meaning, priority=rv.priority,
                vocabulary_id=rv.vocabulary_id,
            )
            for rv in related
        ],
    )


# ── Quiz Schemas ──────────────────────────────────────────

class QuizOptionOut(Schema):
    text: str
    is_correct: bool


class QuizQuestionOut(Schema):
    kanji_id: int
    char: str
    sino_vi: str
    onyomi: str = ""
    kunyomi: str = ""
    meaning_vi: str = ""
    question_type: str
    options: List[QuizOptionOut]


class QuizLessonOut(Schema):
    lesson_id: int
    lesson_label: str
    questions: List[QuizQuestionOut]
    total: int


# ── Quiz Endpoint ─────────────────────────────────────────

@router.get("/quiz/{lesson_id}/status", auth=None)
def kanji_quiz_status(request, lesson_id: int):
    """
    Check quiz readiness for a lesson.
    Returns list of kanji with has_quiz flag so frontend can drive generation.
    """
    from .models import KanjiQuizQuestion

    lesson = get_object_or_404(KanjiLesson, pk=lesson_id)
    lesson_label = f"{lesson.jlpt_level} Bài {lesson.lesson_number}: {lesson.topic}"

    kanjis = list(lesson.kanjis.order_by('order', 'id'))
    quiz_kanji_ids = set(
        KanjiQuizQuestion.objects.filter(kanji__lesson=lesson)
        .values_list('kanji_id', flat=True)
        .distinct()
    )

    items = []
    for k in kanjis:
        items.append({
            "id": k.id,
            "char": k.char,
            "sino_vi": k.sino_vi,
            "has_quiz": k.id in quiz_kanji_ids,
        })

    return {
        "lesson_id": lesson.id,
        "lesson_label": lesson_label,
        "items": items,
        "total": len(items),
        "ready": sum(1 for i in items if i["has_quiz"]),
    }


@router.post("/quiz/generate-one", auth=None)
def kanji_quiz_generate_one(request):
    """Generate quiz for a single kanji. Returns success/error."""
    import json
    body = json.loads(request.body)
    kanji_id = body.get("kanji_id")
    if not kanji_id:
        return {"status": "error", "message": "kanji_id required"}

    from .services.quiz_generator import generate_and_save_for_kanji
    try:
        result, error = generate_and_save_for_kanji(kanji_id)
        if error:
            return {"status": "error", "message": error}
        from .models import Kanji as KanjiModel
        k = KanjiModel.objects.get(pk=kanji_id)
        return {"status": "success", "char": k.char}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/quiz/{lesson_id}", response=QuizLessonOut, auth=None)
def kanji_quiz(request, lesson_id: int, quiz_type: str = "all"):
    """
    Return shuffled quiz questions for a lesson.
    Assumes quiz data already exists (use /status + /generate-one first).
    quiz_type: 'meaning' | 'reading' | 'kanji' | 'all'
    """
    import random
    from .models import KanjiQuizQuestion

    lesson = get_object_or_404(KanjiLesson, pk=lesson_id)
    lesson_label = f"{lesson.jlpt_level} Bài {lesson.lesson_number}: {lesson.topic}"

    qs = KanjiQuizQuestion.objects.filter(
        kanji__lesson=lesson,
    ).select_related('kanji')

    if quiz_type != "all":
        qs = qs.filter(question_type=quiz_type)

    questions = []
    for qq in qs:
        options = [QuizOptionOut(text=qq.correct_answer, is_correct=True)]
        for d in qq.distractors[:3]:
            options.append(QuizOptionOut(text=d, is_correct=False))
        random.shuffle(options)

        questions.append(QuizQuestionOut(
            kanji_id=qq.kanji.id,
            char=qq.kanji.char,
            sino_vi=qq.kanji.sino_vi,
            onyomi=qq.kanji.onyomi or "",
            kunyomi=qq.kanji.kunyomi or "",
            meaning_vi=qq.kanji.meaning_vi or "",
            question_type=qq.question_type,
            options=options,
        ))

    random.shuffle(questions)

    return QuizLessonOut(
        lesson_id=lesson.id,
        lesson_label=lesson_label,
        questions=questions,
        total=len(questions),
    )
