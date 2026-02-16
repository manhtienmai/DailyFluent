import json
import logging
import re
from django.db import transaction
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


def _is_pure_kana(text):
    """Check if text is purely hiragana/katakana (no kanji)."""
    for ch in text:
        if ch in 'ぁ-んァ-ヶー・＜＞':
            continue
        # Unicode ranges: Hiragana 3040-309F, Katakana 30A0-30FF
        cp = ord(ch)
        if (0x3040 <= cp <= 0x309F) or (0x30A0 <= cp <= 0x30FF):
            continue
        # Fullwidth brackets, punctuation, etc - still "kana-like"
        if ch in '＜＞（）「」・ー〜':
            continue
        # If it's a CJK ideograph (kanji), it's NOT pure kana
        if (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF):
            return False
    return True


def generate_and_save_for_set_item(set_item_id, model_name=None, mondai_type=None):
    """
    Generate quiz distractors for a single SetItem and save to DB.
    Returns (result_dict, error_string).
    """
    from vocab.models import SetItem

    try:
        set_item = SetItem.objects.select_related(
            'definition__entry__vocab'
        ).get(pk=set_item_id)
    except SetItem.DoesNotExist:
        return None, f"SetItem {set_item_id} not found"

    vocab = set_item.definition.entry.vocab
    ed = vocab.extra_data or {}
    kanji = vocab.word
    reading = ed.get('reading', '') or kanji  # fallback: word itself
    meaning = set_item.definition.meaning
    is_kana = _is_pure_kana(kanji)

    if is_kana:
        result, error = generate_meaning_only_distractors(kanji, meaning, model_name=model_name)
    else:
        result, error = generate_quiz_distractors(kanji, reading, meaning, model_name=model_name)

    if error:
        return None, error

    saved = _save_quiz_results(set_item, result, mondai_type=mondai_type)
    return saved, None


def generate_and_save_batch(set_item_ids, model_name=None, mondai_type=None):
    """
    Generate quiz distractors for multiple SetItems in one Gemini call.
    Returns (results_dict_by_id, errors_list).
    """
    from vocab.models import SetItem

    set_item_ids = [int(sid) for sid in set_item_ids]

    items = SetItem.objects.filter(
        pk__in=set_item_ids
    ).select_related('definition__entry__vocab')

    items_map = {item.pk: item for item in items}

    # Split words into kanji words (3 quiz types) and kana-only words (meaning only)
    kanji_words = []
    kana_words = []
    for sid in set_item_ids:
        item = items_map.get(sid)
        if not item:
            continue
        vocab = item.definition.entry.vocab
        ed = vocab.extra_data or {}
        word = vocab.word
        reading = ed.get('reading', '') or word
        meaning = item.definition.meaning

        entry = {
            'id': sid,
            'kanji': word,
            'reading': reading,
            'meaning': meaning,
        }
        if _is_pure_kana(word):
            kana_words.append(entry)
        else:
            kanji_words.append(entry)

    if not kanji_words and not kana_words:
        return {}, ["No valid words found in batch"]

    results_by_id = {}
    errors = []

    # Process kanji words (full 3-type generation)
    if kanji_words:
        result, error = generate_batch_distractors(kanji_words, model_name=model_name)
        if error:
            errors.append(error)
        else:
            for wd in kanji_words:
                word_result = result.get(wd['kanji'])
                if not word_result:
                    errors.append(f"No result for {wd['kanji']}")
                    continue
                saved = _save_quiz_results(items_map[wd['id']], word_result, mondai_type=mondai_type)
                results_by_id[wd['id']] = {'word': wd['kanji'], 'questions': saved}

    # Process kana-only words (meaning-only generation)
    if kana_words:
        result, error = generate_batch_meaning_only(kana_words, model_name=model_name)
        if error:
            errors.append(error)
        else:
            for wd in kana_words:
                word_result = result.get(wd['kanji'])
                if not word_result:
                    errors.append(f"No result for {wd['kanji']}")
                    continue
                saved = _save_quiz_results(items_map[wd['id']], word_result, mondai_type=mondai_type)
                results_by_id[wd['id']] = {'word': wd['kanji'], 'questions': saved}

    return results_by_id, errors


def _save_quiz_results(set_item, result, mondai_type=None):
    """Save quiz result dict to QuizQuestion records."""
    from vocab.models import QuizQuestion

    saved = {}
    with transaction.atomic():
        for qtype in ('meaning', 'reading', 'kanji'):
            q_data = result.get(qtype)
            if not q_data:
                continue
            obj, _ = QuizQuestion.objects.update_or_create(
                set_item=set_item,
                question_type=qtype,
                defaults={
                    'correct_answer': q_data.get('correct', ''),
                    'distractors': q_data.get('distractors', []),
                    'mondai_type': mondai_type,
                },
            )
            saved[qtype] = {
                'correct': obj.correct_answer,
                'distractors': obj.distractors,
            }
    return saved


