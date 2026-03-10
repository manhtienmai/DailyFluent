"""
Gemini-powered example sentence generator for Japanese vocabulary.
Generates usage explanations and example sentences with furigana,
Vietnamese and English translations.
"""
import json
import logging
from typing import Optional

from .gemini_service import GeminiService

logger = logging.getLogger(__name__)

EXAMPLE_PROMPT = """Bạn là chuyên gia tiếng Nhật. Cho danh sách từ vựng tiếng Nhật dưới đây, hãy sinh câu ví dụ minh họa cách dùng.

Yêu cầu cho MỖI từ:
1. "usage": Giải thích ngắn gọn cách dùng từ (1-2 câu, bằng tiếng Việt)
2. "examples": Mảng 2-3 câu ví dụ, mỗi câu gồm:
   - "sentence": Câu tiếng Nhật đầy đủ (dùng kanji nếu có)
   - "reading": Cùng câu đó viết bằng hiragana (furigana đầy đủ)
   - "meaning_vi": Dịch tiếng Việt
   - "meaning_en": Dịch tiếng Anh

Quy tắc:
- Câu ví dụ phải tự nhiên, dùng trong giao tiếp hàng ngày
- Câu ví dụ PHẢI chứa từ vựng cần minh họa
- Độ khó câu phù hợp trình độ N3-N2
- Furigana (reading) phải chính xác 100%

Trả về JSON thuần túy, KHÔNG markdown, KHÔNG code block:
{{
  "results": [
    {{
      "word": "từ vựng 1",
      "usage": "cách dùng...",
      "examples": [
        {{
          "sentence": "日本語の文",
          "reading": "にほんごのぶん",
          "meaning_vi": "Dịch tiếng Việt",
          "meaning_en": "English translation"
        }}
      ]
    }}
  ]
}}

Danh sách từ vựng:
{words_json}
"""


def _parse_gemini_response(raw_text):
    """Parse Gemini JSON response, handling markdown code blocks."""
    if not raw_text:
        return None, "Empty response from Gemini"

    text = raw_text.strip()
    # Strip markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
        return data, None
    except json.JSONDecodeError as e:
        logger.error(f"Cannot parse Gemini response: {text[:300]}")
        return None, f"JSON parse error: {e}"


def generate_examples_for_words(words_data: list[dict], model_name: str = None):
    """
    Call Gemini to generate example sentences for a batch of JP words.
    
    Args:
        words_data: List of dicts with keys: word, reading, meaning
        model_name: Optional Gemini model override
    
    Returns:
        (results_dict, error_string)
        results_dict maps word -> {usage, examples: [{sentence, reading, meaning_vi, meaning_en}]}
    """
    if not words_data:
        return {}, None

    words_json = json.dumps(words_data, ensure_ascii=False, indent=2)
    prompt = EXAMPLE_PROMPT.format(words_json=words_json)

    raw = GeminiService.generate_text(prompt, model_name=model_name, caller="example_generator")
    if not raw or raw.startswith("Error:"):
        return None, raw or "No response from Gemini"

    data, error = _parse_gemini_response(raw)
    if error:
        return None, error

    results = {}
    for item in data.get("results", []):
        word = item.get("word", "")
        results[word] = {
            "usage": item.get("usage", ""),
            "examples": item.get("examples", []),
        }

    return results, None


def generate_and_save_for_definition(definition_id: int, model_name: str = None):
    """
    Generate examples for a single WordDefinition and save to DB.
    
    Returns: (saved_count, error_string)
    """
    from vocab.models import WordDefinition, ExampleSentence

    try:
        defn = WordDefinition.objects.select_related(
            'entry__vocab'
        ).get(pk=definition_id)
    except WordDefinition.DoesNotExist:
        return 0, f"WordDefinition {definition_id} not found"

    vocab = defn.entry.vocab
    extra = vocab.extra_data or {}

    word_data = [{
        "word": vocab.word,
        "reading": extra.get("reading", ""),
        "meaning": defn.meaning,
    }]

    results, error = generate_examples_for_words(word_data, model_name=model_name)
    if error:
        return 0, error

    word_result = results.get(vocab.word)
    if not word_result:
        return 0, f"No result for word: {vocab.word}"

    return _save_examples(defn, word_result)


def generate_and_save_batch(definition_ids: list[int], model_name: str = None):
    """
    Generate examples for multiple WordDefinitions in one Gemini call.
    
    Returns: list of (definition_id, saved_count, error_string)
    """
    from vocab.models import WordDefinition

    defns = WordDefinition.objects.select_related(
        'entry__vocab'
    ).filter(pk__in=definition_ids)

    defn_map = {}
    words_data = []
    for defn in defns:
        vocab = defn.entry.vocab
        extra = vocab.extra_data or {}
        word_key = vocab.word
        defn_map[word_key] = defn
        words_data.append({
            "word": word_key,
            "reading": extra.get("reading", ""),
            "meaning": defn.meaning,
        })

    if not words_data:
        return []

    results, error = generate_examples_for_words(words_data, model_name=model_name)
    if error:
        return [(did, 0, error) for did in definition_ids]

    output = []
    for word_key, defn in defn_map.items():
        word_result = results.get(word_key)
        if not word_result:
            output.append((defn.pk, 0, f"No result for: {word_key}"))
            continue

        saved, err = _save_examples(defn, word_result)
        output.append((defn.pk, saved, err))

    return output


def _save_examples(defn, word_result: dict):
    """Save generated examples to DB for a given WordDefinition."""
    from django.db.models import Max as DjMax

    examples = word_result.get("examples", [])
    usage = word_result.get("usage", "")
    saved_count = 0

    # Get current max order
    max_order = defn.examples.aggregate(
        max_order=DjMax('order')
    )['max_order'] or 0

    for i, ex in enumerate(examples):
        sentence = ex.get("sentence", "").strip()
        reading = ex.get("reading", "").strip()
        meaning_vi = ex.get("meaning_vi", "").strip()
        meaning_en = ex.get("meaning_en", "").strip()

        if not sentence:
            continue

        # Build translation: combine VI + EN
        translation_parts = []
        if meaning_vi:
            translation_parts.append(meaning_vi)
        if meaning_en:
            translation_parts.append(f"({meaning_en})")
        translation = " ".join(translation_parts)

        # Build extra data with furigana and individual translations
        extra_data = {}
        if reading:
            extra_data["reading"] = reading
        if meaning_en:
            extra_data["meaning_en"] = meaning_en
        if usage and i == 0:
            extra_data["usage"] = usage

        ExampleSentence.objects.create(
            definition=defn,
            sentence=sentence,
            translation=translation,
            source='gemini',
            order=max_order + i + 1,
        )
        saved_count += 1

    # Save usage to definition extra_data
    if usage:
        extra = defn.extra_data or {}
        extra["usage"] = usage
        # Save reading info for all examples
        example_readings = []
        for ex in examples:
            if ex.get("reading"):
                example_readings.append({
                    "sentence": ex.get("sentence", ""),
                    "reading": ex.get("reading", ""),
                    "meaning_en": ex.get("meaning_en", ""),
                })
        if example_readings:
            extra["gemini_examples"] = example_readings
        defn.extra_data = extra
        defn.save(update_fields=["extra_data"])

    return saved_count, None
