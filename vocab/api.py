"""Vocab API — sets CRUD, courses, flashcards, games, review, progress."""

import random
from ninja import Router, Schema
from typing import List, Optional
from django.db.models import Count, Q, Max

router = Router()


# ── Schemas ────────────────────────────────────────────────

class VocabSetIn(Schema):
    title: str
    description: str = ""
    language: str = "en"


# ── Set CRUD ──────────────────────────────────────────────

@router.get("/sets")
def list_sets(request, language: str = None):
    """List user's vocab sets."""
    from vocab.models import VocabularySet
    qs = VocabularySet.objects.filter(
        owner=request.user
    ).prefetch_related("items")
    if language:
        qs = qs.filter(language=language)
    return [_set_out(s) for s in qs]


@router.post("/sets")
def create_set(request, payload: VocabSetIn):
    """Create a new vocab set."""
    from vocab.models import VocabularySet
    s = VocabularySet.objects.create(
        owner=request.user,
        title=payload.title,
        description=payload.description,
        language=payload.language,
        status="published",
    )
    return _set_out(s)


@router.get("/sets/{set_id}")
def set_detail(request, set_id: int):
    """Get set detail with words."""
    from vocab.models import VocabularySet
    s = VocabularySet.objects.prefetch_related(
        "items__definition__entry__vocab",
        "items__definition__entry",
    ).get(id=set_id)
    words = []
    for item in s.items.all():
        defn = item.definition
        entry = defn.entry
        vocab = entry.vocab
        words.append({
            "item_id": item.id,
            "word": vocab.word,
            "language": vocab.language,
            "part_of_speech": entry.part_of_speech,
            "ipa": entry.ipa,
            "meaning": defn.meaning,
            "example": defn.example_sentence,
            "example_trans": defn.example_trans,
        })
    data = _set_out(s)
    data["words"] = words
    return data


@router.put("/sets/{set_id}")
def update_set(request, set_id: int, payload: VocabSetIn):
    """Update a vocab set."""
    from vocab.models import VocabularySet
    s = VocabularySet.objects.get(id=set_id, owner=request.user)
    s.title = payload.title
    s.description = payload.description
    s.save()
    return {"success": True}


@router.delete("/sets/{set_id}")
def delete_set(request, set_id: int):
    """Delete a vocab set."""
    from vocab.models import VocabularySet
    VocabularySet.objects.filter(id=set_id, owner=request.user).delete()
    return {"success": True}


@router.delete("/sets/{set_id}/items/{item_id}")
def delete_set_item(request, set_id: int, item_id: int):
    """Delete a single item from a vocab set."""
    from vocab.models import SetItem
    deleted, _ = SetItem.objects.filter(
        id=item_id,
        vocabulary_set_id=set_id,
        vocabulary_set__owner=request.user,
    ).delete()
    return {"success": True, "deleted": deleted}


@router.get("/user-sets")
def user_sets_with_items(request):
    """Get all user's vocab sets with items (for my-words page)."""
    from vocab.models import VocabularySet
    sets = VocabularySet.objects.filter(
        owner=request.user
    ).prefetch_related(
        "items__definition__entry__vocab",
        "items__definition__entry",
    ).order_by("-updated_at")

    result = []
    for s in sets:
        words = []
        for item in s.items.all():
            defn = item.definition
            entry = defn.entry
            vocab = entry.vocab
            words.append({
                "item_id": item.id,
                "word": vocab.word,
                "reading": entry.ipa or "",
                "meaning": defn.meaning,
                "language": vocab.language,
            })
        result.append({
            "id": s.id,
            "title": s.title,
            "language": s.language,
            "word_count": len(words),
            "words": words,
        })
    return result


# ── Courses ───────────────────────────────────────────────