def generate_quiz_distractors(kanji, reading, meaning, model_name=None):
    """
    Generate quiz distractors for a JP word with kanji.
    Returns (data_dict, error_string).
    """
    prompt = f"""You are a JLPT exam question designer. Generate high-quality distractors for a Japanese vocabulary quiz.

Word:
- Kanji: {kanji}
- Reading (Hiragana): {reading}
- Meaning (Vietnamese): {meaning}

Generate exactly 3 plausible but WRONG distractors for each of these 3 question types:

1. **Meaning** (Vietnamese): The correct answer is "{meaning}". Generate 3 Vietnamese meanings that are plausible but wrong. They should be meanings of similar or related Japanese words, NOT random words.

2. **Reading** (Hiragana): The correct answer is "{reading}". Generate 3 hiragana readings that look/sound similar to the correct reading but are wrong. They should be realistic readings that a learner might confuse (e.g., similar kanji readings, common misreadings).

3. **Kanji**: The correct answer is "{kanji}". Generate 3 kanji compounds that look visually similar or share one kanji character with the correct answer, but are different words.

Return ONLY valid JSON in this exact format, no markdown:
{{
  "meaning": {{
    "correct": "{meaning}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }},
  "reading": {{
    "correct": "{reading}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }},
  "kanji": {{
    "correct": "{kanji}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }}
}}"""

    return _call_gemini_and_parse(prompt, model_name)


def generate_meaning_only_distractors(word, meaning, model_name=None):
    """
    Generate meaning-only distractors for a hiragana/katakana word.
    Reading and kanji quiz types are not applicable.
    """
    prompt = f"""You are a JLPT exam question designer. Generate distractors for a Japanese vocabulary quiz.

Word: {word}
Meaning (Vietnamese): {meaning}

This word is written in hiragana/katakana only (no kanji). Generate exactly 3 plausible but WRONG Vietnamese meaning distractors. They should be meanings of similar or related Japanese words, NOT random words.

Return ONLY valid JSON, no markdown:
{{
  "meaning": {{
    "correct": "{meaning}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }}
}}"""

    return _call_gemini_and_parse(prompt, model_name)


def generate_batch_distractors(words, model_name=None):
    """
    Generate quiz distractors for multiple kanji words in one Gemini call.
    Returns (data_dict_keyed_by_kanji, error_string).
    """
    word_lines = []
    for i, w in enumerate(words, 1):
        word_lines.append(f"{i}. Kanji: {w['kanji']} | Reading: {w['reading']} | Meaning: {w['meaning']}")

    words_text = "\n".join(word_lines)
    sample_kanji = words[0]['kanji']

    prompt = f"""You are a JLPT exam question designer. Generate high-quality distractors for a Japanese vocabulary quiz.

Words:
{words_text}

For EACH word above, generate exactly 3 plausible but WRONG distractors for each of these 3 question types:
1. **Meaning** (Vietnamese): Similar Vietnamese meanings of related Japanese words.
2. **Reading** (Hiragana): Similar-looking/sounding hiragana readings.
3. **Kanji**: Visually similar kanji compounds sharing characters.

Return ONLY valid JSON in this exact format (no markdown), keyed by the word:
{{
  "{sample_kanji}": {{
    "meaning": {{ "correct": "...", "distractors": ["w1", "w2", "w3"] }},
    "reading": {{ "correct": "...", "distractors": ["w1", "w2", "w3"] }},
    "kanji": {{ "correct": "...", "distractors": ["w1", "w2", "w3"] }}
  }},
  ...
}}"""

    return _call_gemini_and_parse(prompt, model_name)


def generate_batch_meaning_only(words, model_name=None):
    """
    Generate meaning-only distractors for multiple hiragana/katakana words.
    Returns (data_dict_keyed_by_word, error_string).
    """
    word_lines = []
    for i, w in enumerate(words, 1):
        word_lines.append(f"{i}. {w['kanji']} — {w['meaning']}")

    words_text = "\n".join(word_lines)
    sample = words[0]['kanji']

    prompt = f"""You are a JLPT exam question designer. Generate distractors for a Japanese vocabulary quiz.

These words are hiragana/katakana only (no kanji). For each, generate 3 plausible but WRONG Vietnamese meaning distractors. They should be meanings of similar or related Japanese words.

Words:
{words_text}

Return ONLY valid JSON (no markdown), keyed by the word:
{{
  "{sample}": {{
    "meaning": {{ "correct": "...", "distractors": ["w1", "w2", "w3"] }}
  }},
  ...
}}"""

    return _call_gemini_and_parse(prompt, model_name)


def _call_gemini_and_parse(prompt, model_name=None):
    """Call Gemini and parse JSON response. Returns (data, error)."""
    raw = GeminiService.generate_text(prompt, model_name=model_name)
    if not raw or raw.startswith("Error:"):
        return None, raw or "Unknown error"

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        return None, f"Could not parse JSON from response: {raw[:200]}"

    try:
        data = json.loads(json_match.group())
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}. Raw: {raw[:200]}"
