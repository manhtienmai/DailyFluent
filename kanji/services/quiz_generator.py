"""
Kanji Quiz Generator — uses Gemini to create distractors for kanji recognition quizzes.

Follows the same pattern as vocab/services/quiz_generator.py.
"""

import json
import logging
import re

from django.db import transaction

logger = logging.getLogger(__name__)


def generate_and_save_for_kanji(kanji_id, model_name=None):
    """
    Generate quiz distractors for a single Kanji and save to DB.
    Returns (result_dict, error_string).
    """
    from kanji.models import Kanji

    try:
        kanji = Kanji.objects.get(pk=kanji_id)
    except Kanji.DoesNotExist:
        return None, f"Kanji {kanji_id} not found"

    result, error = _generate_kanji_distractors(kanji, model_name=model_name)
    if error:
        return None, error

    saved = _save_quiz_results(kanji, result)
    return saved, None


def generate_batch_for_lesson(lesson_id, model_name=None):
    """
    Generate quiz distractors for all kanji in a lesson (batch).
    Returns (results_by_kanji_id, errors_list).
    """
    from kanji.models import KanjiLesson

    try:
        lesson = KanjiLesson.objects.prefetch_related('kanjis').get(pk=lesson_id)
    except KanjiLesson.DoesNotExist:
        return {}, [f"Lesson {lesson_id} not found"]

    kanji_list = list(lesson.kanjis.all())
    if not kanji_list:
        return {}, ["No kanji in this lesson"]

    results_by_id = {}
    errors = []

    # Process one by one to avoid overly large prompts
    for kanji in kanji_list:
        result, error = _generate_kanji_distractors(kanji, model_name=model_name)
        if error:
            errors.append(f"{kanji.char}: {error}")
            continue
        saved = _save_quiz_results(kanji, result)
        results_by_id[kanji.id] = {'char': kanji.char, 'questions': saved}

    return results_by_id, errors


def _generate_kanji_distractors(kanji, model_name=None):
    """
    Generate quiz distractors for a single Kanji character.
    Returns (data_dict, error_string).
    """
    from vocab.services.gemini_service import GeminiService

    char = kanji.char
    sino_vi = kanji.sino_vi or ''
    meaning_vi = kanji.meaning_vi or sino_vi or '?'
    onyomi = kanji.onyomi or ''
    kunyomi = kanji.kunyomi or ''
    reading = onyomi or kunyomi or '?'

    prompt = f"""You are a JLPT kanji quiz designer. Generate high-quality distractors for a kanji recognition quiz.

Kanji character: {char}
Sino-Vietnamese (Hán Việt): {sino_vi}
Meaning (Vietnamese): {meaning_vi}
Onyomi: {onyomi}
Kunyomi: {kunyomi}

Generate exactly 3 plausible but WRONG distractors for each of these 3 question types:

1. **Meaning** (Vietnamese): The correct answer is "{meaning_vi}". Generate 3 Vietnamese meanings that are plausible but wrong. They should be meanings of visually similar kanji or kanji with similar radicals, NOT random words.

2. **Reading** (Hiragana/Katakana): The correct answer reading is "{reading}". Generate 3 readings that look/sound similar to the correct reading but are wrong. They should be realistic readings of similar-looking kanji that a learner might confuse.

3. **Kanji**: The correct answer is "{char}". Generate 3 kanji characters that look visually similar (share radicals, similar stroke count, or commonly confused) but are different characters. Each distractor should be a single kanji character.

Return ONLY valid JSON in this exact format, no markdown:
{{
  "meaning": {{
    "correct": "{meaning_vi}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }},
  "reading": {{
    "correct": "{reading}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }},
  "kanji": {{
    "correct": "{char}",
    "distractors": ["wrong1", "wrong2", "wrong3"]
  }}
}}"""

    return _call_gemini_and_parse(prompt, model_name)


def _save_quiz_results(kanji, result):
    """Save quiz result dict to KanjiQuizQuestion records."""
    from kanji.models import KanjiQuizQuestion

    saved = {}
    with transaction.atomic():
        for qtype in ('meaning', 'reading', 'kanji'):
            q_data = result.get(qtype)
            if not q_data:
                continue
            obj, _ = KanjiQuizQuestion.objects.update_or_create(
                kanji=kanji,
                question_type=qtype,
                defaults={
                    'correct_answer': q_data.get('correct', ''),
                    'distractors': q_data.get('distractors', []),
                },
            )
            saved[qtype] = {
                'correct': obj.correct_answer,
                'distractors': obj.distractors,
            }
    return saved


def _call_gemini_and_parse(prompt, model_name=None):
    """Call Gemini and parse JSON response. Returns (data, error)."""
    from vocab.services.gemini_service import GeminiService

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