@router.get("/courses")
def list_courses(request, language: str = None):
    """List vocab courses (VocabSource collections)."""
    from django.core.cache import cache
    from vocab.models import VocabSource

    cache_key = f"vocab_courses_{language or 'all'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    qs = VocabSource.objects.filter(is_active=True).annotate(
        _set_count=Count("sets", distinct=True),
        _total_words=Count("sets__items", distinct=True),
    )
    if language:
        qs = qs.filter(language=language)
    result = [
        {
            "id": c.id,
            "title": c.name,
            "slug": c.code,
            "description": c.description,
            "language": c.language,
            "source_type": c.source_type,
            "level": c.level,
            "cover_image": c.cover_image.url if c.cover_image else None,
            "set_count": c._set_count,
            "total_words": c._total_words,
        }
        for c in qs
    ]
    cache.set(cache_key, result, 1800)  # 30 min
    return result


@router.get("/courses/{slug}")
def course_detail(request, slug: str):
    """Get course detail with sets."""
    from vocab.models import VocabSource
    c = VocabSource.objects.prefetch_related("sets__items").get(code=slug)
    sets = [
        _set_out(s)
        for s in c.sets.filter(status="published").order_by("set_number")
    ]
    return {
        "id": c.id,
        "title": c.name,
        "slug": c.code,
        "description": c.description,
        "language": c.language,
        "cover_image": c.cover_image.url if c.cover_image else None,
        "sets": sets,
    }


@router.get("/courses/{slug}/set/{set_num}/learn")
def learn_set(request, slug: str, set_num: int):
    """Get words to learn from a course set."""
    from vocab.models import VocabSource, VocabularySet
    source = VocabSource.objects.get(code=slug)
    vs = VocabularySet.objects.prefetch_related(
        "items__definition__entry__vocab",
        "items__definition__examples",
    ).get(collection=source, set_number=set_num)
    words = _get_set_words(vs)
    return {"set": _set_out(vs), "words": words}


@router.get("/courses/{slug}/set/{set_num}/quiz")
def quiz_set(request, slug: str, set_num: int):
    """Get quiz questions for a course set — generated dynamically."""
    import random
    from vocab.models import VocabSource, VocabularySet

    source = VocabSource.objects.get(code=slug)
    vs = VocabularySet.objects.prefetch_related(
        "items__definition__entry__vocab",
    ).get(collection=source, set_number=set_num)

    # Collect all words with meanings
    word_list = []
    for item in vs.items.all():
        defn = item.definition
        entry = defn.entry
        vocab = entry.vocab
        word_list.append({
            "id": item.id,
            "word": vocab.word,
            "reading": entry.ipa or "",
            "meaning": defn.meaning,
        })

    if not word_list:
        return {"set": _set_out(vs), "questions": []}

    # Build MCQ: pick correct meaning + 3 distractors from same set
    all_meanings = [w["meaning"] for w in word_list]
    questions = []
    for w in word_list:
        correct = w["meaning"]
        # Pick 3 other meanings as distractors
        other_meanings = [m for m in all_meanings if m != correct]
        if len(other_meanings) >= 3:
            distractors = random.sample(other_meanings, 3)
        else:
            distractors = other_meanings[:]
        choices = distractors + [correct]
        random.shuffle(choices)
        questions.append({
            "id": w["id"],
            "word": w["word"],
            "reading": w["reading"],
            "choices": choices,
            "correct_answer": correct,
        })

    random.shuffle(questions)
    return {"set": _set_out(vs), "questions": questions}


# ── Flashcards & Review ───────────────────────────────────

@router.get("/flashcards")
def flashcard_review(request, language: str = "en"):
    """Get flashcard review queue using FsrsService (FSRS-5)."""
    from vocab.services import FsrsService

    cards, stats = FsrsService.get_flashcard_session(
        user=request.user,
        language=language,
    )
    return {"cards": cards, "stats": stats}





@router.get("/review")
def review_due(request, language: str = "en"):
    """Get count of cards due for review."""
    from vocab.models import FsrsCardStateEn
    from django.utils import timezone

    count = FsrsCardStateEn.objects.filter(
        user=request.user,
        due__lte=timezone.now(),
    ).count()
    return {"due_count": count}


# ── Progress & Stats ──────────────────────────────────────

