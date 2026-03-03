"""
Exam Utilities — shared helper functions for the exam app.

DRY: Centralizes helpers that were duplicated across api.py and views.py.
"""

import re


def ruby_to_html(text: str) -> str:
    """
    Convert furigana markup to <ruby> HTML — single source of truth.

    Supports two formats:
      Format 1 (analyze API): {漢字}(かな)  →  <ruby>漢字<rt>かな</rt></ruby>
      Format 2 (translate API): 漢字{かな}  →  <ruby>漢字<rt>かな</rt></ruby>

    Previously duplicated in:
      - exam/api.py → choukai_mondai._ruby()
      - exam/api.py → dokkai_detail._ruby_api()
      - exam/views.py → _ruby()
    """
    if not text:
        return ''
    # Format 1: {漢字}(かな)
    text = re.sub(
        r'\{([^}]+)\}\(([^)]+)\)',
        r'<ruby>\1<rt>\2</rt></ruby>',
        text,
    )
    # Format 2: 漢字{かな} — base is kanji + digits; reading in {} is hiragana/katakana
    text = re.sub(
        r'([\u4e00-\u9fff\u3400-\u4dbf\uff10-\uff190-9]+)'
        r'\{([\u3040-\u309f\u30a0-\u30ff]+)\}',
        r'<ruby>\1<rt>\2</rt></ruby>',
        text,
    )
    return text


def audio_url(question) -> str:
    """
    Build audio URL for an ExamQuestion.
    Handles the case where DB stores a full URL (from import scripts).

    Previously duplicated in:
      - exam/api.py → choukai_mondai._audio_url()
      - exam/views.py → _audio_url()
    """
    if not question.audio:
        return ''
    name = question.audio.name or ''
    if name.startswith('http'):
        return name
    return question.audio.url
