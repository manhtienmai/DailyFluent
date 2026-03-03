"""
Admin CRUD API — comprehensive endpoints for the Next.js admin dashboard.
Covers: Vocabulary, VocabularySet, Exam, Users, Kanji, Grammar, etc.
"""

from ninja import Router, Schema, Query, Field
from ninja.pagination import paginate, PageNumberPagination
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from typing import Optional, Any
from datetime import datetime as dt
import json

User = get_user_model()
router = Router()


# ═══════════════════════════════════════════════════════════
# ── Helper: Staff-only check ──
# ═══════════════════════════════════════════════════════════

def staff_required(request):
    return request.user and request.user.is_staff


# ═══════════════════════════════════════════════════════════
# ── VOCABULARY ──
# ═══════════════════════════════════════════════════════════

class VocabOut(Schema):
    id: int
    word: str
    language: str
    extra_data: Optional[dict] = None
    entry_count: int = 0
    first_meaning: Optional[str] = None
    first_pos: Optional[str] = None

class VocabDetailOut(Schema):
    id: int
    word: str
    language: str
    extra_data: Optional[dict] = None
    entries: list[dict] = []

class VocabSetOut(Schema):
    id: int
    title: str
    collection: Optional[str] = None
    status: str = ""
    is_public: bool = True
    toeic_level: Optional[int] = None
    set_number: Optional[int] = None
    word_count: int = 0

class VocabSetDetailOut(Schema):
    id: int
    title: str
    collection: Optional[str] = None
    status: str = ""
    is_public: bool = True
    toeic_level: Optional[int] = None
    set_number: Optional[int] = None
    description: Optional[str] = None
    word_count: int = 0
    items: list[dict] = []


@router.get("/vocab/", response=list[VocabOut])
@paginate(PageNumberPagination, page_size=50)
def vocab_list(request, search: str = "", language: str = "all"):
    if not staff_required(request):
        return []
    from vocab.models import Vocabulary, WordDefinition
    qs = Vocabulary.objects.annotate(entry_count=Count('entries'))
    if search:
        qs = qs.filter(
            Q(word__icontains=search) |
            Q(extra_data__reading__icontains=search) |
            Q(extra_data__han_viet__icontains=search) |
            Q(entries__definitions__meaning__icontains=search)
        ).distinct()
    if language and language != "all":
        lang_map = {"ja": "jp", "jp": "jp", "en": "en"}
        qs = qs.filter(language=lang_map.get(language, language))
    results = []
    for v in qs.order_by('-id').prefetch_related('entries__definitions'):
        first_meaning = None
        first_pos = None
        for entry in v.entries.all():
            for defn in entry.definitions.all():
                if defn.meaning:
                    first_meaning = defn.meaning
                    first_pos = entry.part_of_speech
                    break
            if first_meaning:
                break
        results.append({
            'id': v.id, 'word': v.word, 'language': v.language,
            'extra_data': v.extra_data, 'entry_count': v.entry_count,
            'first_meaning': first_meaning, 'first_pos': first_pos,
        })
    return results


# ── Vocab Set simple list (must appear before {vocab_id} catch-all) ──

class VocabSetSimpleOut(Schema):
    id: int
    title: str
    collection: Optional[str] = None
    toeic_level: Optional[int] = None

@router.get("/vocab/sets-simple/", response=list[VocabSetSimpleOut])
def vocab_set_simple_list(request):
    """Lightweight set list for select dropdowns."""
    if not staff_required(request):
        return []
    try:
        from vocab.models import VocabularySet
        qs = VocabularySet.objects.select_related('collection').order_by('-id')[:200]
        return [
            {
                'id': vs.id,
                'title': vs.title,
                'collection': vs.collection.name if vs.collection else None,
                'toeic_level': vs.toeic_level,
            }
            for vs in qs
        ]
    except Exception:
        return []


# ── Vocab Create (quick) ──

class VocabCreateIn(Schema):
    word: str
    language: str = "jp"
    reading: str = ""
    han_viet: str = ""
    part_of_speech: str = "noun"
    meaning: str = ""