@router.get("/progress")
def progress(request, language: str = "en"):
    """Get overall vocab progress."""
    from vocab.models import FsrsCardStateEn
    from django.utils import timezone

    stats = FsrsCardStateEn.objects.filter(user=request.user).aggregate(
        total=Count("id"),
        mastered=Count("id", filter=Q(total_reviews__gte=3, successful_reviews__gte=2)),
        review_due=Count("id", filter=Q(due__lte=timezone.now())),
    )

    return {
        "total_words": stats["total"],
        "learned": stats["total"],
        "mastered": stats["mastered"],
        "review_due": stats["review_due"],
    }


@router.get("/study-status")
def study_status(request):
    """Get daily study status."""
    from vocab.models import UserStudySettings
    settings, _ = UserStudySettings.objects.get_or_create(user=request.user)
    settings.reset_daily_counts_if_needed()
    return {
        "new_cards_per_day": settings.new_cards_per_day,
        "reviews_per_day": settings.reviews_per_day,
        "new_cards_today": settings.new_cards_today,
        "reviews_today": settings.reviews_today,
        "can_study_new": settings.new_cards_today < settings.new_cards_per_day,
        "can_review": settings.reviews_today < settings.reviews_per_day,
    }


# ── Word Detail & Search ─────────────────────────────────

@router.get("/english/{word}")
def word_detail(request, word: str):
    """Get word detail (all entries and definitions)."""
    from vocab.models import Vocabulary
    try:
        v = Vocabulary.objects.prefetch_related(
            "entries__definitions__examples"
        ).get(word__iexact=word, language="en")
    except Vocabulary.DoesNotExist:
        return {"error": "Word not found", "word": word}

    entries = []
    for entry in v.entries.all():
        defs = []
        for d in entry.definitions.all():
            examples = [
                {"sentence": e.sentence, "translation": e.translation, "source": e.source}
                for e in d.examples.all()[:3]
            ]
            defs.append({
                "id": d.id,
                "meaning": d.meaning,
                "examples": examples,
            })
        entries.append({
            "id": entry.id,
            "part_of_speech": entry.part_of_speech,
            "ipa": entry.ipa,
            "audio_us": entry.audio_us,
            "audio_uk": entry.audio_uk,
            "definitions": defs,
        })
    return {
        "id": v.id,
        "word": v.word,
        "language": v.language,
        "extra_data": v.extra_data,
        "entries": entries,
    }


@router.get("/my-words")
def my_words(request, language: str = "en", filter: str = "all"):
    """Get user's learned words."""
    from vocab.models import FsrsCardStateEn
    qs = FsrsCardStateEn.objects.filter(
        user=request.user
    ).select_related("vocab")

    # Filter by state: 0=New, 1=Learning, 2=Review, 3=Relearning
    if filter == "new":
        qs = qs.filter(state=0)
    elif filter == "learning":
        qs = qs.filter(state__in=[1, 3])
    elif filter == "review":
        qs = qs.filter(state=2)
    elif filter == "mastered":
        qs = qs.filter(total_reviews__gte=3, successful_reviews__gte=2)

    cards = qs.order_by("-last_review")[:100]
    return [
        {
            "id": c.id,
            "word": c.vocab.word,
            "state": c.state,
            "total_reviews": c.total_reviews,
            "last_review": c.last_review.isoformat() if c.last_review else None,
            "due": c.due.isoformat() if c.due else None,
        }
        for c in cards
    ]


# ── Typing & Phrases ─────────────────────────────────────

@router.get("/typing")
def typing_practice(request):
    """Get words for typing practice."""
    from vocab.models import FsrsCardStateEn
    qs = FsrsCardStateEn.objects.filter(user=request.user)
    total = qs.count()
    if total == 0:
        return []
    # Random selection via IDs instead of ORDER BY RANDOM()
    all_ids = list(qs.values_list("id", flat=True))
    sample_ids = random.sample(all_ids, min(10, len(all_ids)))
    cards = qs.filter(id__in=sample_ids).select_related("vocab")
    return [
        {"id": c.vocab.id, "word": c.vocab.word}
        for c in cards
    ]


