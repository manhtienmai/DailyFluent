"""
Grammar Content Pipeline — auto-create GrammarPoint records from ExamQuestion data.

Called after quiz import to keep GrammarPoint table in sync.
Standard content pipeline pattern: content creation → canonical records → user progress lazily.
"""
import re
import logging
from django.utils.text import slugify

logger = logging.getLogger(__name__)

# ── Hiragana → Romaji mapping for SEO-friendly slugs ──────────

_HIRA_MAP = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'っ': 't', 'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'ー': '-',
}


def _hira_to_romaji(text: str) -> str:
    """Convert hiragana text to romaji for slug generation."""
    result = []
    i = 0
    while i < len(text):
        ch = text[i]
        if i + 1 < len(text) and text[i + 1] in ('ゃ', 'ゅ', 'ょ'):
            base = _HIRA_MAP.get(ch, ch)
            small = _HIRA_MAP.get(text[i + 1], text[i + 1])
            result.append(base[:-1] + small if base.endswith('i') else base + small)
            i += 2
            continue
        if ch in _HIRA_MAP:
            result.append(_HIRA_MAP[ch])
        elif ch in ('\uff0f', '/'):
            result.append('-')
        elif ch in ('\uff08', '\uff09', '(', ')'):
            pass
        elif ch in (' ', '\u3000'):
            result.append('-')
        elif ch.isascii() and ch.isalnum():
            result.append(ch)
        elif ch == '-':
            result.append('-')
        i += 1
    return re.sub(r'-+', '-', ''.join(result)).strip('-').lower()


def _make_grammar_slug(title: str, reading: str) -> str:
    """Generate an SEO-friendly slug from reading (romaji) or title."""
    # 1. Try slugify on reading if it has ASCII chars
    if reading:
        slug = slugify(reading.strip())
        if slug and len(slug) > 2:
            return slug
        # 2. Try hiragana to romaji conversion
        romaji = _hira_to_romaji(reading.strip())
        if romaji and len(romaji) > 1:
            return romaji

    # 3. Fallback: try title
    cleaned = re.sub(r'^[\uff5e\u301c]+', '', title).strip()
    slug = slugify(cleaned)
    if slug and len(slug) > 2:
        return slug

    # 4. Last resort: hash-based
    return f"gp-{abs(hash(title)) % 100000}"


def sync_grammar_points_from_questions(template_ids=None):
    """
    Create GrammarPoint records from bunpou quiz ExamQuestion.explanation_json.

    Args:
        template_ids: list of ExamTemplate IDs to sync. If None, syncs ALL bunpou templates.

    Returns:
        dict with 'created' and 'total' counts.
    """
    from exam.models import ExamTemplate, ExamQuestion
    from grammar.models import GrammarPoint

    # 1. Get relevant templates
    if template_ids:
        t_ids = list(template_ids) if not isinstance(template_ids, list) else template_ids
    else:
        t_ids = list(
            ExamTemplate.objects.filter(is_active=True, category="BUN")
            .values_list("id", flat=True)
        )

    if not t_ids:
        return {"created": 0, "total": 0}

    # 2. Extract unique grammar points from questions
    gp_data = {}
    for q in ExamQuestion.objects.filter(template_id__in=t_ids).select_related("template"):
        ej = q.explanation_json or {}
        gp = ej.get("grammar_point", "").strip()
        if not gp or gp in gp_data:
            continue
        gp_data[gp] = {
            "structure": ej.get("grammar_structure", ""),
            "meaning": ej.get("grammar_meaning", ""),
            "furigana": ej.get("grammar_furigana", ""),
            "reading": ej.get("grammar_reading", ""),
            "note": ej.get("grammar_note", ""),
            "topic": ej.get("grammar_topic", ""),
            "level": q.template.level or "N3",
            "examples": ej.get("examples", []) or ej.get("grammar_examples", []),
        }

    if not gp_data:
        return {"created": 0, "total": 0}

    # 3. Find existing and create missing
    existing_titles = set(
        GrammarPoint.objects.filter(title__in=gp_data.keys())
        .values_list("title", flat=True)
    )
    existing_slugs = set(GrammarPoint.objects.values_list("slug", flat=True))

    new_gps = []
    for title, data in gp_data.items():
        if title not in existing_titles:
            # Build examples text
            examples_text = ""
            for ex in data.get("examples", []):
                if isinstance(ex, dict):
                    ja = ex.get("ja", "")
                    vi = ex.get("vi", "")
                    if ja:
                        examples_text += f"{ja}\n{vi}\n\n" if vi else f"{ja}\n"
                elif isinstance(ex, str):
                    examples_text += f"{ex}\n"

            reading = data.get("reading") or data.get("furigana", "")
            slug = _make_grammar_slug(title, reading)

            # Ensure unique slug
            base_slug = slug
            counter = 1
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            existing_slugs.add(slug)

            new_gps.append(GrammarPoint(
                title=title,
                slug=slug,
                level=data["level"],
                reading=reading,
                meaning_vi=data["meaning"],
                formation=data["structure"],
                notes=data.get("note", ""),
                summary=data.get("topic", ""),
                examples=examples_text.strip(),
                is_active=True,
            ))

    if new_gps:
        GrammarPoint.objects.bulk_create(new_gps, ignore_conflicts=True)
        logger.info(f"Created {len(new_gps)} GrammarPoint records from quiz data")

    return {
        "created": len(new_gps),
        "total": len(gp_data),
        "already_existed": len(existing_titles),
    }