@router.post("/vocab/create/")
def vocab_create(request, payload: VocabCreateIn):
    """Create a vocabulary with entry + definition in one step."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import Vocabulary, WordEntry, WordDefinition
    try:
        extra_data = {}
        if payload.reading:
            extra_data['reading'] = payload.reading
        if payload.han_viet:
            extra_data['han_viet'] = payload.han_viet

        vocab, v_created = Vocabulary.objects.get_or_create(
            word=payload.word,
            defaults={'language': payload.language, 'extra_data': extra_data},
        )
        if not v_created and extra_data:
            changed = False
            for k, val in extra_data.items():
                if val and vocab.extra_data.get(k) != val:
                    vocab.extra_data[k] = val
                    changed = True
            if changed:
                vocab.save(update_fields=['extra_data'])

        entry, _ = WordEntry.objects.get_or_create(
            vocab=vocab, part_of_speech=payload.part_of_speech,
        )

        defn = None
        if payload.meaning:
            defn, _ = WordDefinition.objects.get_or_create(
                entry=entry, meaning=payload.meaning,
            )

        return {"success": True, "id": vocab.id, "created": v_created}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ── Vocab Update ──

class VocabUpdateIn(Schema):
    word: Optional[str] = None
    language: Optional[str] = None
    reading: Optional[str] = None
    han_viet: Optional[str] = None

@router.put("/vocab/update/{vocab_id}/")
def vocab_update(request, vocab_id: int, payload: VocabUpdateIn):
    """Update a vocabulary's word, language, or extra_data fields."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import Vocabulary
    try:
        vocab = Vocabulary.objects.get(id=vocab_id)
        if payload.word is not None:
            vocab.word = payload.word
        if payload.language is not None:
            vocab.language = payload.language
        if payload.reading is not None:
            vocab.extra_data['reading'] = payload.reading
        if payload.han_viet is not None:
            vocab.extra_data['han_viet'] = payload.han_viet
        vocab.save()
        return {"success": True}
    except Vocabulary.DoesNotExist:
        return {"success": False, "message": "Vocabulary not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ── Entry CRUD ──

class EntryIn(Schema):
    part_of_speech: str = "noun"
    ipa: str = ""

@router.post("/vocab/{vocab_id}/entries/")
def entry_create(request, vocab_id: int, payload: EntryIn):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import Vocabulary, WordEntry
    try:
        vocab = Vocabulary.objects.get(id=vocab_id)
        entry, created = WordEntry.objects.get_or_create(
            vocab=vocab, part_of_speech=payload.part_of_speech,
            defaults={'ipa': payload.ipa},
        )
        return {"success": True, "id": entry.id, "created": created}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/vocab/{vocab_id}/entries/{entry_id}/")
def entry_update(request, vocab_id: int, entry_id: int, payload: EntryIn):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import WordEntry
    try:
        WordEntry.objects.filter(id=entry_id, vocab_id=vocab_id).update(
            part_of_speech=payload.part_of_speech, ipa=payload.ipa,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/vocab/{vocab_id}/entries/{entry_id}/")
def entry_delete(request, vocab_id: int, entry_id: int):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import WordEntry
    WordEntry.objects.filter(id=entry_id, vocab_id=vocab_id).delete()
    return {"success": True}


# ── Definition CRUD ──

class DefinitionIn(Schema):
    meaning: str
    extra_data: Optional[dict] = None

@router.post("/vocab/{vocab_id}/entries/{entry_id}/definitions/")
def definition_create(request, vocab_id: int, entry_id: int, payload: DefinitionIn):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import WordEntry, WordDefinition
    try:
        entry = WordEntry.objects.get(id=entry_id, vocab_id=vocab_id)
        defn = WordDefinition.objects.create(
            entry=entry, meaning=payload.meaning,
            extra_data=payload.extra_data or {},
        )
        return {"success": True, "id": defn.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/vocab/{vocab_id}/entries/{entry_id}/definitions/{def_id}/")
def definition_update(request, vocab_id: int, entry_id: int, def_id: int, payload: DefinitionIn):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import WordDefinition
    try:
        WordDefinition.objects.filter(id=def_id, entry_id=entry_id, entry__vocab_id=vocab_id).update(
            meaning=payload.meaning,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/vocab/{vocab_id}/entries/{entry_id}/definitions/{def_id}/")
def definition_delete(request, vocab_id: int, entry_id: int, def_id: int):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import WordDefinition
    WordDefinition.objects.filter(id=def_id, entry_id=entry_id, entry__vocab_id=vocab_id).delete()
    return {"success": True}


# ── Vocab Sets ──

@router.get("/vocab/sets/", response=list[VocabSetOut])
@paginate(PageNumberPagination, page_size=50)
def vocab_set_list(request, search: str = ""):
    if not staff_required(request):
        return []
    from vocab.models import VocabularySet
    qs = VocabularySet.objects.select_related('collection').annotate(word_count=Count('items'))
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(collection__title__icontains=search))
    return [
        {
            'id': vs.id, 'title': vs.title,
            'collection': vs.collection.name if vs.collection else None,
            'status': vs.status, 'is_public': vs.is_public,
            'toeic_level': vs.toeic_level, 'set_number': vs.set_number,
            'word_count': vs.word_count,
        }
        for vs in qs.order_by('-id')
    ]


@router.get("/vocab/sets/{set_id}/", response=VocabSetDetailOut)
def vocab_set_detail(request, set_id: int):
    if not staff_required(request):
        return {"id": 0, "title": "", "items": []}
    from vocab.models import VocabularySet
    vs = VocabularySet.objects.select_related('collection').annotate(word_count=Count('items')).get(id=set_id)
    items = []
    for si in vs.items.select_related('definition', 'definition__entry', 'definition__entry__vocab').all().order_by('display_order'):
        d = si.definition
        items.append({
            "id": si.id, "order": si.display_order,
            "word": d.entry.vocab.word if d and d.entry else "",
            "definition": d.meaning if d else "",
            "part_of_speech": d.entry.part_of_speech if d and d.entry else "",
            "has_quiz": si.quiz_questions.exists(),
        })
    return {
        "id": vs.id, "title": vs.title, "collection": vs.collection.name if vs.collection else None,
        "status": vs.status, "is_public": vs.is_public, "toeic_level": vs.toeic_level,
        "set_number": vs.set_number, "description": vs.description,
        "word_count": len(items), "items": items,
    }


class VocabSetUpdateIn(Schema):
    title: str
    description: str = ""
    status: str = "published"
    is_public: bool = True

@router.put("/vocab/sets/{set_id}/")
def vocab_set_update(request, set_id: int, payload: VocabSetUpdateIn):
    """Update a vocabulary set (rename, change status, etc.)."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import VocabularySet
    try:
        VocabularySet.objects.filter(id=set_id).update(
            title=payload.title, description=payload.description,
            status=payload.status, is_public=payload.is_public,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/vocab/sets/{set_id}/")
def vocab_set_delete(request, set_id: int):
    """Delete a vocabulary set."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import VocabularySet
    VocabularySet.objects.filter(id=set_id).delete()
    return {"success": True}


# ── Vocab detail & delete (MUST be after all static /vocab/... routes) ──

@router.get("/vocab/{vocab_id}/", response=VocabDetailOut)
def vocab_detail(request, vocab_id: int):
    if not staff_required(request):
        return {"id": 0, "word": "", "language": "", "entries": []}
    from vocab.models import Vocabulary
    v = Vocabulary.objects.get(id=vocab_id)
    entries = []
    for entry in v.entries.all().prefetch_related('definitions__examples'):
        defs = []
        for d in entry.definitions.all():
            exs = [{"id": e.id, "sentence": e.sentence, "translation": e.translation, "source": e.source} for e in d.examples.all()]
            defs.append({"id": d.id, "meaning": d.meaning, "extra_data": d.extra_data, "examples": exs})
        entries.append({
            "id": entry.id, "part_of_speech": entry.part_of_speech,
            "ipa": entry.ipa, "audio_us": entry.audio_us, "audio_uk": entry.audio_uk,
            "definitions": defs,
        })
    return {"id": v.id, "word": v.word, "language": v.language, "extra_data": v.extra_data, "entries": entries}


@router.delete("/vocab/{vocab_id}/")
def vocab_delete(request, vocab_id: int):
    if not staff_required(request):
        return {"success": False}
    from vocab.models import Vocabulary
    Vocabulary.objects.filter(id=vocab_id).delete()
    return {"success": True}



# ═══════════════════════════════════════════════════════════
# ── EXAM ──
# ═══════════════════════════════════════════════════════════

class ExamTemplateOut(Schema):
    id: int
    title: str
    book_title: Optional[str] = None
    level: str = ""
    category: str = ""
    group_type: str = ""
    lesson_index: int = 0
    question_count: int = 0
    main_question_type: Optional[str] = None
    is_full_toeic: bool = False

class ExamBookOut(Schema):
    id: int
    title: str
    level: str = ""
    category: str = ""
    total_lessons: int = 0
    is_active: bool = True
    description: Optional[str] = None
    cover_image: Optional[str] = None

class ExamQuestionOut(Schema):
    id: int
    template_title: Optional[str] = None
    order: int = 0
    question_type: str = ""
    toeic_part: Optional[str] = None
    text: str = ""
    mondai: Optional[str] = None
    source: Optional[str] = None


@router.get("/exam/templates/", response=list[ExamTemplateOut])
@paginate(PageNumberPagination, page_size=50)
def exam_template_list(request, search: str = "", category: str = "all"):
    if not staff_required(request):
        return []
    from exam.models import ExamTemplate
    qs = ExamTemplate.objects.annotate(question_count=Count('questions'))
    if search:
        qs = qs.filter(Q(title__icontains=search))
    if category and category != "all":
        cat_upper = category.upper()
        if cat_upper == "TOEIC":
            qs = qs.filter(category__in=["LISTENING", "READING", "TOEIC_FULL"])
        elif cat_upper == "JLPT":
            qs = qs.filter(category__in=["MOJI", "BUN", "MIX"])
        else:
            qs = qs.filter(category__iexact=category)
    return [
        {
            "id": t.id, "title": t.title,
            "book_title": t.book.title if t.book else None,
            "level": t.level, "category": t.category,
            "group_type": t.group_type, "lesson_index": t.lesson_index,
            "question_count": t.question_count,
            "main_question_type": t.main_question_type,
            "is_full_toeic": t.is_full_toeic,
        }
        for t in qs.select_related('book').order_by('-id')
    ]


@router.get("/exam/books/", response=list[ExamBookOut])
@paginate(PageNumberPagination, page_size=50)
def exam_book_list(request):
    if not staff_required(request):
        return []
    from exam.models import ExamBook
    qs = ExamBook.objects.all().order_by('-id')
    return [
        {
            "id": b.id, "title": b.title, "level": b.level,
            "category": b.category, "total_lessons": b.total_lessons,
            "is_active": b.is_active, "description": b.description,
            "cover_image": b.cover_image.url if b.cover_image else None,
        }
        for b in qs
    ]


class ExamBookIn(Schema):
    title: str
    level: str = "N5"
    category: str = "MOJI"
    description: str = ""
    total_lessons: int = 0
    is_active: bool = True

@router.post("/exam/books/")
def exam_book_create(request, payload: ExamBookIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from exam.models import ExamBook
        b = ExamBook.objects.create(
            title=payload.title, level=payload.level, category=payload.category,
            description=payload.description, total_lessons=payload.total_lessons,
            is_active=payload.is_active,
        )
        return {"success": True, "id": b.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/exam/books/{book_id}/")
def exam_book_update(request, book_id: int, payload: ExamBookIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from exam.models import ExamBook
        ExamBook.objects.filter(id=book_id).update(
            title=payload.title, level=payload.level, category=payload.category,
            description=payload.description, total_lessons=payload.total_lessons,
            is_active=payload.is_active,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/exam/books/{book_id}/")
def exam_book_delete(request, book_id: int):
    if not staff_required(request):
        return {"success": False}
    from exam.models import ExamBook
    ExamBook.objects.filter(id=book_id).delete()
    return {"success": True}


# ── Choukai tool endpoints ──

@router.get("/choukai/load-questions/")
def choukai_load_questions(request, book_id: int = 0):
    """Load all questions for a choukai book, grouped by mondai."""
    if not staff_required(request):
        return {"questions": [], "mondai_groups": []}
    from exam.models import ExamQuestion, ExamTemplate

    # Get all templates for this book
    template_ids = list(
        ExamTemplate.objects.filter(book_id=book_id).values_list("id", flat=True)
    )
    if not template_ids:
        return {"questions": [], "mondai_groups": [], "total": 0}

    qs = (
        ExamQuestion.objects
        .filter(template_id__in=template_ids)
        .select_related("template")
        .order_by("mondai", "order_in_mondai", "order")
    )

    # Build mondai groups
    mondai_map = {}
    questions = []
    for q in qs:
        mondai_key = q.mondai or "0"
        if mondai_key not in mondai_map:
            mondai_map[mondai_key] = {"mondai": mondai_key, "count": 0}
        mondai_map[mondai_key]["count"] += 1

        choices = q.data.get("choices", []) if q.data else []

        # Avoid double MEDIA_URL prefix – if the stored name is already a
        # full URL we must use it directly; .url would prepend MEDIA_URL again.
        img_url = None
        if q.image:
            img_url = q.image.name if q.image.name.startswith("http") else q.image.url
        audio_url = None
        if q.audio:
            audio_url = q.audio.name if q.audio.name.startswith("http") else q.audio.url

        questions.append({
            "id": q.id,
            "mondai": mondai_key,
            "order": q.order,
            "order_in_mondai": q.order_in_mondai,
            "text": q.text,
            "text_vi": q.text_vi,
            "correct_answer": q.correct_answer,
            "choices": choices,
            "image_url": img_url,
            "audio_url": audio_url,
            "transcript_data": q.transcript_data or {},
            "explanation_vi": q.explanation_vi,
        })

    mondai_groups = sorted(mondai_map.values(), key=lambda x: x["mondai"])

    return {
        "questions": questions,
        "mondai_groups": mondai_groups,
        "total": len(questions),
    }

@router.post("/choukai/create-book/")
def choukai_create_book(request, payload: ExamBookIn):
    """Create a new choukai book."""
    if not staff_required(request):
        return {"success": False}
    try:
        from exam.models import ExamBook
        b = ExamBook.objects.create(
            title=payload.title, level=payload.level or "N2",
            category="CHOUKAI",
            description=payload.description,
            total_lessons=payload.total_lessons,
            is_active=True,
        )
        return {"success": True, "id": b.id}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/exam/questions/", response=list[ExamQuestionOut])
@paginate(PageNumberPagination, page_size=50)
def exam_question_list(request, search: str = "", template_id: int = 0):
    if not staff_required(request):
        return []
    from exam.models import ExamQuestion
    qs = ExamQuestion.objects.select_related('template').all()
    if template_id:
        qs = qs.filter(template_id=template_id)
    if search:
        qs = qs.filter(Q(text__icontains=search) | Q(template__title__icontains=search))
    return [
        {
            "id": q.id,
            "template_title": q.template.title if q.template else None,
            "order": q.order, "question_type": q.question_type,
            "toeic_part": q.toeic_part, "text": q.text[:200],
            "mondai": q.mondai, "source": q.source,
        }
        for q in qs.order_by('-id')[:200]
    ]


# ═══════════════════════════════════════════════════════════
# ── USERS ──
# ═══════════════════════════════════════════════════════════

class UserOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_joined: dt
    is_active: bool
    is_staff: bool

@router.get("/users/", response=list[UserOut])
@paginate(PageNumberPagination, page_size=50)
def user_list(request, search: str = ""):
    if not staff_required(request):
        return []
    qs = User.objects.all()
    if search:
        qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search))
    return qs.order_by('-date_joined').values(
        'id', 'username', 'email', 'first_name', 'last_name',
        'date_joined', 'is_active', 'is_staff'
    )


class UserUpdateIn(Schema):
    is_active: bool = True
    is_staff: bool = False

@router.put("/users/{user_id}/")
def user_update(request, user_id: int, payload: UserUpdateIn):
    if not staff_required(request):
        return {"success": False}
    try:
        User.objects.filter(id=user_id).update(is_active=payload.is_active, is_staff=payload.is_staff)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ═══════════════════════════════════════════════════════════
# ── KANJI ──
# ═══════════════════════════════════════════════════════════

class KanjiLessonOut(Schema):
    id: int
    title: str       # mapped from topic
    level: str = ""  # mapped from jlpt_level
    lesson_number: int = 0
    order: int = 0
    kanji_count: int = 0

class KanjiOut(Schema):
    id: int
    char: str
    sino_vi: str = ""
    keyword: str = ""
    onyomi: str = ""
    kunyomi: str = ""
    meaning_vi: str = ""
    strokes: Optional[int] = None
    note: str = ""
    lesson_id: Optional[int] = None
    lesson_title: str = ""
    order: int = 0

@router.get("/kanji/lessons/", response=list[KanjiLessonOut])
@paginate(PageNumberPagination, page_size=50)
def kanji_lesson_list(request):
    if not staff_required(request):
        return []
    try:
        from kanji.models import KanjiLesson
        from django.db.models import F
        qs = KanjiLesson.objects.annotate(
            kanji_count=Count('kanjis'),
            title=F('topic'),
            level=F('jlpt_level'),
        )
        return qs.order_by('jlpt_level', 'order', 'lesson_number').values(
            'id', 'title', 'level', 'lesson_number', 'order', 'kanji_count'
        )
    except Exception:
        return []


class KanjiLessonCreateIn(Schema):
    topic: str
    jlpt_level: str = "N5"
    lesson_number: int = 1
    order: int = 0

@router.post("/kanji/lessons/")
def kanji_lesson_create(request, payload: KanjiLessonCreateIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from kanji.models import KanjiLesson
        lesson = KanjiLesson.objects.create(
            topic=payload.topic, jlpt_level=payload.jlpt_level,
            lesson_number=payload.lesson_number, order=payload.order,
        )
        return {"success": True, "id": lesson.id, "title": lesson.topic}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.put("/kanji/lessons/{lesson_id}/")
def kanji_lesson_update(request, lesson_id: int, payload: KanjiLessonCreateIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from kanji.models import KanjiLesson
        KanjiLesson.objects.filter(id=lesson_id).update(
            topic=payload.topic, jlpt_level=payload.jlpt_level,
            lesson_number=payload.lesson_number, order=payload.order,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.delete("/kanji/lessons/{lesson_id}/")
def kanji_lesson_delete(request, lesson_id: int):
    if not staff_required(request):
        return {"success": False}
    from kanji.models import KanjiLesson
    KanjiLesson.objects.filter(id=lesson_id).delete()
    return {"success": True}


# ── Individual Kanji ──

@router.get("/kanji/list/", response=list[KanjiOut])
@paginate(PageNumberPagination, page_size=50)
def kanji_list(request, search: str = "", lesson_id: int = 0, level: str = ""):
    if not staff_required(request):
        return []
    try:
        from kanji.models import Kanji
        qs = Kanji.objects.select_related('lesson').all()
        if search:
            qs = qs.filter(
                Q(char__icontains=search) | Q(sino_vi__icontains=search) |
                Q(keyword__icontains=search) | Q(meaning_vi__icontains=search) |
                Q(onyomi__icontains=search) | Q(kunyomi__icontains=search)
            )
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        if level:
            qs = qs.filter(lesson__jlpt_level=level)
        return [
            {
                "id": k.id, "char": k.char, "sino_vi": k.sino_vi,
                "keyword": k.keyword, "onyomi": k.onyomi, "kunyomi": k.kunyomi,
                "meaning_vi": k.meaning_vi, "strokes": k.strokes,
                "note": k.note, "lesson_id": k.lesson_id,
                "lesson_title": str(k.lesson) if k.lesson else "",
                "order": k.order,
            }
            for k in qs.order_by('lesson__jlpt_level', 'lesson__order', 'order')
        ]
    except Exception:
        return []


class KanjiCreateIn(Schema):
    char: str
    sino_vi: str = ""
    keyword: str = ""
    onyomi: str = ""
    kunyomi: str = ""
    meaning_vi: str = ""
    strokes: Optional[int] = None
    note: str = ""
    lesson_id: Optional[int] = None
    order: int = 0

@router.post("/kanji/create/")
def kanji_create(request, payload: KanjiCreateIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from kanji.models import Kanji
        k = Kanji.objects.create(
            char=payload.char, sino_vi=payload.sino_vi, keyword=payload.keyword,
            onyomi=payload.onyomi, kunyomi=payload.kunyomi, meaning_vi=payload.meaning_vi,
            strokes=payload.strokes, note=payload.note,
            lesson_id=payload.lesson_id, order=payload.order,
        )
        return {"success": True, "id": k.id}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.put("/kanji/{kanji_id}/")
def kanji_update(request, kanji_id: int, payload: KanjiCreateIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from kanji.models import Kanji
        Kanji.objects.filter(id=kanji_id).update(
            char=payload.char, sino_vi=payload.sino_vi, keyword=payload.keyword,
            onyomi=payload.onyomi, kunyomi=payload.kunyomi, meaning_vi=payload.meaning_vi,
            strokes=payload.strokes, note=payload.note,
            lesson_id=payload.lesson_id, order=payload.order,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.delete("/kanji/{kanji_id}/")
def kanji_delete(request, kanji_id: int):
    if not staff_required(request):
        return {"success": False}
    from kanji.models import Kanji
    Kanji.objects.filter(id=kanji_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── GRAMMAR ──
# ═══════════════════════════════════════════════════════════

class GrammarBookOut(Schema):
    id: int
    title: str
    level: str = ""
    point_count: int = 0

@router.get("/grammar/books/", response=list[GrammarBookOut])
@paginate(PageNumberPagination, page_size=50)
def grammar_book_list(request):
    if not staff_required(request):
        return []
    try:
        from grammar.models import GrammarBook
        qs = GrammarBook.objects.annotate(point_count=Count('sections__points'))
        return qs.order_by('-id').values('id', 'title', 'level', 'point_count')
    except Exception:
        return []


class GrammarBookIn(Schema):
    title: str
    level: str = "N5"

@router.post("/grammar/books/")
def grammar_book_create(request, payload: GrammarBookIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from grammar.models import GrammarBook
        b = GrammarBook.objects.create(title=payload.title, level=payload.level)
        return {"success": True, "id": b.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/grammar/books/{book_id}/")
def grammar_book_update(request, book_id: int, payload: GrammarBookIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from grammar.models import GrammarBook
        GrammarBook.objects.filter(id=book_id).update(title=payload.title, level=payload.level)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/grammar/books/{book_id}/")
def grammar_book_delete(request, book_id: int):
    if not staff_required(request):
        return {"success": False}
    from grammar.models import GrammarBook
    GrammarBook.objects.filter(id=book_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── COURSES ──
# ═══════════════════════════════════════════════════════════

class CourseOut(Schema):
    id: int
    title: str
    slug: str
    order: int = 0
    is_active: bool = True
    section_count: int = 0

@router.get("/courses/", response=list[CourseOut])
@paginate(PageNumberPagination, page_size=50)
def course_list(request):
    if not staff_required(request):
        return []
    from core.models import Course
    qs = Course.objects.annotate(section_count=Count('sections'))
    return qs.order_by('order').values('id', 'title', 'slug', 'order', 'is_active', 'section_count')


class CourseIn(Schema):
    title: str
    order: int = 0
    is_active: bool = True

@router.post("/courses/")
def course_create(request, payload: CourseIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from core.models import Course
        c = Course.objects.create(title=payload.title, order=payload.order, is_active=payload.is_active)
        return {"success": True, "id": c.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/courses/{course_id}/")
def course_update(request, course_id: int, payload: CourseIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from core.models import Course
        Course.objects.filter(id=course_id).update(title=payload.title, order=payload.order, is_active=payload.is_active)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/courses/{course_id}/")
def course_delete(request, course_id: int):
    if not staff_required(request):
        return {"success": False}
    from core.models import Course
    Course.objects.filter(id=course_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── PAYMENT ──
# ═══════════════════════════════════════════════════════════

class PlanOut(Schema):
    id: int
    name: str
    price: float
    duration_days: int
    is_active: bool
    is_popular: bool = False

class PaymentOut(Schema):
    id: int
    user: str
    plan: str
    amount: float
    status: str
    created_at: str

@router.get("/payment/plans/", response=list[PlanOut])
@paginate(PageNumberPagination, page_size=50)
def payment_plan_list(request):
    if not staff_required(request):
        return []
    try:
        from payment.models import PaymentPlan
        return list(PaymentPlan.objects.order_by('-id').values(
            'id', 'name', 'price', 'duration_days', 'is_active', 'is_popular'
        ))
    except Exception:
        return []


class PlanIn(Schema):
    name: str
    price: float = 0
    duration_days: int = 30
    is_active: bool = True
    is_popular: bool = False

@router.post("/payment/plans/")
def payment_plan_create(request, payload: PlanIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from payment.models import PaymentPlan
        from django.utils.text import slugify
        slug = slugify(payload.name) or "plan"
        p = PaymentPlan.objects.create(
            name=payload.name, slug=slug, price=payload.price,
            duration_days=payload.duration_days, is_active=payload.is_active,
            is_popular=payload.is_popular,
        )
        return {"success": True, "id": p.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/payment/plans/{plan_id}/")
def payment_plan_update(request, plan_id: int, payload: PlanIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from payment.models import PaymentPlan
        PaymentPlan.objects.filter(id=plan_id).update(
            name=payload.name, price=payload.price,
            duration_days=payload.duration_days, is_active=payload.is_active,
            is_popular=payload.is_popular,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/payment/plans/{plan_id}/")
def payment_plan_delete(request, plan_id: int):
    if not staff_required(request):
        return {"success": False}
    from payment.models import PaymentPlan
    PaymentPlan.objects.filter(id=plan_id).delete()
    return {"success": True}


@router.get("/payment/payments/", response=list[PaymentOut])
@paginate(PageNumberPagination, page_size=50)
def payment_list(request):
    if not staff_required(request):
        return []
    try:
        from payment.models import Payment
        return [
            {
                "id": p.id, "user": p.user.username,
                "plan": p.plan.name if p.plan else "—",
                "amount": float(p.amount), "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in Payment.objects.select_related('user', 'plan').order_by('-created_at')[:100]
        ]
    except Exception:
        return []


class PaymentStatusIn(Schema):
    status: str

@router.put("/payment/payments/{payment_id}/status/")
def payment_update_status(request, payment_id: str, payload: PaymentStatusIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from payment.models import Payment
        Payment.objects.filter(id=payment_id).update(status=payload.status)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ═══════════════════════════════════════════════════════════
# ── WALLET ──
# ═══════════════════════════════════════════════════════════

class WalletOut(Schema):
    id: int
    username: str
    coins: int

class TransactionOut(Schema):
    id: int
    username: str
    amount: int
    balance_after: int
    transaction_type: str
    description: str
    created_at: str

@router.get("/wallet/wallets/", response=list[WalletOut])
@paginate(PageNumberPagination, page_size=50)
def wallet_list(request):
    if not staff_required(request):
        return []
    try:
        from wallet.models import UserWallet
        return [
            {"id": w.id, "username": w.user.username, "coins": w.coins}
            for w in UserWallet.objects.select_related('user').order_by('-coins')[:100]
        ]
    except Exception:
        return []


class WalletUpdateIn(Schema):
    coins: int

@router.put("/wallet/wallets/{wallet_id}/")
def wallet_update(request, wallet_id: int, payload: WalletUpdateIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from wallet.models import UserWallet
        UserWallet.objects.filter(id=wallet_id).update(coins=payload.coins)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/wallet/transactions/", response=list[TransactionOut])
@paginate(PageNumberPagination, page_size=50)
def wallet_transaction_list(request):
    if not staff_required(request):
        return []
    try:
        from wallet.models import CoinTransaction
        return [
            {
                "id": t.id, "username": t.user.username,
                "amount": t.amount, "balance_after": t.balance_after,
                "transaction_type": t.transaction_type,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in CoinTransaction.objects.select_related('user').order_by('-created_at')[:100]
        ]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════
# ── FEEDBACK ──
# ═══════════════════════════════════════════════════════════

class FeedbackOut(Schema):
    id: int
    title: str
    type: str = ""
    status: str = ""
    user: str = ""
    total_votes: int = 0
    created_at: str = ""

@router.get("/feedback/", response=list[FeedbackOut])
@paginate(PageNumberPagination, page_size=50)
def feedback_list(request, status: str = "all"):
    if not staff_required(request):
        return []
    try:
        from feedback.models import FeedbackItem
        qs = FeedbackItem.objects.select_related('user').all()
        if status and status != "all":
            qs = qs.filter(status=status)
        return [
            {
                "id": f.id, "title": f.title, "type": f.type,
                "status": f.status, "user": f.user.username if f.user else "",
                "total_votes": f.total_votes,
                "created_at": f.created_at.isoformat() if f.created_at else "",
            }
            for f in qs.order_by('-created_at')[:100]
        ]
    except Exception:
        return []


class FeedbackStatusIn(Schema):
    status: str

@router.put("/feedback/{feedback_id}/")
def feedback_update_status(request, feedback_id: int, payload: FeedbackStatusIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from feedback.models import FeedbackItem
        FeedbackItem.objects.filter(id=feedback_id).update(status=payload.status)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/feedback/{feedback_id}/")
def feedback_delete(request, feedback_id: int):
    if not staff_required(request):
        return {"success": False}
    from feedback.models import FeedbackItem
    FeedbackItem.objects.filter(id=feedback_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── SHOP ──
# ═══════════════════════════════════════════════════════════

class FrameOut(Schema):
    id: int
    name: str
    rarity: str = ""
    price: int = 0
    is_active: bool = True
    display_order: int = 0

@router.get("/shop/frames/", response=list[FrameOut])
@paginate(PageNumberPagination, page_size=50)
def shop_frame_list(request):
    if not staff_required(request):
        return []
    try:
        from shop.models import AvatarFrame
        return list(AvatarFrame.objects.order_by('display_order').values(
            'id', 'name', 'rarity', 'price', 'is_active', 'display_order'
        ))
    except Exception:
        return []


class FrameIn(Schema):
    name: str
    rarity: str = "COMMON"
    price: int = 100
    is_active: bool = True
    display_order: int = 0

@router.post("/shop/frames/")
def shop_frame_create(request, payload: FrameIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from shop.models import AvatarFrame
        from django.utils.text import slugify
        slug = slugify(payload.name) or "frame"
        f = AvatarFrame.objects.create(
            name=payload.name, slug=slug, rarity=payload.rarity,
            price=payload.price, is_active=payload.is_active,
            display_order=payload.display_order,
        )
        return {"success": True, "id": f.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/shop/frames/{frame_id}/")
def shop_frame_update(request, frame_id: int, payload: FrameIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from shop.models import AvatarFrame
        AvatarFrame.objects.filter(id=frame_id).update(
            name=payload.name, rarity=payload.rarity,
            price=payload.price, is_active=payload.is_active,
            display_order=payload.display_order,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/shop/frames/{frame_id}/")
def shop_frame_delete(request, frame_id: int):
    if not staff_required(request):
        return {"success": False}
    from shop.models import AvatarFrame
    AvatarFrame.objects.filter(id=frame_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── VIDEOS ──
# ═══════════════════════════════════════════════════════════

class VideoOut(Schema):
    id: int
    title: str
    level: str = ""
    category: str = ""
    created_at: str = ""
    transcript_count: int = 0

@router.get("/videos/", response=list[VideoOut])
@paginate(PageNumberPagination, page_size=50)
def video_list(request):
    if not staff_required(request):
        return []
    try:
        from video.models import Video
        qs = Video.objects.annotate(transcript_count=Count('transcript_lines'))
        return [
            {
                "id": v.id, "title": v.title, "level": v.level,
                "category": v.category.name if v.category else "",
                "created_at": v.created_at.isoformat() if v.created_at else "",
                "transcript_count": v.transcript_count,
            }
            for v in qs.select_related('category').order_by('-id')
        ]
    except Exception:
        return []


class VideoIn(Schema):
    title: str
    level: str = "N5"
    youtube_id: str = ""
    description: str = ""

@router.post("/videos/")
def video_create(request, payload: VideoIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from video.models import Video
        v = Video.objects.create(
            title=payload.title, level=payload.level,
            youtube_id=payload.youtube_id, description=payload.description,
        )
        return {"success": True, "id": v.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/videos/{video_id}/")
def video_update(request, video_id: int, payload: VideoIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from video.models import Video
        Video.objects.filter(id=video_id).update(
            title=payload.title, level=payload.level,
            youtube_id=payload.youtube_id, description=payload.description,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/videos/{video_id}/")
def video_delete(request, video_id: int):
    if not staff_required(request):
        return {"success": False}
    from video.models import Video
    Video.objects.filter(id=video_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── PLACEMENT ──
# ═══════════════════════════════════════════════════════════

class PlacementQuestionOut(Schema):
    id: int
    skill: str = ""
    difficulty: str = ""
    question_preview: str = ""
    correct_answer: str = ""
    is_active: bool = True

@router.get("/placement/questions/", response=list[PlacementQuestionOut])
@paginate(PageNumberPagination, page_size=50)
def placement_question_list(request):
    if not staff_required(request):
        return []
    try:
        from placement.models import PlacementQuestion
        return [
            {
                "id": q.id, "skill": q.skill, "difficulty": q.difficulty,
                "question_preview": q.question_text[:100] if q.question_text else "",
                "correct_answer": q.correct_answer or "",
                "is_active": q.is_active,
            }
            for q in PlacementQuestion.objects.order_by('-id')
        ]
    except Exception:
        return []


class PlacementQuestionIn(Schema):
    skill: str = "VOC"
    difficulty: int = 1
    question_text: str = ""
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    correct_answer: str = "A"
    is_active: bool = True

@router.post("/placement/questions/")
def placement_question_create(request, payload: PlacementQuestionIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from placement.models import PlacementQuestion
        q = PlacementQuestion.objects.create(
            skill=payload.skill, difficulty=payload.difficulty,
            question_text=payload.question_text,
            option_a=payload.option_a, option_b=payload.option_b,
            option_c=payload.option_c, option_d=payload.option_d,
            correct_answer=payload.correct_answer, is_active=payload.is_active,
        )
        return {"success": True, "id": q.id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/placement/questions/{question_id}/")
def placement_question_update(request, question_id: int, payload: PlacementQuestionIn):
    if not staff_required(request):
        return {"success": False}
    try:
        from placement.models import PlacementQuestion
        PlacementQuestion.objects.filter(id=question_id).update(
            skill=payload.skill, difficulty=payload.difficulty,
            question_text=payload.question_text,
            option_a=payload.option_a, option_b=payload.option_b,
            option_c=payload.option_c, option_d=payload.option_d,
            correct_answer=payload.correct_answer, is_active=payload.is_active,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/placement/questions/{question_id}/")
def placement_question_delete(request, question_id: int):
    if not staff_required(request):
        return {"success": False}
    from placement.models import PlacementQuestion
    PlacementQuestion.objects.filter(id=question_id).delete()
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ── ANALYTICS ──
# ═══════════════════════════════════════════════════════════

class StreakOut(Schema):
    id: int
    username: str
    current_streak: int
    longest_streak: int
    total_days: int

@router.get("/streak/stats/", response=list[StreakOut])
@paginate(PageNumberPagination, page_size=50)
def streak_list(request):
    if not staff_required(request):
        return []
    try:
        from streak.models import StreakData
        return [
            {
                "id": s.id, "username": s.user.username,
                "current_streak": s.current_streak,
                "longest_streak": s.longest_streak,
                "total_days": s.total_days,
            }
            for s in StreakData.objects.select_related('user').order_by('-current_streak')[:100]
        ]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════
# ── VOCAB TOOLS (Phase 1-3) ──
# ═══════════════════════════════════════════════════════════

class BulkProcessIn(Schema):
    word: str
    limit: int = 0
    set_id: Optional[int] = None

@router.post("/vocab/bulk-process/")
def vocab_bulk_process(request, payload: BulkProcessIn):
    """Process a single word: Scrape Cambridge → Save → Return result."""
    if not staff_required(request):
        return {"status": "error", "message": "Unauthorized"}
    from vocab.models import Vocabulary, WordEntry, WordDefinition, ExampleSentence, VocabularySet, SetItem
    from vocab.utils_scraper import scrape_cambridge
    from django.db import transaction

    word = payload.word.strip().lower()
    if not word:
        return {"status": "error", "message": "No word provided"}

    try:
        vocab = Vocabulary.objects.filter(word=word).first()
        reuse_existing = False
        scraped_entries = []
        created_entries = 0

        if vocab and WordDefinition.objects.filter(entry__vocab=vocab).exists():
            reuse_existing = True
        else:
            scraped_entries = scrape_cambridge(word)
            if not scraped_entries:
                return {"status": "error", "message": f"Not found dictionary data for '{word}'", "word": word}
            if payload.limit > 0:
                scraped_entries = scraped_entries[:payload.limit]

        with transaction.atomic():
            if not reuse_existing:
                vocab, _ = Vocabulary.objects.get_or_create(
                    word=word, defaults={"language": Vocabulary.Language.ENGLISH}
                )
                for item in scraped_entries:
                    pos = item.get("type") or "unknown"
                    entry, _ = WordEntry.objects.get_or_create(
                        vocab=vocab, part_of_speech=pos,
                        defaults={"ipa": item.get("ipa", ""), "audio_us": item.get("audio_us") or "", "audio_uk": item.get("audio_uk") or ""}
                    )
                    definition_text = item.get("definition", "")
                    if definition_text:
                        if not entry.definitions.filter(meaning=definition_text).exists():
                            defn = WordDefinition.objects.create(entry=entry, meaning=definition_text)
                            example_text = item.get("example", "")
                            if example_text:
                                ExampleSentence.objects.create(definition=defn, sentence=example_text, source="cambridge")
                            created_entries += 1

        # Optionally add to VocabularySet
        if payload.set_id:
            try:
                vocab_set = VocabularySet.objects.get(pk=payload.set_id)
                first_def = WordDefinition.objects.filter(entry__vocab=vocab).first()
                if first_def and not SetItem.objects.filter(vocabulary_set=vocab_set, definition=first_def).exists():
                    SetItem.objects.create(vocabulary_set=vocab_set, definition=first_def, display_order=vocab_set.items.count())
            except (VocabularySet.DoesNotExist, ValueError):
                pass

        return {
            "status": "success",
            "message": f"{'Reused' if reuse_existing else 'Added'} '{word}' with {created_entries} definitions.",
            "word": word, "definitions": created_entries, "reused": reuse_existing,
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "word": word}


@router.get("/vocab/scrape/")
def vocab_scrape(request, word: str = ""):
    """Scrape-only preview from Cambridge Dictionary."""
    if not staff_required(request):
        return {"results": []}
    from vocab.utils_scraper import scrape_cambridge
    word = word.strip()
    if not word:
        return {"error": "No word provided"}
    try:
        results = scrape_cambridge(word)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


class ManualAddIn(Schema):
    word: str
    meaning: str
    language: str = "en"
    pos: str = ""
    ipa: str = ""
    audio_us: str = ""
    audio_uk: str = ""
    example: str = ""
    example_trans: str = ""
    image_url: str = ""

@router.post("/vocab/manual-add/")
def vocab_manual_add(request, payload: ManualAddIn):
    """Manually add a single vocabulary word."""
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}
    from vocab.models import Vocabulary, WordEntry, WordDefinition, ExampleSentence
    from django.db import transaction

    if not payload.word or not payload.meaning:
        return {"success": False, "message": "Word and meaning required"}

    try:
        with transaction.atomic():
            vocab, _ = Vocabulary.objects.get_or_create(
                word=payload.word, defaults={"language": payload.language}
            )
            entry, _ = WordEntry.objects.get_or_create(
                vocab=vocab, part_of_speech=payload.pos,
                defaults={"ipa": payload.ipa, "audio_us": payload.audio_us, "audio_uk": payload.audio_uk}
            )
            defn = WordDefinition.objects.create(
                entry=entry, meaning=payload.meaning, image_url=payload.image_url or None
            )
            if payload.example:
                ExampleSentence.objects.create(
                    definition=defn, sentence=payload.example,
                    translation=payload.example_trans, source="user"
                )
        return {"success": True, "message": f"Added '{payload.word}'", "id": vocab.id}
    except Exception as e:
        return {"success": False, "message": str(e)}




# ── Set word management (Phase 3) ──

@router.get("/vocab/search-words/")
def vocab_search_words(request, q: str = ""):
    """Search existing words for adding to sets."""
    if not staff_required(request):
        return []
    from vocab.models import WordDefinition
    if len(q) < 2:
        return []
    return [
        {
            "def_id": d.id,
            "word": d.entry.vocab.word,
            "meaning": d.meaning,
            "pos": d.entry.part_of_speech,
        }
        for d in WordDefinition.objects.select_related("entry", "entry__vocab")
            .filter(Q(entry__vocab__word__icontains=q) | Q(meaning__icontains=q))
            .order_by("entry__vocab__word")[:30]
    ]


class AddWordsIn(Schema):
    definition_ids: list[int]

@router.post("/vocab/sets/{set_id}/add-words/")
def vocab_set_add_words(request, set_id: int, payload: AddWordsIn):
    """Add definitions to a vocabulary set."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import VocabularySet, SetItem
    try:
        vs = VocabularySet.objects.get(id=set_id)
        added = 0
        current_max = vs.items.count()
        for def_id in payload.definition_ids:
            if not SetItem.objects.filter(vocabulary_set=vs, definition_id=def_id).exists():
                SetItem.objects.create(vocabulary_set=vs, definition_id=def_id, display_order=current_max + added)
                added += 1
        return {"success": True, "added": added}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.delete("/vocab/sets/{set_id}/words/{item_id}/")
def vocab_set_remove_word(request, set_id: int, item_id: int):
    """Remove a word from a vocabulary set."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import SetItem
    SetItem.objects.filter(id=item_id, vocabulary_set_id=set_id).delete()
    return {"success": True}


class MoveWordsIn(Schema):
    item_ids: list[int]
    target_set_id: int

@router.post("/vocab/sets/{set_id}/move-words/")
def vocab_set_move_words(request, set_id: int, payload: MoveWordsIn):
    """Move words from one set to another."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import VocabularySet, SetItem
    try:
        target = VocabularySet.objects.get(id=payload.target_set_id)
        moved = 0
        current_max = target.items.count()
        for item_id in payload.item_ids:
            si = SetItem.objects.filter(id=item_id, vocabulary_set_id=set_id).first()
            if si:
                if not SetItem.objects.filter(vocabulary_set=target, definition=si.definition).exists():
                    si.vocabulary_set = target
                    si.display_order = current_max + moved
                    si.save()
                    moved += 1
                else:
                    si.delete()
                    moved += 1
        return {"success": True, "moved": moved}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ═══════════════════════════════════════════════════════════
# ── IMPORT JP (Phase 2) ──
# ═══════════════════════════════════════════════════════════

class ImportJPIn(Schema):
    json_data: str  # raw JSON string
    set_id: Optional[int] = None
    new_set_title: str = ""
    source: str = "other"
    default_pos: str = "noun"

@router.post("/vocab/import-jp/")
def vocab_import_jp(request, payload: ImportJPIn):
    """Import Japanese vocabulary from JSON data."""
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}
    from vocab.models import Vocabulary, WordEntry, WordDefinition, ExampleSentence, VocabularySet, SetItem
    from django.db import transaction

    try:
        data = json.loads(payload.json_data)
        if not isinstance(data, list):
            return {"success": False, "message": "JSON must be a list of objects."}
    except json.JSONDecodeError:
        return {"success": False, "message": "Invalid JSON format."}

    # Resolve or create VocabularySet
    vocab_set = None
    if payload.set_id:
        try:
            vocab_set = VocabularySet.objects.get(id=payload.set_id)
        except VocabularySet.DoesNotExist:
            return {"success": False, "message": f"Set {payload.set_id} not found"}
    elif payload.new_set_title:
        vocab_set = VocabularySet.objects.create(
            title=payload.new_set_title,
            language="ja", is_public=True, status="published",
        )

    stats = {"created_vocabs": 0, "existing_vocabs": 0, "created_definitions": 0, "created_examples": 0, "added_to_set": 0, "skipped": 0}

    try:
        with transaction.atomic():
            for item in data:
                word = item.get("word", "").strip()
                if not word:
                    stats["skipped"] += 1
                    continue

                vocab, created = Vocabulary.objects.get_or_create(
                    word=word,
                    defaults={"language": "ja", "extra_data": item.get("extra_data", {})}
                )
                if created:
                    stats["created_vocabs"] += 1
                else:
                    stats["existing_vocabs"] += 1

                meanings = item.get("meanings", [])
                if isinstance(meanings, list):
                    for m in meanings:
                        pos = m.get("pos", payload.default_pos)
                        entry, _ = WordEntry.objects.get_or_create(
                            vocab=vocab, part_of_speech=pos,
                            defaults={"ipa": m.get("ipa", item.get("ipa", "")), "audio_us": m.get("audio_us", ""), "audio_uk": m.get("audio_uk", "")}
                        )
                        defn = WordDefinition.objects.create(entry=entry, meaning=m.get("meaning", ""), image_url=m.get("image", ""))
                        stats["created_definitions"] += 1
                        example_text = m.get("example", "")
                        if example_text:
                            ExampleSentence.objects.create(
                                definition=defn, sentence=example_text,
                                translation=m.get("example_trans", ""), source=payload.source
                            )
                            stats["created_examples"] += 1

                        # Add to set
                        if vocab_set:
                            if not SetItem.objects.filter(vocabulary_set=vocab_set, definition=defn).exists():
                                SetItem.objects.create(vocabulary_set=vocab_set, definition=defn, display_order=vocab_set.items.count())
                                stats["added_to_set"] += 1

        return {"success": True, "stats": stats, "set_id": vocab_set.id if vocab_set else None}
    except Exception as e:
        return {"success": False, "message": str(e)}


class QuickCreateSetIn(Schema):
    title: str
    language: str = "ja"
    description: str = ""

@router.post("/vocab/quick-create-set/")
def vocab_quick_create_set(request, payload: QuickCreateSetIn):
    """Quickly create a new VocabularySet."""
    if not staff_required(request):
        return {"success": False}
    from vocab.models import VocabularySet
    if not payload.title:
        return {"success": False, "message": "Title required"}
    try:
        vs = VocabularySet.objects.create(
            title=payload.title, language=payload.language,
            description=payload.description, is_public=True, status="published",
        )
        return {"success": True, "id": vs.id, "title": vs.title}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ═══════════════════════════════════════════════════════════
# ── QUIZ GENERATION (Phase 4) ──
# ═══════════════════════════════════════════════════════════

class QuizGenerateIn(Schema):
    set_item_id: int
    model: str = "gemini-2.5-flash"
    mondai_type: Optional[str] = None

@router.post("/vocab/quiz/generate/")
def quiz_generate(request, payload: QuizGenerateIn):
    """Generate quiz distractors for a single SetItem using Gemini AI."""
    if not staff_required(request):
        return {"status": "error", "message": "Unauthorized"}
    try:
        from vocab.services.quiz_generator import generate_and_save_for_set_item
        result, error = generate_and_save_for_set_item(
            payload.set_item_id,
            model_name=payload.model,
            mondai_type=payload.mondai_type,
        )
        if error:
            return {"status": "error", "message": error}

        from vocab.models import SetItem
        item = SetItem.objects.select_related('definition__entry__vocab').get(pk=payload.set_item_id)
        return {
            "status": "success",
            "message": f"Generated quiz for '{item.definition.entry.vocab.word}'",
            "word": item.definition.entry.vocab.word,
            "questions": result,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/vocab/quiz/load-set/")
def quiz_load_set(request, set_id: int = 0):
    """Load words in a VocabularySet with quiz status info."""
    if not staff_required(request):
        return {"items": []}
    if not set_id:
        return {"items": []}
    try:
        from vocab.models import VocabularySet, SetItem
        vocab_set = VocabularySet.objects.get(pk=set_id)
        items = SetItem.objects.filter(
            vocabulary_set=vocab_set,
        ).select_related(
            'definition__entry__vocab'
        ).prefetch_related('quiz_questions').order_by('display_order', 'id')

        result = []
        for item in items:
            vocab = item.definition.entry.vocab
            ed = vocab.extra_data or {}
            existing_types = list(
                item.quiz_questions.values_list('question_type', flat=True)
            )
            result.append({
                "id": item.id,
                "word": vocab.word,
                "reading": ed.get("reading", ""),
                "definition": item.definition.meaning,
                "has_quiz": len(existing_types) > 0,
                "quiz_types": existing_types,
            })
        return {"items": result}
    except Exception as e:
        return {"items": [], "error": str(e)}


# ═══════════════════════════════════════════════════════════
# ── KANJI QUIZ GENERATION ──
# ═══════════════════════════════════════════════════════════

@router.get("/kanji/quiz/load-lesson/")
def kanji_quiz_load_lesson(request, lesson_id: int = 0, level: str = ""):
    """Load all kanji in a lesson with quiz status info."""
    if not staff_required(request):
        return {"items": []}
    if not lesson_id:
        return {"items": []}
    try:
        from kanji.models import KanjiLesson, Kanji
        lesson = KanjiLesson.objects.get(pk=lesson_id)
        kanjis = Kanji.objects.filter(
            lesson=lesson,
        ).prefetch_related('quiz_questions').order_by('order', 'id')

        result = []
        for k in kanjis:
            existing_types = list(
                k.quiz_questions.values_list('question_type', flat=True)
            )
            result.append({
                "id": k.id,
                "char": k.char,
                "sino_vi": k.sino_vi,
                "meaning_vi": k.meaning_vi,
                "onyomi": k.onyomi,
                "kunyomi": k.kunyomi,
                "has_quiz": len(existing_types) > 0,
                "quiz_types": existing_types,
            })
        return {"items": result}
    except Exception as e:
        return {"items": [], "error": str(e)}


class KanjiQuizGenerateIn(Schema):
    kanji_id: int
    model: str = "gemini-2.5-flash"

@router.post("/kanji/quiz/generate/")
def kanji_quiz_generate(request, payload: KanjiQuizGenerateIn):
    """Generate quiz distractors for a single Kanji using Gemini AI."""
    if not staff_required(request):
        return {"status": "error", "message": "Unauthorized"}
    try:
        from kanji.services.quiz_generator import generate_and_save_for_kanji
        result, error = generate_and_save_for_kanji(
            payload.kanji_id,
            model_name=payload.model,
        )
        if error:
            return {"status": "error", "message": error}

        from kanji.models import Kanji
        kanji = Kanji.objects.get(pk=payload.kanji_id)
        return {
            "status": "success",
            "message": f"Generated quiz for '{kanji.char}'",
            "char": kanji.char,
            "questions": result,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════
# ── EXAM: AI Import 用法 (Usage quiz) ──
# ═══════════════════════════════════════════════════════════

class ImportUsageAIIn(Schema):
    raw_text: str
    book_id: Optional[int] = None
    level: str = "N2"
    model: str = "gemini-2.5-flash"

@router.post("/exam/import-usage-ai/")
def import_usage_ai(request, payload: ImportUsageAIIn):
    """
    AI-powered import for 用法 (Usage) quizzes.
    1. Send raw exam text to Gemini API with prompt template
    2. Parse JSON response
    3. Create ExamTemplate + ExamQuestion records
    """
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}

    import os, re, logging
    logger = logging.getLogger(__name__)

    # ── 1. Build prompt ──
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", "extract_vocab_quiz.md"
    )
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return {"success": False, "message": "Prompt template not found"}

    full_prompt = prompt_template + "\n\n" + payload.raw_text

    # ── 2. Call Gemini ──
    from vocab.services.gemini_service import GeminiService
    raw_response = GeminiService.generate_text(full_prompt, model_name=payload.model)

    if not raw_response or raw_response.startswith("Error:"):
        return {"success": False, "message": f"Gemini API error: {raw_response}"}

    # ── 3. Parse JSON from response ──
    # Strip markdown code fences if present
    cleaned = raw_response.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "message": f"JSON parse error: {e}",
            "raw_response": raw_response[:2000],
        }

    questions_data = data.get("questions", [])
    if not questions_data:
        return {"success": False, "message": "No questions found in AI response", "raw_response": raw_response[:2000]}

    # ── 4. Create ExamTemplate ──
    from exam.models import ExamTemplate, ExamQuestion, ExamBook, QuestionType, ExamLevel, ExamCategory, ExamGroupType

    book = None
    if payload.book_id:
        try:
            book = ExamBook.objects.get(id=payload.book_id)
        except ExamBook.DoesNotExist:
            pass

    book_title = data.get("book_title", "AI Import")
    exam_type = data.get("exam_type", "用法")
    template_title = f"{book_title} - {exam_type} ({len(questions_data)} câu)"

    template = ExamTemplate.objects.create(
        book=book,
        title=template_title,
        level=payload.level,
        category=ExamCategory.MOJIGOI,
        group_type=ExamGroupType.BY_PATTERN,
        main_question_type=QuestionType.USAGE,
    )

    # ── 5. Create ExamQuestion records ──
    created_count = 0
    errors = []
    for i, q in enumerate(questions_data):
        try:
            word = q.get("word", "")
            reading = q.get("reading", "")
            han_viet = q.get("han_viet", "")
            meaning_vi = q.get("meaning_vi", "")
            correct = q.get("correct", 1)
            correct_translation = q.get("correct_translation", "")
            options = q.get("options", [])
            explanations = q.get("explanations", [])

            # Build choices data
            choices = []
            for j, opt_text in enumerate(options):
                choices.append({"key": str(j + 1), "text": opt_text})

            # Build explanation_json
            explanation_json = {
                "word": word,
                "reading": reading,
                "han_viet": han_viet,
                "meaning_vi": meaning_vi,
                "correct_translation": correct_translation,
                "explanations": explanations,
            }

            ExamQuestion.objects.create(
                template=template,
                order=i + 1,
                question_type=QuestionType.USAGE,
                text=word,
                text_vi=f"{reading} 【{han_viet}】 {meaning_vi}" if han_viet else f"{reading} - {meaning_vi}",
                data={"choices": choices},
                correct_answer=str(correct),
                explanation_json=explanation_json,
                mondai="01",
                order_in_mondai=i + 1,
            )
            created_count += 1
        except Exception as e:
            errors.append(f"Q{i+1}: {str(e)}")

    result = {
        "success": True,
        "message": f"Đã tạo {created_count}/{len(questions_data)} câu hỏi",
        "template_id": template.id,
        "template_slug": template.slug,
        "created": created_count,
        "total": len(questions_data),
        "ai_data": data,
    }
    if errors:
        result["errors"] = errors
    return result


# ═══════════════════════════════════════════════════════════
# ── EXAM: AI Import 文法 (Grammar quiz) ──
# ═══════════════════════════════════════════════════════════

class ImportGrammarAIIn(Schema):
    raw_text: str
    book_id: Optional[int] = None
    level: str = "N2"
    model: str = "gemini-2.5-flash"

@router.post("/exam/import-grammar-ai/")
def import_grammar_ai(request, payload: ImportGrammarAIIn):
    """
    AI-powered import for 文法 (Grammar) quizzes.
    1. Send raw HTML exam data to Gemini API with grammar prompt template
    2. Parse JSON response
    3. Create ExamTemplate + ExamQuestion records
    """
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}

    import os, re, logging
    logger = logging.getLogger(__name__)

    # ── 1. Build prompt ──
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", "extract_grammar_quiz.md"
    )
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return {"success": False, "message": "Grammar prompt template not found"}

    full_prompt = prompt_template + "\n\n" + payload.raw_text

    # ── 2. Call Gemini ──
    from vocab.services.gemini_service import GeminiService
    raw_response = GeminiService.generate_text(full_prompt, model_name=payload.model)

    if not raw_response or raw_response.startswith("Error:"):
        return {"success": False, "message": f"Gemini API error: {raw_response}"}

    # ── 3. Parse JSON from response ──
    cleaned = raw_response.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "message": f"JSON parse error: {e}",
            "raw_response": raw_response[:2000],
        }

    questions_data = data.get("questions", [])
    if not questions_data:
        return {"success": False, "message": "No questions found in AI response", "raw_response": raw_response[:2000]}

    # ── 4. Create ExamTemplate ──
    from exam.models import ExamTemplate, ExamQuestion, ExamBook, QuestionType, ExamLevel, ExamCategory, ExamGroupType

    book = None
    if payload.book_id:
        try:
            book = ExamBook.objects.get(id=payload.book_id)
        except ExamBook.DoesNotExist:
            pass

    book_title = data.get("book_title", "AI Import")
    exam_type = data.get("exam_type", "文法")
    template_title = f"{book_title} - {exam_type} ({len(questions_data)} câu)"

    template = ExamTemplate.objects.create(
        book=book,
        title=template_title,
        level=payload.level,
        category=ExamCategory.BUNPOU,
        group_type=ExamGroupType.BY_PATTERN,
        main_question_type=QuestionType.FILL_BLANK,
    )

    # ── 5. Create ExamQuestion records ──
    created_count = 0
    errors = []
    for i, q in enumerate(questions_data):
        try:
            sentence = q.get("sentence", "")
            sentence_completed = q.get("sentence_completed", "")
            sentence_vi = q.get("sentence_vi", "")
            correct = q.get("correct", 1)
            options = q.get("options", [])
            explanations = q.get("explanations", [])

            # Build choices data
            choices = []
            for j, opt_text in enumerate(options):
                choices.append({"key": str(j + 1), "text": opt_text})

            # Build explanation_json with grammar info
            explanation_json = {
                "grammar_point": q.get("grammar_point", ""),
                "grammar_reading": q.get("grammar_reading", ""),
                "grammar_meaning": q.get("grammar_meaning", ""),
                "grammar_structure": q.get("grammar_structure", ""),
                "grammar_note": q.get("grammar_note", ""),
                "grammar_furigana": q.get("grammar_furigana", ""),
                "grammar_topic": q.get("grammar_topic", ""),
                "sentence_completed": sentence_completed,
                "correct_translation": sentence_vi,
                "explanations": explanations,
                "examples": q.get("examples", []),
            }

            ExamQuestion.objects.create(
                template=template,
                order=i + 1,
                question_type=QuestionType.FILL_BLANK,
                text=sentence,
                text_vi=sentence_vi,
                data={"choices": choices},
                correct_answer=str(correct),
                explanation_json=explanation_json,
                mondai="01",
                order_in_mondai=i + 1,
            )
            created_count += 1
        except Exception as e:
            errors.append(f"Q{i+1}: {str(e)}")

    # ── 6. Auto-create GrammarPoint records (content pipeline) ──
    from exam.grammar_sync import sync_grammar_points_from_questions
    sync_result = sync_grammar_points_from_questions(template_ids=[template.id])

    result = {
        "success": True,
        "message": f"Đã tạo {created_count}/{len(questions_data)} câu hỏi ngữ pháp",
        "template_id": template.id,
        "template_slug": template.slug,
        "created": created_count,
        "total": len(questions_data),
        "grammar_points_synced": sync_result,
        "ai_data": data,
    }
    if errors:
        result["errors"] = errors
    return result


# ═══════════════════════════════════════════════════════════
# ── EXAM: Direct JSON Import 文法 (Grammar quiz - no AI) ──
# ═══════════════════════════════════════════════════════════

class ImportGrammarJSONIn(Schema):
    json_text: str
    book_id: Optional[int] = None
    level: str = "N2"

@router.post("/exam/import-grammar-json/")
def import_grammar_json(request, payload: ImportGrammarJSONIn):
    """
    Direct JSON import for 文法 (Grammar) quizzes.
    Accepts pre-generated JSON (e.g., from manual Gemini calls) and saves to DB.
    Same save logic as import_grammar_ai but skips the Gemini API call.
    """
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}

    import re, logging
    logger = logging.getLogger(__name__)

    # ── 1. Parse JSON ──
    cleaned = payload.json_text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"success": False, "message": f"JSON parse error: {e}"}

    questions_data = data.get("questions", [])
    if not questions_data:
        return {"success": False, "message": "No 'questions' array found in JSON"}

    # ── 2. Create ExamTemplate ──
    from exam.models import ExamTemplate, ExamQuestion, ExamBook, QuestionType, ExamLevel, ExamCategory, ExamGroupType

    book = None
    if payload.book_id:
        try:
            book = ExamBook.objects.get(id=payload.book_id)
        except ExamBook.DoesNotExist:
            pass

    book_title = data.get("book_title", "JSON Import")
    exam_type = data.get("exam_type", "文法")
    template_title = f"{book_title} - {exam_type} ({len(questions_data)} câu)"

    template = ExamTemplate.objects.create(
        book=book,
        title=template_title,
        level=payload.level,
        category=ExamCategory.BUNPOU,
        group_type=ExamGroupType.BY_PATTERN,
        main_question_type=QuestionType.FILL_BLANK,
    )

    # ── 3. Create ExamQuestion records ──
    created_count = 0
    errors = []
    for i, q in enumerate(questions_data):
        try:
            sentence = q.get("sentence", "")
            sentence_completed = q.get("sentence_completed", "")
            sentence_vi = q.get("sentence_vi", "")
            correct = q.get("correct", 1)
            options = q.get("options", [])
            explanations = q.get("explanations", [])

            choices = [{"key": str(j + 1), "text": opt_text} for j, opt_text in enumerate(options)]

            explanation_json = {
                "grammar_point": q.get("grammar_point", ""),
                "grammar_reading": q.get("grammar_reading", ""),
                "grammar_meaning": q.get("grammar_meaning", ""),
                "grammar_structure": q.get("grammar_structure", ""),
                "grammar_note": q.get("grammar_note", ""),
                "grammar_furigana": q.get("grammar_furigana", ""),
                "grammar_topic": q.get("grammar_topic", ""),
                "sentence_completed": sentence_completed,
                "correct_translation": sentence_vi,
                "explanations": explanations,
                "examples": q.get("examples", []),
            }

            ExamQuestion.objects.create(
                template=template,
                order=i + 1,
                question_type=QuestionType.FILL_BLANK,
                text=sentence,
                text_vi=sentence_vi,
                data={"choices": choices},
                correct_answer=str(correct),
                explanation_json=explanation_json,
                mondai="01",
                order_in_mondai=i + 1,
            )
            created_count += 1
        except Exception as e:
            errors.append(f"Q{i+1}: {str(e)}")

    # ── 4. Auto-create GrammarPoint records ──
    from exam.grammar_sync import sync_grammar_points_from_questions
    sync_result = sync_grammar_points_from_questions(template_ids=[template.id])

    result = {
        "success": True,
        "message": f"Đã tạo {created_count}/{len(questions_data)} câu hỏi ngữ pháp từ JSON",
        "template_id": template.id,
        "template_slug": template.slug,
        "created": created_count,
        "total": len(questions_data),
        "grammar_points_synced": sync_result,
    }
    if errors:
        result["errors"] = errors
    return result


# ═══════════════════════════════════════════════════════════
# ── EXAM: AI Import 並べ替え (Sentence Ordering quiz) ──
# ═══════════════════════════════════════════════════════════

class ImportSentenceOrderAIIn(Schema):
    raw_text: str
    book_id: Optional[int] = None
    level: str = "N2"
    model: str = "gemini-2.5-flash"

@router.post("/exam/import-sentence-order-ai/")
def import_sentence_order_ai(request, payload: ImportSentenceOrderAIIn):
    """
    AI-powered import for 並べ替え (Sentence Ordering) quizzes.
    1. Send raw HTML exam data to Gemini API with sentence order prompt template
    2. Parse JSON response
    3. Create ExamTemplate + ExamQuestion records
    """
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}

    import os, re, logging
    logger = logging.getLogger(__name__)

    # ── 1. Build prompt ──
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", "extract_sentence_order_quiz.md"
    )
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return {"success": False, "message": "Sentence order prompt template not found"}

    full_prompt = prompt_template + "\n\n" + payload.raw_text

    # ── 2. Call Gemini ──
    from vocab.services.gemini_service import GeminiService
    raw_response = GeminiService.generate_text(full_prompt, model_name=payload.model)

    if not raw_response or raw_response.startswith("Error:"):
        return {"success": False, "message": f"Gemini API error: {raw_response}"}

    # ── 3. Parse JSON from response ──
    cleaned = raw_response.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "message": f"JSON parse error: {e}",
            "raw_response": raw_response[:2000],
        }

    questions_data = data.get("questions", [])
    if not questions_data:
        return {"success": False, "message": "No questions found in AI response", "raw_response": raw_response[:2000]}

    # ── 4. Create ExamTemplate ──
    from exam.models import ExamTemplate, ExamQuestion, ExamBook, QuestionType, ExamLevel, ExamCategory, ExamGroupType

    book = None
    if payload.book_id:
        try:
            book = ExamBook.objects.get(id=payload.book_id)
        except ExamBook.DoesNotExist:
            pass

    book_title = data.get("book_title", "AI Import")
    exam_type = data.get("exam_type", "並べ替え")
    template_title = f"{book_title} - {exam_type} ({len(questions_data)} câu)"

    template = ExamTemplate.objects.create(
        book=book,
        title=template_title,
        level=payload.level,
        category=ExamCategory.BUNPOU,
        group_type=ExamGroupType.BY_PATTERN,
        main_question_type=QuestionType.SENTENCE_ORDER,
    )

    # ── 5. Create ExamQuestion records ──
    created_count = 0
    errors = []
    for i, q in enumerate(questions_data):
        try:
            sentence = q.get("sentence", "")
            sentence_completed = q.get("sentence_completed", "")
            sentence_vi = q.get("sentence_vi", "")
            correct = q.get("correct", 1)
            correct_order = q.get("correct_order", "")
            options = q.get("options", [])

            # Build choices data (tokens for ordering)
            choices = []
            for j, opt_text in enumerate(options):
                choices.append({"key": str(j + 1), "text": opt_text})

            # Build explanation_json with grammar info
            grammar_examples = q.get("grammar_examples", [])
            explanation_json = {
                "grammar_point": q.get("grammar_point", ""),
                "grammar_reading": q.get("grammar_reading", ""),
                "grammar_meaning": q.get("grammar_meaning", ""),
                "grammar_structure": q.get("grammar_structure", ""),
                "grammar_note": q.get("grammar_note", ""),
                "sentence_completed": sentence_completed,
                "correct_translation": sentence_vi,
                "correct_order": correct_order,
                "grammar_examples": grammar_examples,
            }

            ExamQuestion.objects.create(
                template=template,
                order=i + 1,
                question_type=QuestionType.SENTENCE_ORDER,
                text=sentence,
                text_vi=sentence_vi,
                data={
                    "choices": choices,
                    "correct_order": correct_order,
                },
                correct_answer=str(correct),
                explanation_json=explanation_json,
                mondai="01",
                order_in_mondai=i + 1,
            )
            created_count += 1
        except Exception as e:
            errors.append(f"Q{i+1}: {str(e)}")

    # ── 6. Auto-create GrammarPoint records (content pipeline) ──
    from exam.grammar_sync import sync_grammar_points_from_questions
    sync_result = sync_grammar_points_from_questions(template_ids=[template.id])

    result = {
        "success": True,
        "message": f"Đã tạo {created_count}/{len(questions_data)} câu hỏi sắp xếp câu",
        "template_id": template.id,
        "template_slug": template.slug,
        "created": created_count,
        "total": len(questions_data),
        "grammar_points_synced": sync_result,
        "ai_data": data,
    }
    if errors:
        result["errors"] = errors
    return result


# ═══════════════════════════════════════════════════════════
# ── EXAM: Import English Exam (EN10) ──
# ═══════════════════════════════════════════════════════════

@router.post("/exam/english-import/")
def import_english_exam(request, payload: dict):
    """Import a full English Lớp 10 exam from structured JSON."""
    if not staff_required(request):
        return {"success": False, "message": "Unauthorized"}

    from exam.models import ExamTemplate, ExamQuestion, ReadingPassage, ExamLevel, ExamCategory, QuestionType

    title = payload.get("title", "English Exam")
    description = payload.get("description", "")
    time_limit = payload.get("time_limit_minutes", 60)
    sections = payload.get("sections", [])

    if not sections:
        return {"success": False, "message": "No sections found"}

    template = ExamTemplate.objects.create(
        title=title,
        description=description,
        level=ExamLevel.EN10,
        category=ExamCategory.ENGLISH,
        main_question_type=QuestionType.MCQ,
        time_limit_minutes=time_limit,
    )

    created = 0
    errors = []
    for section in sections:
        section_type = section.get("type", "grammar")
        section_title = section.get("title", "")

        passage = None
        passage_text = section.get("passage_text", "")
        if passage_text:
            passage = ReadingPassage.objects.create(
                template=template,
                title=section_title,
                text=passage_text,
                instruction=section.get("passage_instruction", ""),
            )

        for q_data in section.get("questions", []):
            try:
                ExamQuestion.objects.create(
                    template=template,
                    passage=passage,
                    order=q_data.get("num", created + 1),
                    question_type=QuestionType.MCQ,
                    text=q_data.get("text", ""),
                    text_vi=q_data.get("text_vi", ""),
                    correct_answer=q_data.get("correct_answer", ""),
                    explanation_json=q_data.get("explanation_json", {}),
                    data={
                        "choices": q_data.get("choices", []),
                        "section_type": section_type,
                        "section_title": section_title,
                    },
                )
                created += 1
            except Exception as e:
                errors.append(f"Q{q_data.get('num', '?')}: {str(e)}")

    result = {
        "success": True,
        "message": f"Imported {created} questions",
        "template_id": template.id,
        "template_slug": template.slug,
        "created": created,
    }
    if errors:
        result["errors"] = errors
    return result


# ═══════════════════════════════════════════════════════════
# ── VIP / SUBSCRIPTION MANAGEMENT ──
# ═══════════════════════════════════════════════════════════

@router.get("/vip/users/")
def vip_user_list(request, search: str = "", filter: str = "all", page: int = 1):
    """List users with their VIP status. filter: all / vip / non_vip"""
    if not staff_required(request):
        return {"items": [], "count": 0}

    from payment.models import Subscription

    page_size = 50
    qs = User.objects.all().select_related()
    if search:
        qs = qs.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    users_data = []
    for u in qs.order_by("-date_joined"):
        try:
            sub = u.subscription
            is_vip = sub.is_valid
            end_date = sub.end_date.isoformat() if sub.end_date else None
            plan_name = sub.plan.name if sub.plan else "—"
            sub_active = sub.is_active
        except Subscription.DoesNotExist:
            is_vip = False
            end_date = None
            plan_name = "—"
            sub_active = False

        if filter == "vip" and not is_vip:
            continue
        if filter == "non_vip" and is_vip:
            continue

        users_data.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": f"{u.first_name} {u.last_name}".strip() or "—",
            "is_vip": is_vip,
            "sub_active": sub_active,
            "end_date": end_date,
            "plan_name": plan_name,
            "date_joined": u.date_joined.isoformat(),
        })

    total = len(users_data)
    start = (page - 1) * page_size
    end = start + page_size
    return {"items": users_data[start:end], "count": total}


class VipGrantIn(Schema):
    duration_days: int = 365


@router.post("/vip/grant/{user_id}/")
def vip_grant(request, user_id: int, payload: VipGrantIn):
    """Grant or extend VIP for a user."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    from payment.models import Subscription, PaymentPlan

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"success": False, "message": "User not found"}

    # Get or create a plan for admin grants
    plan, _ = PaymentPlan.objects.get_or_create(
        slug="admin-vip-grant",
        defaults={
            "name": "VIP (Admin Grant)",
            "price": 0,
            "duration_days": payload.duration_days,
            "is_active": False,  # Hidden from public
        },
    )

    today = timezone.now().date()
    try:
        sub = user.subscription
        if sub.is_valid:
            # Extend from current end_date
            sub.end_date = sub.end_date + timedelta(days=payload.duration_days)
        else:
            sub.start_date = today
            sub.end_date = today + timedelta(days=payload.duration_days)
        sub.is_active = True
        sub.plan = plan
        sub.save()
    except Subscription.DoesNotExist:
        Subscription.objects.create(
            user=user,
            plan=plan,
            start_date=today,
            end_date=today + timedelta(days=payload.duration_days),
            is_active=True,
        )

    return {"success": True, "message": f"VIP granted to {user.username} for {payload.duration_days} days"}


@router.post("/vip/revoke/{user_id}/")
def vip_revoke(request, user_id: int):
    """Revoke VIP for a user."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    from payment.models import Subscription

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"success": False, "message": "User not found"}

    try:
        sub = user.subscription
        sub.is_active = False
        sub.end_date = timezone.now().date()
        sub.save()
    except Subscription.DoesNotExist:
        pass

    return {"success": True, "message": f"VIP revoked for {user.username}"}


# ═══════════════════════════════════════════════════════════
# ── TTS AUDIO GENERATION ──
# ═══════════════════════════════════════════════════════════

@router.get("/tts/stats/")
def tts_stats(request, language: str = "en"):
    """Get stats on how many WordEntries have/lack audio."""
    if not staff_required(request):
        return {"error": "Forbidden"}

    from vocab.models import WordEntry, Vocabulary

    total = WordEntry.objects.filter(vocab__language=language).count()

    if language == "en":
        has_us = WordEntry.objects.filter(vocab__language=language).exclude(audio_us="").count()
        has_uk = WordEntry.objects.filter(vocab__language=language).exclude(audio_uk="").count()
        missing = WordEntry.objects.filter(
            vocab__language=language, audio_us=""
        ).count()
    else:
        has_us = WordEntry.objects.filter(vocab__language=language).exclude(audio_us="").count()
        has_uk = 0
        missing = WordEntry.objects.filter(vocab__language=language, audio_us="").count()

    return {
        "total": total,
        "has_audio_us": has_us,
        "has_audio_uk": has_uk,
        "missing": missing,
        "language": language,
    }


@router.get("/tts/missing/")
def tts_missing_list(request, language: str = "en", page: int = 1):
    """List WordEntries missing audio."""
    if not staff_required(request):
        return {"items": [], "count": 0}

    from vocab.models import WordEntry

    page_size = 50
    qs = WordEntry.objects.filter(
        vocab__language=language, audio_us=""
    ).select_related("vocab").order_by("vocab__word")

    total = qs.count()
    start = (page - 1) * page_size
    items = [
        {
            "id": e.id,
            "word": e.vocab.word,
            "pos": e.part_of_speech,
            "ipa": e.ipa,
            "audio_us": e.audio_us,
            "audio_uk": e.audio_uk,
        }
        for e in qs[start : start + page_size]
    ]
    return {"items": items, "count": total}


class TtsBatchIn(Schema):
    language: str = "en"
    limit: int = 50
    force: bool = False


@router.post("/tts/generate-batch/")
def tts_generate_batch(request, payload: TtsBatchIn):
    """Trigger batch TTS generation in a background thread."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    from vocab.tts_service import batch_generate, get_batch_progress
    import threading

    progress = get_batch_progress()
    if progress.get("running"):
        return {"success": False, "message": "Batch already running", "progress": progress}

    def run():
        batch_generate(
            language=payload.language,
            limit=payload.limit,
            force=payload.force,
        )

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"success": True, "message": f"Batch started: {payload.limit} entries ({payload.language})"}


@router.get("/tts/progress/")
def tts_progress(request):
    """Get current batch TTS progress."""
    if not staff_required(request):
        return {"error": "Forbidden"}

    from vocab.tts_service import get_batch_progress
    return get_batch_progress()


class TtsSingleIn(Schema):
    entry_id: int
    force: bool = False


@router.post("/tts/generate-single/")
def tts_generate_single(request, payload: TtsSingleIn):
    """Generate TTS for a single WordEntry."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    from vocab.tts_service import generate_audio_for_entry

    try:
        result = generate_audio_for_entry(payload.entry_id, force=payload.force)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =============================================
#  EXAM LOCK / PUBLIC MANAGEMENT
# =============================================

@router.get("/exams/english/")
def admin_english_exams(request, search: str = ""):
    """List all English Lớp 10 exam templates with public/locked status."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    from exam.models import ExamTemplate, ExamLevel, ExamCategory

    qs = ExamTemplate.objects.filter(
        level=ExamLevel.EN10,
        category=ExamCategory.ENGLISH,
    ).order_by("lesson_index", "id")

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(slug__icontains=search))

    items = []
    for t in qs:
        items.append({
            "id": t.id,
            "title": t.title,
            "slug": t.slug,
            "description": t.description,
            "total_questions": t.questions.count(),
            "is_public": t.is_public,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return {"success": True, "items": items, "total": len(items)}


@router.post("/exams/english/{exam_id}/toggle-public/")
def admin_toggle_exam_public(request, exam_id: int):
    """Toggle is_public flag for an English exam."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    from exam.models import ExamTemplate

    try:
        t = ExamTemplate.objects.get(id=exam_id)
    except ExamTemplate.DoesNotExist:
        return {"success": False, "message": "Exam not found"}

    t.is_public = not t.is_public
    t.save(update_fields=["is_public"])

    return {
        "success": True,
        "id": t.id,
        "is_public": t.is_public,
        "message": f"Đề '{t.title}' đã {'mở công khai' if t.is_public else 'khóa VIP'}.",
    }


@router.post("/exams/english/bulk-toggle/")
def admin_bulk_toggle_exams(request):
    """Bulk toggle is_public for multiple exams."""
    if not staff_required(request):
        return {"success": False, "message": "Forbidden"}

    import json
    body = json.loads(request.body)
    ids = body.get("ids", [])
    action = body.get("action", "public")  # "public" or "lock"

    from exam.models import ExamTemplate

    updated = ExamTemplate.objects.filter(id__in=ids).update(
        is_public=(action == "public")
    )

    return {
        "success": True,
        "updated": updated,
        "message": f"Đã {'mở công khai' if action == 'public' else 'khóa VIP'} {updated} đề.",
    }