@router.get("/phrases")
def phrases(request, language: str = "en"):
    """Get common phrases."""
    from vocab.models import VocabularySet
    phrase_sets = VocabularySet.objects.filter(
        title__contains="phrase",
        status="published",
    ).prefetch_related("items__definition__entry__vocab")[:5]

    results = []
    for s in phrase_sets:
        for item in s.items.all()[:20]:
            results.append({
                "word": item.definition.entry.vocab.word,
                "meaning": item.definition.meaning,
            })
    return results


# ── Games ─────────────────────────────────────────────────

@router.get("/games")
def list_games(request):
    """List available vocab games."""
    return [
        {"slug": "matching", "title": "Nối từ", "description": "Nối từ với nghĩa", "icon": "🔗"},
        {"slug": "fill-blank", "title": "Điền từ", "description": "Điền từ vào chỗ trống", "icon": "✍️"},
        {"slug": "speed-quiz", "title": "Trắc nghiệm nhanh", "description": "Chọn đáp án đúng", "icon": "⚡"},
    ]


@router.get("/games/{slug}")
def game_data(request, slug: str):
    """Get game data (words to play with)."""
    from vocab.models import FsrsCardStateEn
    qs = FsrsCardStateEn.objects.filter(user=request.user)
    all_ids = list(qs.values_list("id", flat=True))
    if not all_ids:
        return {"game": slug, "words": []}
    sample_ids = random.sample(all_ids, min(20, len(all_ids)))
    cards = qs.filter(id__in=sample_ids).select_related("vocab")
    words = [
        {"id": c.vocab.id, "word": c.vocab.word}
        for c in cards
    ]
    return {"game": slug, "words": words}


# ── Highlight / Save Word ────────────────────────────────

class SaveHighlightIn(Schema):
    word: str
    context_sentence: str = ""
    meaning_vi: str = ""
    reading: str = ""
    han_viet: str = ""
    source: str = "highlight"
    language: str = "jp"


@router.post("/save-highlight")
def save_highlight(request, payload: SaveHighlightIn):
    """Save a highlighted word to user's personal set + FSRS card."""
    from vocab.vocab_service import VocabWordService

    return VocabWordService.save_or_create_word(
        user=request.user,
        word=payload.word,
        language=payload.language,
        reading=payload.reading,
        meaning_vi=payload.meaning_vi,
        han_viet=payload.han_viet,
        context_sentence=payload.context_sentence,
    )


class ExplainContextIn(Schema):
    word: str
    context_sentence: str
    language: str = "jp"


