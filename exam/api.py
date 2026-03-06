"""Exam API — hub, templates, books, choukai, dokkai, sessions."""

from ninja import Router, Schema
from ninja.errors import HttpError
from typing import Dict, List, Optional
from exam.quiz_service import QuizService, USAGE_CONFIG, BUNPOU_CONFIG
from exam.exam_service import AnswerService, ExamSessionService
from exam.utils import ruby_to_html, audio_url

router = Router()


@router.get("")
@router.get("/list")
def exam_hub(request):
    """Exam hub — categories and recent attempts."""
    from django.core.cache import cache
    from exam.models import ExamBook, ExamAttempt

    # Cache the books list (shared across users)
    books_key = "exam_hub_books"
    books_data = cache.get(books_key)
    if books_data is None:
        books = ExamBook.objects.filter(is_active=True)[:6]
        books_data = [
            {"id": b.id, "title": b.title, "slug": b.slug, "level": b.level, "category": b.category}
            for b in books
        ]
        cache.set(books_key, books_data, 1800)  # 30 min

    recent = []
    try:
        attempts = ExamAttempt.objects.filter(user=request.user).select_related("template")[:5]
        recent = [
            {
                "id": a.id,
                "title": a.template.title,
                "score": a.score_percent,
                "correct": a.correct_count,
                "total": a.total_questions,
                "date": a.started_at.isoformat(),
            }
            for a in attempts
        ]
    except Exception:
        pass
    return {
        "books": books_data,
        "recent_attempts": recent,
    }


@router.get("/toeic")
def toeic_list(request):
    """List TOEIC exams."""
    from exam.models import ExamTemplate
    templates = ExamTemplate.objects.filter(level="TOEIC", is_active=True)
    return {
        "templates": [
            {
                "id": t.id, "title": t.title, "slug": t.slug,
                "category": t.category, "question_count": t.total_questions,
            }
            for t in templates
        ]
    }


@router.get("/books")
def list_books(request):
    """List exam books."""
    from exam.models import ExamBook
    books = ExamBook.objects.filter(is_active=True).prefetch_related("tests")
    return [
        {
            "id": b.id,
            "title": b.title,
            "slug": b.slug,
            "level": b.level,
            "category": b.category,
            "description": b.description,
            "template_count": b.tests.filter(is_active=True).count(),
        }
        for b in books
    ]


@router.get("/books/{slug}")
def book_detail(request, slug: str):
    """Get exam book detail."""
    from exam.models import ExamBook
    b = ExamBook.objects.prefetch_related("tests").get(slug=slug, is_active=True)
    return {
        "id": b.id,
        "title": b.title,
        "slug": b.slug,
        "level": b.level,
        "category": b.category,
        "description": b.description,
        "templates": [
            {
                "id": t.id, "title": t.title, "slug": t.slug,
                "category": t.category, "question_count": t.total_questions,
            }
            for t in b.tests.filter(is_active=True)
        ],
    }


@router.get("/choukai")
@router.get("/choukai/books")
def choukai_list(request):
    """List choukai books."""
    from exam.models import ExamBook
    books = ExamBook.objects.filter(is_active=True, category="CHOUKAI").prefetch_related("tests__questions")
    result = []
    for b in books:
        q_count = sum(len(t.questions.all()) for t in b.tests.all())
        result.append({
            "id": b.id,
            "title": b.title,
            "slug": b.slug,
            "level": b.level,
            "description": b.description,
            "cover_url": b.cover_image.url if b.cover_image else "",
            "question_count": q_count,
        })
    return result