@router.post("/explain-in-context")
def explain_in_context(request, payload: ExplainContextIn):
    """Use Gemini to explain a word in its sentence context if not found in DB."""
    from vocab.services.gemini_service import GeminiService
    import json
    from vocab.models import Vocabulary

    word = payload.word.strip()
    sentence = payload.context_sentence.strip()

    if not word:
        return {"error": "Word is empty"}

    # Helper to build response from a Vocabulary object
    def _vocab_response(v):
        for entry in v.entries.all():
            for defn in entry.definitions.all():
                return {
                    "word": v.word,
                    "reading": entry.ipa or "",
                    "han_viet": v.extra_data.get("han_viet", "") if v.extra_data else "",
                    "meaning_vi": defn.meaning,
                    "jlpt_level": v.extra_data.get("jlpt_level", "") if v.extra_data else "",
                    "english_origin": v.extra_data.get("english_origin", "") if v.extra_data else "",
                    "collocation": v.extra_data.get("collocation", "") if v.extra_data else "",
                    "synonyms": v.extra_data.get("synonyms", []) if v.extra_data else [],
                    "antonyms": v.extra_data.get("antonyms", []) if v.extra_data else [],
                    "source": "db",
                }
        return None

    # Step 1: Exact match
    try:
        v = Vocabulary.objects.prefetch_related(
            "entries__definitions"
        ).get(word=word, language=payload.language)
        result = _vocab_response(v)
        if result:
            return result
    except Vocabulary.DoesNotExist:
        pass

    # Step 2: Stem match for conjugated Japanese verbs/adjectives
    # Try stripping common endings to find the dictionary form in DB
    if payload.language == "jp" and len(word) >= 2:
        suffixes = [
            'ていました', 'ています', 'ていた', 'ている', 'てある',
            'られた', 'られる', 'させた', 'させる', 'ました',
            'ません', 'ないで', 'なかった',
            'いた', 'った', 'んだ', 'した', 'いて', 'って', 'んで', 'して',
            'れる', 'てる', 'てた', 'よう', 'たい', 'ない',
            'ます', 'た', 'て', 'く', 'い',
        ]
        stems = set()
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix):
                stems.add(word[:-len(suffix)])

        # Limit stems to avoid excessive OR conditions
        stems = set(list(stems)[:5])

        if stems:
            try:
                q = Q()
                for s in stems:
                    if len(s) >= 1:
                        q |= Q(word__startswith=s)
                matches = Vocabulary.objects.prefetch_related(
                    "entries__definitions"
                ).filter(q, language="jp").order_by("-id")[:10]

                # Pick best match: longest stored word whose stem matches
                best = None
                for v in matches:
                    if abs(len(v.word) - len(word)) <= 3:
                        if best is None or len(v.word) > len(best.word):
                            best = v
                if best:
                    result = _vocab_response(best)
                    if result:
                        return result
            except Exception:
                pass

    # Fallback: AI explanation
    prompt = f"""Từ/cụm từ: "{word}"
Câu: "{sentence}"

QUAN TRỌNG: Nếu từ "{word}" là động từ đã chia (ví dụ: thể た, thể て, thể bị động, thể sai khiến, thể ます...), hãy trả về **thể từ điển (辞書形)** trong trường "word_dict".
- Ví dụ: "言われた" → word_dict: "言う"
- Ví dụ: "食べている" → word_dict: "食べる"
- Ví dụ: "勘違い" → word_dict: "勘違い" (danh từ giữ nguyên)

Trả về CHỈ JSON (KHÔNG markdown, KHÔNG text thừa):
{{
  "word_dict": "thể từ điển / dạng gốc của từ (辞書形)",
  "reading": "cách đọc hiragana của word_dict",
  "han_viet": "Hán Việt (nếu có kanji, nếu không để trống)",
  "meaning_vi": "nghĩa tiếng Việt ngắn gọn, dễ hiểu",
  "jlpt_level": "mức JLPT (N5/N4/N3/N2/N1), ví dụ N2. Nếu không chắc để trống",
  "english_origin": "Nếu là từ mượn tiếng Anh (外来語/katakana), trả về từ tiếng Anh gốc. VD: リハビリ→rehabilitation. Nếu không phải từ mượn thì để trống",
  "collocation": "Các cụm từ / collocation phổ biến với từ này, ngăn cách bởi dấu phẩy. VD: '出来事が起きる, 大きな出来事'. Nếu không có để trống",
  "synonyms": [
    {{"word": "từ đồng nghĩa", "reading": "furigana nếu từ có kanji khó (xem quy tắc bên dưới)", "meaning": "nghĩa Việt ngắn"}}
  ],
  "antonyms": [
    {{"word": "từ trái nghĩa", "reading": "furigana (quy tắc như trên)", "meaning": "nghĩa Việt ngắn"}}
  ]
}}

Lưu ý về synonyms/antonyms:
- Trả về 3-5 từ thông dụng nhất
- Quy tắc furigana (reading) cho synonyms/antonyms:
  + Ghi furigana nếu từ đồng/trái nghĩa có kanji ở mức JLPT NGANG hoặc KHÓ HƠN từ đang tra.
  + Ví dụ: Nếu từ đang tra là N3, thì từ đồng nghĩa N3/N2/N1 cần furigana, còn N4/N5 không cần.
  + Ví dụ: Nếu từ đang tra là N2, thì từ đồng nghĩa N2/N1 cần furigana, còn N3/N4/N5 không cần.
  + Nói cách khác: chỉ BỎ furigana khi từ đồng/trái nghĩa DỄ HƠN RÕ RÀNG so với từ đang tra.
- Nếu không có từ đồng/trái nghĩa phù hợp, trả về mảng rỗng []
"""

    try:
        result = GeminiService.generate_text(prompt, model_name="gemini-2.5-flash")
        if result:
            # Clean markdown fences if present
            text = result.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                elif "```" in text:
                    text = text.split("```")[0]
            
            # Find JSON block if there's text around it
            if "{" in text and "}" in text:
                text = text[text.find("{"):text.rfind("}")+1]
                
            data = json.loads(text.strip())
            dict_word = data.get("word_dict", word)
            reading = data.get("reading", "")
            han_viet = data.get("han_viet", "")
            meaning_vi = data.get("meaning_vi", "")
            jlpt_level = data.get("jlpt_level", "")
            english_origin = data.get("english_origin", "")
            collocation = data.get("collocation", "")
            synonyms = data.get("synonyms", [])
            antonyms = data.get("antonyms", [])

            # Auto-save to DB for future lookups
            try:
                from vocab.models import Vocabulary, WordEntry, WordDefinition
                save_word = dict_word or word
                extra = {}
                if reading:
                    extra["reading"] = reading
                if han_viet:
                    extra["han_viet"] = han_viet
                if jlpt_level:
                    extra["jlpt_level"] = jlpt_level
                if english_origin:
                    extra["english_origin"] = english_origin
                if collocation:
                    extra["collocation"] = collocation
                if synonyms:
                    extra["synonyms"] = synonyms
                if antonyms:
                    extra["antonyms"] = antonyms

                v, _ = Vocabulary.objects.get_or_create(
                    word=save_word,
                    language=payload.language,
                    defaults={"extra_data": extra},
                )
                # Update extra_data if vocab existed but was missing fields
                if not v.extra_data:
                    v.extra_data = extra
                    v.save(update_fields=["extra_data"])
                elif extra:
                    changed = False
                    for k, val in extra.items():
                        if k not in v.extra_data or not v.extra_data[k]:
                            v.extra_data[k] = val
                            changed = True
                    if changed:
                        v.save(update_fields=["extra_data"])

                entry, _ = WordEntry.objects.get_or_create(
                    vocab=v,
                    defaults={"ipa": reading},
                )
                if not entry.ipa and reading:
                    entry.ipa = reading
                    entry.save(update_fields=["ipa"])

                WordDefinition.objects.get_or_create(
                    entry=entry,
                    meaning=meaning_vi,
                )
            except Exception as save_err:
                import traceback
                print(f"[Auto-save] Failed to save '{dict_word or word}' to DB: {save_err}")
                traceback.print_exc()

            return {
                "word": dict_word or word,
                "reading": reading,
                "han_viet": han_viet,
                "meaning_vi": meaning_vi,
                "jlpt_level": jlpt_level,
                "english_origin": english_origin,
                "collocation": collocation,
                "synonyms": synonyms,
                "antonyms": antonyms,
                "source": "ai",
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"AI failed: {str(e)}", "word": word, "source": "error"}

    return {"error": "No result", "word": word, "source": "error"}


# ── Helpers ───────────────────────────────────────────────

def _set_out(s):
    # Use annotated _word_count if available, else use len() on prefetched, else query
    if hasattr(s, '_word_count'):
        wc = s._word_count
    elif 'items' in getattr(s, '_prefetched_objects_cache', {}):
        wc = len(s.items.all())
    else:
        wc = s.items.count()
    # Use select_related collection if available
    course_title = None
    try:
        course_title = s.collection.name if s.collection_id else None
    except Exception:
        pass
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "word_count": wc,
        "status": s.status,
        "language": s.language,
        "toeic_level": s.toeic_level,
        "set_number": s.set_number,
        "chapter": s.chapter,
        "chapter_name": s.chapter_name,
        "course_title": course_title,
    }


def _get_set_words(vs):
    """Get all words with examples for a set."""
    words = []
    for item in vs.items.all():
        defn = item.definition
        entry = defn.entry
        vocab = entry.vocab
        examples = [
            {"sentence": e.sentence, "translation": e.translation}
            for e in defn.examples.all()[:3]
        ]
        words.append({
            "item_id": item.id,
            "word": vocab.word,
            "language": vocab.language,
            "part_of_speech": entry.part_of_speech,
            "ipa": entry.ipa,
            "audio_us": entry.audio_us,
            "audio_uk": entry.audio_uk,
            "meaning": defn.meaning,
            "examples": examples,
        })
    return words