@router.post("/choukai/save-answer")
def choukai_save_answer(request):
    """Save a single choukai answer."""
    import json

    if not request.user.is_authenticated:
        return {"success": True, "saved": False}

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        selected_key = str(data.get('selected_key', ''))
        if not question_id or not selected_key:
            return {"success": False, "error": "Missing fields"}

        result = AnswerService.save_single_answer(
            request.user, question_id, selected_key, mode="choukai"
        )
        return {"success": True, "saved": True, "is_correct": result["is_correct"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/choukai/{slug}")
def choukai_detail(request, slug: str):
    """Get choukai book detail with mondai groups (lightweight, for lazy-loading)."""
    import re
    from exam.models import ExamBook, ExamTemplate, ExamAttempt

    _MONDAI_LABELS = {
        '1': 'もんだい1 課題理解', '2': 'もんだい2 ポイント理解',
        '3': 'もんだい3 概要理解', '4': 'もんだい4 発話表現',
        '5': 'もんだい5 即時応答',
    }

    b = ExamBook.objects.get(slug=slug)
    tpl = ExamTemplate.objects.filter(book=b, is_active=True, category="CHOUKAI").first()

    groups = []
    total_questions = 0
    if tpl:
        qs = tpl.questions.order_by("mondai", "order_in_mondai")
        cur_k, cur_ids = None, []
        for q in qs:
            m = q.mondai or "0"
            if m != cur_k:
                if cur_k is not None:
                    groups.append({
                        "key": cur_k,
                        "label": _MONDAI_LABELS.get(cur_k, cur_k),
                        "count": len(cur_ids),
                        "qids": cur_ids,
                    })
                cur_k, cur_ids = m, []
            cur_ids.append({"id": q.id, "num": q.order_in_mondai, "correct": q.correct_answer})
        if cur_k is not None:
            groups.append({
                "key": cur_k,
                "label": _MONDAI_LABELS.get(cur_k, cur_k),
                "count": len(cur_ids),
                "qids": cur_ids,
            })
        total_questions = sum(g["count"] for g in groups)

    first_key = groups[0]["key"] if groups else ""

    # Load previous answers for authenticated users
    initial_answers = {}
    try:
        if request.user.is_authenticated and tpl:
            attempt = ExamAttempt.objects.filter(
                user=request.user, template=tpl, status=ExamAttempt.Status.IN_PROGRESS,
            ).first()
            if attempt:
                for qa in attempt.answers.all():
                    initial_answers[str(qa.question_id)] = qa.raw_answer.get('selected_key', '')
    except Exception:
        pass

    return {
        "id": b.id,
        "title": b.title,
        "slug": b.slug,
        "level": b.level,
        "description": b.description or "",
        "cover_url": b.cover_image.url if b.cover_image else "",
        "mondai_groups": groups,
        "total_questions": total_questions,
        "first_key": first_key,
        "initial_answers": initial_answers,
    }


@router.get("/choukai/{slug}/mondai/{mondai_key}")
def choukai_mondai(request, slug: str, mondai_key: str):
    """Lazy-load full question data for a single mondai group."""
    from exam.models import ExamBook, ExamTemplate

    b = ExamBook.objects.get(slug=slug)
    tpl = ExamTemplate.objects.filter(book=b, is_active=True, category="CHOUKAI").first()
    if not tpl:
        return {"questions": []}

    qs = tpl.questions.filter(mondai=mondai_key).order_by("order_in_mondai")
    questions = []
    for q in qs:
        d = q.data or {}
        no_image_mondais = {"3", "5"} if b.level == "N3" else set()
        img_url = "" if mondai_key in no_image_mondais or d.get('image_type') == 'TEXT_OPTIONS_ONLY' else (q.image.url if q.image else "")

        questions.append({
            "id": q.id,
            "num": q.order_in_mondai,
            "audio_url": audio_url(q),
            "image_url": img_url,
            "text": q.text,
            "correct": q.correct_answer,
            "choices": [
                {"key": str(c.get("number")), "html": ruby_to_html(c.get("text"))}
                for c in (d.get("choices") or d.get("answer_options") or [])
            ],
            "lines": [
                {"speaker": l.get("speaker"), "html": ruby_to_html(l.get("text")), "vi": l.get("text_vi")}
                for l in d.get("conversation", [])
            ],
        })

    return {"questions": questions}


@router.get("/dokkai")
@router.get("/dokkai/list")
def dokkai_list(request):
    """List dokkai exercises."""
    from exam.models import ExamTemplate
    from django.db.models import Count
    templates = ExamTemplate.objects.filter(
        category__in=["DOKKAI", "MIX"], is_active=True
    ).select_related("book").annotate(
        q_count=Count("questions")
    )
    return [
        {
            "id": t.id,
            "title": t.title,
            "slug": t.slug,
            "level": t.level,
            "reading_format": t.reading_format,
            "description": t.description or "",
            "question_count": t.q_count,
            "book_title": t.book.title if t.book else None,
        }
        for t in templates
    ]


@router.get("/dokkai/{slug}")
def dokkai_detail(request, slug: str):
    """Get dokkai passage with questions."""
    from exam.models import ExamTemplate

    t = ExamTemplate.objects.prefetch_related("passages", "questions").get(slug=slug)
    passages = []
    for p in t.passages.all():
        bilingual = []
        if p.data:
            bilingual = p.data.get('bilingual_reading', [])
        passages.append({
            "id": p.id,
            "title": p.title,
            "text_html": ruby_to_html(p.text) if p.text else "",
            "image_url": p.image.url if p.image else "",
            "instruction": p.instruction,
            "bilingual_reading": bilingual,
            "vocabulary": p.data.get('vocabulary', []) if p.data else [],
        })

    questions = []
    for q in t.questions.all():
        choices_raw = q.data.get('choices', [])
        norm_choices = []
        for c in choices_raw:
            key = str(c.get('key') or c.get('number') or '')
            text = c.get('text', '')
            norm_choices.append({
                'key': key,
                'text': text,
                'text_html': ruby_to_html(text),
            })
        questions.append({
            "id": q.id,
            "text_html": ruby_to_html(q.text) if q.text else "",
            "choices": norm_choices,
            "correct_answer": q.correct_answer,
            "explanation_json": q.explanation_json or {},
        })

    return {
        "id": t.id,
        "title": t.title,
        "slug": t.slug,
        "level": t.level,
        "reading_format": t.reading_format or "",
        "total_count": len(questions),
        "passages": passages,
        "questions": questions,
    }


@router.get("/usage/all-questions")
def usage_all_questions(request, level: str = "", page: int = 1, page_size: int = 9999):
    """Return usage questions with pagination for the grid UI."""
    return QuizService.get_all_questions(USAGE_CONFIG, level, page, page_size)


@router.post("/usage/sync-to-fsrs")
def usage_sync_to_fsrs(request):
    """
    Import all usage quiz words into the FSRS system for the current user.
    Creates Vocabulary + WordEntry + WordDefinition + FsrsCardStateEn as needed.
    """
    from exam.models import ExamQuestion, ExamTemplate
    from vocab.models import Vocabulary, WordEntry, WordDefinition, FsrsCardStateEn
    from vocab.fsrs_bridge import create_new_card_state, card_data_to_dict, CARD_STATE_NEW
    from django.utils import timezone

    # 1. Gather all usage quiz words
    t_ids = ExamTemplate.objects.filter(
        is_active=True, main_question_type="USAGE"
    ).values_list("id", flat=True)

    word_data = {}  # word -> {reading, han_viet, meaning_vi}
    for q in ExamQuestion.objects.filter(template_id__in=t_ids):
        ej = q.explanation_json or {}
        w = ej.get("word", "").strip()
        if not w or w in word_data:
            continue
        word_data[w] = {
            "reading": ej.get("reading", ""),
            "han_viet": ej.get("han_viet", ""),
            "meaning_vi": ej.get("meaning_vi", ""),
        }

    if not word_data:
        return {"synced": 0, "total": 0}

    # 2. Find or create Vocabulary entries
    existing_vocabs = {v.word: v for v in Vocabulary.objects.filter(word__in=word_data.keys())}
    new_vocabs = []
    for w, data in word_data.items():
        if w not in existing_vocabs:
            new_vocabs.append(Vocabulary(
                word=w,
                language="jp",
                extra_data={
                    "reading": data["reading"],
                    "han_viet": data["han_viet"],
                },
            ))
    if new_vocabs:
        Vocabulary.objects.bulk_create(new_vocabs, ignore_conflicts=True)
        # Re-fetch to get IDs
        existing_vocabs = {v.word: v for v in Vocabulary.objects.filter(word__in=word_data.keys())}

    # 3. Ensure WordEntry + WordDefinition for each
    vocab_ids = [v.id for v in existing_vocabs.values()]
    existing_entries = {
        e.vocab_id: e
        for e in WordEntry.objects.filter(vocab_id__in=vocab_ids)
    }
    new_entries = []
    for w, vocab in existing_vocabs.items():
        if vocab.id not in existing_entries:
            new_entries.append(WordEntry(vocab=vocab, part_of_speech=""))
    if new_entries:
        created = WordEntry.objects.bulk_create(new_entries, ignore_conflicts=True)
        existing_entries = {
            e.vocab_id: e
            for e in WordEntry.objects.filter(vocab_id__in=vocab_ids)
        }

    # Create definitions where missing
    entry_ids = [e.id for e in existing_entries.values()]
    existing_defs = set(
        WordDefinition.objects.filter(entry_id__in=entry_ids).values_list("entry_id", flat=True)
    )
    new_defs = []
    for w, vocab in existing_vocabs.items():
        entry = existing_entries.get(vocab.id)
        if entry and entry.id not in existing_defs:
            meaning = word_data[w].get("meaning_vi", "")
            if meaning:
                new_defs.append(WordDefinition(entry=entry, meaning=meaning))
    if new_defs:
        WordDefinition.objects.bulk_create(new_defs, ignore_conflicts=True)

    # 4. Create FsrsCardStateEn for the user
    existing_states = set(
        FsrsCardStateEn.objects.filter(
            user=request.user, vocab_id__in=vocab_ids
        ).values_list("vocab_id", flat=True)
    )
    now = timezone.now()
    new_card = card_data_to_dict(create_new_card_state())
    new_states = []
    for vocab in existing_vocabs.values():
        if vocab.id not in existing_states:
            new_states.append(FsrsCardStateEn(
                user=request.user,
                vocab=vocab,
                card_data=new_card,
                state=CARD_STATE_NEW,
                due=now,
            ))
    if new_states:
        FsrsCardStateEn.objects.bulk_create(new_states, ignore_conflicts=True)

    return {
        "synced": len(new_states),
        "total": len(word_data),
        "already_existed": len(word_data) - len(new_states),
    }

@router.get("/usage")
@router.get("/usage/list")
def usage_list(request, level: str = ""):
    """List 用法 (Usage) quiz templates."""
    return QuizService.list_templates(USAGE_CONFIG, level)


@router.get("/usage/{slug}")
def usage_detail(request, slug: str):
    """Get usage quiz detail with full questions + explanations for client-side quiz."""
    return QuizService.get_detail(slug)


# ── Bunpou (文法) endpoints ──

@router.get("/bunpou/grammar-patterns")
def bunpou_grammar_patterns(request, level: str = ""):
    """Extract unique grammar patterns from all bunpou questions (cached)."""
    from django.core.cache import cache
    from exam.models import ExamQuestion, ExamTemplate

    cache_key = f"bunpou_patterns_{level or 'all'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = ExamQuestion.objects.filter(
        template__category="BUN",
        template__is_active=True,
    ).select_related("template").order_by("template__level", "id")

    if level:
        qs = qs.filter(template__level=level)

    seen = {}   # grammar_point -> data dict
    for q in qs:
        ej = q.explanation_json or {}
        gp = ej.get("grammar_point", "").strip()
        if not gp:
            continue
        if gp not in seen:
            seen[gp] = {
                "grammar_point": gp,
                "grammar_furigana": ej.get("grammar_furigana", ""),
                "grammar_structure": ej.get("grammar_structure", ""),
                "grammar_meaning": ej.get("grammar_meaning", ""),
                "grammar_note": ej.get("grammar_note", ""),
                "grammar_topic": ej.get("grammar_topic", ""),
                "grammar_reading": ej.get("grammar_reading", ""),
                "examples": ej.get("examples", []),
                "level": q.template.level,
                "question_count": 0,
                "question_ids": [],
            }
        seen[gp]["question_count"] += 1
        seen[gp]["question_ids"].append(q.id)
        # Merge examples from different questions
        exs = ej.get("examples", [])
        existing = seen[gp]["examples"]
        existing_texts = {e.get("ja", "") for e in existing}
        for ex in exs:
            if ex.get("ja", "") not in existing_texts:
                existing.append(ex)
                existing_texts.add(ex.get("ja", ""))

    patterns = sorted(seen.values(), key=lambda p: (p["level"], p["grammar_point"]))
    level_stats = {}
    for p in patterns:
        lv = p["level"]
        level_stats[lv] = level_stats.get(lv, 0) + 1

    result = {
        "patterns": patterns,
        "total": len(patterns),
        "level_stats": level_stats,
    }
    cache.set(cache_key, result, 3600)  # 1 hour
    return result

@router.get("/bunpou/all-questions")
def bunpou_all_questions(request, level: str = "", page: int = 1, page_size: int = 9999):
    """Return bunpou questions with pagination for the grid UI."""
    return QuizService.get_all_questions(BUNPOU_CONFIG, level, page, page_size)


@router.post("/bunpou/sync-to-fsrs")
def bunpou_sync_to_fsrs(request):
    """
    Sync bunpou quiz grammar patterns into FSRS for the current user.
    Step 1: Ensure GrammarPoint records exist (via shared pipeline utility).
    Step 2: Create FsrsCardStateGrammar for the user's new grammar points.
    """
    from grammar.models import GrammarPoint, FsrsCardStateGrammar
    from vocab.fsrs_bridge import create_new_card_state, card_data_to_dict, CARD_STATE_NEW
    from django.utils import timezone

    # 1. Ensure GrammarPoint records exist (idempotent)
    from exam.grammar_sync import sync_grammar_points_from_questions
    sync_result = sync_grammar_points_from_questions()

    # 2. Create FsrsCardStateGrammar for the user
    all_gps = GrammarPoint.objects.filter(is_active=True)
    gp_ids = list(all_gps.values_list("id", flat=True))

    existing_states = set(
        FsrsCardStateGrammar.objects.filter(
            user=request.user, grammar_point_id__in=gp_ids
        ).values_list("grammar_point_id", flat=True)
    )

    now = timezone.now()
    new_card = card_data_to_dict(create_new_card_state())
    new_states = []
    for gp_id in gp_ids:
        if gp_id not in existing_states:
            new_states.append(FsrsCardStateGrammar(
                user=request.user,
                grammar_point_id=gp_id,
                card_data=new_card,
                state=CARD_STATE_NEW,
                due=now,
            ))
    if new_states:
        FsrsCardStateGrammar.objects.bulk_create(new_states, ignore_conflicts=True)

    return {
        "synced": len(new_states),
        "total": len(gp_ids),
        "already_existed": len(gp_ids) - len(new_states),
        "grammar_points": sync_result,
    }


@router.get("/bunpou")
@router.get("/bunpou/list")
def bunpou_list(request, level: str = ""):
    """List 文法 (Bunpou) quiz templates."""
    return QuizService.list_templates(BUNPOU_CONFIG, level)


@router.get("/bunpou/{slug}")
def bunpou_detail(request, slug: str):
    """Get bunpou quiz detail with full questions + explanations for client-side quiz."""
    return QuizService.get_detail(slug)


# ── EN10 Grammar Topics & Phrasal Verbs endpoints ─────────
# NOTE: Must appear BEFORE the catch-all /{slug} route

@router.get("/english/grammar-topics", auth=None)
def en10_grammar_topics_list(request):
    """List all EN10 grammar topics (for the topics grid page)."""
    from exam.models import EN10GrammarTopic

    topics = EN10GrammarTopic.objects.filter(is_active=True).order_by("order")
    return [
        {
            "topic_id": t.topic_id,
            "title": t.title,
            "title_vi": t.title_vi,
            "emoji": t.emoji,
            "description": t.description,
            "difficulty": t.difficulty,
            "question_count": t.question_count,
            "order": t.order,
        }
        for t in topics
    ]


@router.get("/english/grammar-topics/{topic_id}", auth=None)
def en10_grammar_topic_detail(request, topic_id: str):
    """Get full grammar topic with theory sections, formulas, and exercises."""
    from exam.models import EN10GrammarTopic

    try:
        t = EN10GrammarTopic.objects.get(topic_id=topic_id, is_active=True)
    except EN10GrammarTopic.DoesNotExist:
        raise HttpError(404, "Grammar topic not found")

    return {
        "topic_id": t.topic_id,
        "title": t.title,
        "title_vi": t.title_vi,
        "emoji": t.emoji,
        "description": t.description,
        "difficulty": t.difficulty,
        "question_count": t.question_count,
        "sections": t.sections,
        "formulas": t.formulas,
        "exercises": t.exercises,
    }


@router.get("/english/phrasal-verbs-data", auth=None)
def en10_phrasal_verbs_data(request):
    """Get all phrasal verbs data (verbs, fill sentences, quiz questions)."""
    from exam.models import EN10PhrasalVerbSet

    pv = EN10PhrasalVerbSet.objects.filter(is_active=True).first()
    if not pv:
        return {"verbs": [], "fill_sentences": [], "quiz_questions": []}

    return {
        "verbs": pv.verbs,
        "fill_sentences": pv.fill_sentences,
        "quiz_questions": pv.quiz_questions,
    }


@router.get("/english/vocab-topics", auth=None)
def en10_vocab_topics_list(request):
    """List all EN10 vocabulary topics (for the topics grid page)."""
    from exam.models import EN10VocabTopic

    topics = EN10VocabTopic.objects.filter(is_active=True).order_by("order")
    return [
        {
            "slug": t.slug,
            "title": t.title,
            "title_vi": t.title_vi,
            "emoji": t.emoji,
            "word_count": t.word_count,
        }
        for t in topics
    ]


@router.get("/english/vocab-topics/{slug}", auth=None)
def en10_vocab_topic_detail(request, slug: str):
    """Get vocabulary topic with full word list."""
    from exam.models import EN10VocabTopic

    try:
        t = EN10VocabTopic.objects.get(slug=slug, is_active=True)
    except EN10VocabTopic.DoesNotExist:
        raise HttpError(404, "Vocabulary topic not found")

    return {
        "slug": t.slug,
        "title": t.title,
        "title_vi": t.title_vi,
        "emoji": t.emoji,
        "word_count": t.word_count,
        "words": t.words,
    }


# ── English 10th Grade Exam endpoints ─────────────────────
# NOTE: Must appear BEFORE the catch-all /{slug} route

@router.get("/english", auth=None)
@router.get("/english/", auth=None)
def english_list(request):
    """List all English Lớp 10 exam templates."""
    from exam.models import ExamTemplate, ExamLevel, ExamCategory, ExamAttempt

    # Check VIP status via subscription
    is_vip = False
    if request.user and request.user.is_authenticated:
        try:
            is_vip = request.user.subscription.is_valid
        except Exception:
            is_vip = False

    templates = ExamTemplate.objects.filter(
        level=ExamLevel.EN10,
        category=ExamCategory.ENGLISH,
        is_active=True,
    ).order_by("lesson_index", "id")

    items = []
    for t in templates:
        best_score = None
        attempted = False
        if request.user and request.user.is_authenticated:
            attempt = ExamAttempt.objects.filter(
                user=request.user,
                template=t,
                status=ExamAttempt.Status.SUBMITTED,
            ).order_by("-correct_count").first()
            if attempt:
                attempted = True
                best_score = attempt.score_percent

        items.append({
            "id": t.id,
            "title": t.title,
            "slug": t.slug,
            "description": t.description,
            "total_questions": t.questions.count(),
            "time_limit_minutes": t.time_limit_minutes or 60,
            "attempted": attempted,
            "best_score": best_score,
            "is_public": t.is_public,
        })

    return {
        "items": items,
        "total": len(items),
        "is_vip": is_vip,
    }


@router.get("/english/{slug}", auth=None)
def english_detail(request, slug: str):
    """Get full English exam with questions grouped by section."""
    from exam.models import ExamTemplate, ExamLevel, ExamCategory, ReadingPassage

    # Check VIP status
    is_vip = False
    if request.user and request.user.is_authenticated:
        try:
            is_vip = request.user.subscription.is_valid
        except Exception:
            is_vip = False

    try:
        template = ExamTemplate.objects.get(
            slug=slug,
            level=ExamLevel.EN10,
            category=ExamCategory.ENGLISH,
        )
    except ExamTemplate.DoesNotExist:
        raise HttpError(404, "Exam not found")

    # Non-VIP: return basic info only, no questions (unless exam is public)
    if not is_vip and not template.is_public:
        return {
            "id": template.id,
            "title": template.title,
            "slug": template.slug,
            "description": template.description,
            "total_questions": template.questions.count(),
            "time_limit_minutes": template.time_limit_minutes or 60,
            "sections": [],
            "is_vip": False,
        }

    questions = template.questions.order_by("order").all()
    passages = {p.id: p for p in ReadingPassage.objects.filter(template=template)}

    sections = []
    current_section = None

    for q in questions:
        section_type = q.data.get("section_type", "grammar")
        section_title = q.data.get("section_title", "")

        if current_section is None or current_section["type"] != section_type or (section_title and current_section["title"] != section_title):
            current_section = {
                "type": section_type,
                "title": section_title,
                "passage": None,
                "questions": [],
            }
            if q.passage_id and q.passage_id in passages:
                p = passages[q.passage_id]
                current_section["passage"] = {
                    "id": p.id,
                    "title": p.title,
                    "text": p.text,
                    "instruction": p.instruction,
                    "content_json": p.content_json,
                }
            sections.append(current_section)

        choices = q.data.get("choices", [])
        current_section["questions"].append({
            "id": q.id,
            "num": q.order,
            "text": q.text,
            "text_vi": q.text_vi,
            "choices": choices,
            "correct_answer": q.correct_answer,
            "explanation_json": q.explanation_json,
            "section_type": section_type,
        })

    return {
        "id": template.id,
        "title": template.title,
        "slug": template.slug,
        "description": template.description,
        "total_questions": len(questions),
        "time_limit_minutes": template.time_limit_minutes or 60,
        "sections": sections,
        "is_vip": True,
    }

@router.get("/english/{slug}/review", auth=None)
def english_review(request, slug: str):
    """Get review quiz items for an English exam."""
    import json
    from pathlib import Path
    from exam.models import ExamTemplate, ExamLevel, ExamCategory

    try:
        template = ExamTemplate.objects.get(
            slug=slug,
            level=ExamLevel.EN10,
            category=ExamCategory.ENGLISH,
        )
    except ExamTemplate.DoesNotExist:
        raise HttpError(404, "Exam not found")

    # Load review fixture
    fixture_path = Path(__file__).parent / "fixtures" / f"en10_{slug.replace('-', '_').replace('e_so_1_tieng_anh_vao_lop_10', 'de_so_1')}_review.json"

    # Try common naming patterns
    if not fixture_path.exists():
        # Try slug-based name
        for f in (Path(__file__).parent / "fixtures").glob("*_review.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("exam_slug") == slug:
                    fixture_path = f
                    break
            except Exception:
                continue

    if not fixture_path.exists():
        return {"exam_slug": slug, "exam_title": template.title, "items": []}

    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    # Optional: filter by type
    quiz_type = request.GET.get("type")
    items = data.get("items", [])
    if quiz_type:
        items = [i for i in items if i.get("type") == quiz_type]

    return {
        "exam_slug": slug,
        "exam_title": template.title,
        "items": items,
        "total": len(items),
        "types": list(set(i.get("type") for i in data.get("items", []))),
    }


class ReviewResultIn(Schema):
    quiz_type: str
    correct_count: int
    total_count: int
    answers_json: dict = {}
    completed: bool = False


@router.post("/english/{slug}/review/save")
def english_review_save(request, slug: str, payload: ReviewResultIn):
    """Save or update a review quiz result for the authenticated user."""
    from exam.models import ExamTemplate, ExamLevel, ExamCategory, ExamReviewResult

    template = ExamTemplate.objects.get(
        slug=slug,
        level=ExamLevel.EN10,
        category=ExamCategory.ENGLISH,
    )

    result, created = ExamReviewResult.objects.update_or_create(
        user=request.user,
        template=template,
        quiz_type=payload.quiz_type,
        defaults={
            "correct_count": payload.correct_count,
            "total_count": payload.total_count,
            "answers_json": payload.answers_json,
            "completed": payload.completed,
        },
    )

    return {
        "success": True,
        "created": created,
        "id": result.id,
        "quiz_type": result.quiz_type,
        "correct_count": result.correct_count,
        "total_count": result.total_count,
        "completed": result.completed,
    }


@router.get("/english/{slug}/review/my-results")
def english_review_my_results(request, slug: str):
    """Get all review quiz results for the authenticated user for this exam."""
    from exam.models import ExamTemplate, ExamLevel, ExamCategory, ExamReviewResult

    template = ExamTemplate.objects.get(
        slug=slug,
        level=ExamLevel.EN10,
        category=ExamCategory.ENGLISH,
    )

    results = ExamReviewResult.objects.filter(
        user=request.user,
        template=template,
    )

    return {
        "results": [
            {
                "quiz_type": r.quiz_type,
                "correct_count": r.correct_count,
                "total_count": r.total_count,
                "answers_json": r.answers_json,
                "completed": r.completed,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in results
        ]
    }


class EnglishImportIn(Schema):
    title: str
    description: str = ""
    time_limit_minutes: int = 60
    sections: list


@router.post("/english/import", auth=None)
def english_import(request, payload: EnglishImportIn):
    """Import a full English exam from structured JSON."""
    from exam.models import ExamTemplate, ExamLevel, ExamCategory, ExamQuestion, ReadingPassage, QuestionType

    template = ExamTemplate.objects.create(
        title=payload.title,
        description=payload.description,
        level=ExamLevel.EN10,
        category=ExamCategory.ENGLISH,
        main_question_type=QuestionType.MCQ,
        time_limit_minutes=payload.time_limit_minutes,
    )

    created = 0
    for section in payload.sections:
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

    return {
        "success": True,
        "message": f"Imported {created} questions",
        "template_id": template.id,
        "template_slug": template.slug,
        "created": created,
    }


# ── Catch-all exam route (must be LAST) ──

@router.get("/{slug}")
def exam_detail(request, slug: str):
    """Get exam template detail."""
    from exam.models import ExamTemplate
    t = ExamTemplate.objects.select_related("book").get(slug=slug, is_active=True)
    return {
        "id": t.id,
        "title": t.title,
        "slug": t.slug,
        "level": t.level,
        "category": t.category,
        "description": t.description,
        "question_count": t.total_questions,
        "time_limit_minutes": t.time_limit_minutes,
        "book": {"id": t.book.id, "title": t.book.title, "slug": t.book.slug} if t.book else None,
    }


@router.post("/attempt/start")
def start_attempt(request, template_slug: str):
    """Start an exam attempt."""
    return ExamSessionService.start_attempt(request.user, template_slug)


@router.get("/attempt/{attempt_id}")
def attempt_detail(request, attempt_id: int):
    """Get attempt with questions."""
    return ExamSessionService.get_attempt_detail(request.user, attempt_id)


class SubmitAnswersIn(Schema):
    """Body schema for submit_attempt — maps question ID → selected answer key."""
    answers: Dict[str, str]


@router.post("/attempt/{attempt_id}/submit")
def submit_attempt(request, attempt_id: int, payload: SubmitAnswersIn):
    """Submit exam attempt answers."""
    return ExamSessionService.submit_attempt(request.user, attempt_id, payload.answers)


@router.get("/attempt/{attempt_id}/result")
def attempt_result(request, attempt_id: int):
    """Get exam attempt results."""
    return ExamSessionService.get_result(request.user, attempt_id)


# ── Quiz Progress (mobile-friendly) ──────────────────────────

class SaveAnswerIn(Schema):
    template_slug: str
    question_id: int
    selected_key: str


@router.post("/quiz/save-answer")
def quiz_save_answer(request, payload: SaveAnswerIn):
    """
    Save a single answer in real-time.
    Creates or reuses an in-progress attempt for the template.
    """
    result = AnswerService.save_single_answer(
        request.user, payload.question_id, payload.selected_key, mode="quiz"
    )
    return result


@router.get("/quiz/{quiz_type}/progress")
def quiz_progress(request, quiz_type: str):
    """Get user's quiz progress for a quiz type."""
    return ExamSessionService.get_progress(request.user, quiz_type)


@router.get("/quiz/today-stats")
def quiz_today_stats(request):
    """Get today's quiz activity for the dashboard."""
    from django.utils import timezone
    from django.db.models import Count, Q
    from exam.models import QuestionAnswer

    today = timezone.now().date()
    qs = QuestionAnswer.objects.filter(
        attempt__user=request.user, created_at__date=today,
    )

    # Single aggregate for totals
    totals = qs.aggregate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
    )

    # Group by category in SQL
    by_type = {}
    category_stats = qs.values(
        'attempt__template__category'
    ).annotate(
        answered=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
    )
    for row in category_stats:
        cat = row['attempt__template__category']
        by_type[cat] = {
            "answered": row['answered'],
            "correct": row['correct'],
        }

    return {
        "date": str(today),
        "total_answered": totals['total'],
        "total_correct": totals['correct'],
        "by_type": by_type,
    }

