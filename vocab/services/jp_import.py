"""
Shared import logic for Japanese vocabulary (Mimikara N2 format).

JSON item structure (actual data):
{
    "id": "vocab_1",
    "original_number": 1,
    "metadata": {"lesson": "...", "audio": "https://..."},
    "word_info": {"kanji": "人生", "reading": "じんせい", "html_display": "<ruby>..."},
    "meanings": {"han_viet": "nhân sinh", "vietnamese": "cuộc sống, cuộc đời"},
    "part_of_speech": "noun",       ← optional, fallback to default_pos
    "examples": [
        {"id": 1, "type": "sentence", "label": "", "jp_html": "...", "jp_text": "...", "vn_text": "..."},
        {"id": 3, "type": "compound", "label": "合", "jp_html": "...", "jp_text": "...", "vn_text": "..."},
        {"id": 4, "type": "synonym",  "label": "類", ...},
        {"id": 5, "type": "collocation", "label": "連", ...},
    ]
}

Mapping:
    original_number         → Vocabulary.extra_data["order"]
    id                      → Vocabulary.extra_data["source_id"]
    metadata.audio          → Vocabulary.extra_data["audio"]
    metadata.lesson         → Vocabulary.extra_data["lesson"]
    word_info.kanji         → Vocabulary.word
    word_info.reading       → Vocabulary.extra_data["reading"]
    word_info.html_display  → Vocabulary.extra_data["html_display"]
    meanings.han_viet       → Vocabulary.extra_data["han_viet"]
    meanings.vietnamese     → WordDefinition.meaning
    part_of_speech          → WordEntry.part_of_speech (or default_pos)
    examples[type=sentence] → ExampleSentence (sentence=jp_html, translation=vn_text)
    examples[type!=sentence]→ WordDefinition.extra_data["relations"]
"""
import logging
import re
from collections import defaultdict
from django.db import transaction

from vocab.models import (
    Vocabulary, WordEntry, WordDefinition, ExampleSentence,
    VocabularySet, SetItem, SetItemExample,
)

logger = logging.getLogger(__name__)


def import_jp_vocab_data(items, vocab_set=None, source='mimikara_n2', default_pos='noun'):
    """
    Import Japanese vocabulary from structured JSON data.

    Args:
        items: list of dicts in Mimikara format
        vocab_set: optional VocabularySet to add words to
        source: ExampleSentence.source value
        default_pos: default part_of_speech

    Returns:
        dict with counts: created_vocabs, created_definitions, created_examples, skipped
    """
    stats = {
        'created_vocabs': 0,
        'created_definitions': 0,
        'created_examples': 0,
        'skipped': 0,
    }

    with transaction.atomic():
        for idx, item in enumerate(items):
            try:
                _import_single_item(item, vocab_set, source, default_pos, idx, stats)
            except Exception as e:
                logger.warning("Skipping item %d: %s", idx, e)
                stats['skipped'] += 1

    return stats


def _import_single_item(item, vocab_set, source, default_pos, item_idx, stats):
    """Import a single vocabulary item."""
    # --- Extract fields ---
    word_info = item.get('word_info', {})
    meanings = item.get('meanings', {})
    metadata = item.get('metadata', {})
    examples = item.get('examples', [])

    kanji = word_info.get('kanji', '').strip()
    if not kanji:
        stats['skipped'] += 1
        return

    reading = word_info.get('reading', '')
    html_display = word_info.get('html_display', '')
    han_viet = meanings.get('han_viet', '')
    vietnamese = meanings.get('vietnamese', '')
    lesson = metadata.get('lesson', '')
    audio = metadata.get('audio', '')
    source_id = item.get('id', '')
    # Use original_number from data if available, otherwise fall back to array index
    order = item.get('original_number', item_idx)
    pos = item.get('part_of_speech', default_pos) or default_pos

    # --- 1. Vocabulary ---
    extra_data = {'order': order}
    if source_id:
        extra_data['source_id'] = source_id
    if reading:
        extra_data['reading'] = reading
    if html_display:
        extra_data['html_display'] = html_display
    if han_viet:
        extra_data['han_viet'] = han_viet
    if lesson:
        extra_data['lesson'] = lesson
    if audio:
        extra_data['audio'] = audio

    vocab, created = Vocabulary.objects.get_or_create(
        word=kanji,
        defaults={
            'language': Vocabulary.Language.JAPANESE,
            'extra_data': extra_data,
        }
    )
    if created:
        stats['created_vocabs'] += 1
    else:
        # Merge extra_data for existing vocab
        changed = False
        for key, val in extra_data.items():
            # Allow overwriting/updating values
            if vocab.extra_data.get(key) != val:
                vocab.extra_data[key] = val
                changed = True
        if changed:
            vocab.save(update_fields=['extra_data'])

    # --- 2. WordEntry ---
    entry, _ = WordEntry.objects.get_or_create(
        vocab=vocab,
        part_of_speech=pos,
    )

    # --- 3. Separate examples ---
    sentence_examples = []
    relation_examples = []
    for ex in examples:
        if ex.get('type') == 'sentence':
            sentence_examples.append(ex)
        else:
            relation_examples.append({
                'type': ex.get('type', ''),
                'label': ex.get('label', ''),
                'jp_html': ex.get('jp_html', ''),
                'jp_text': ex.get('jp_text', ''),
                'vn_text': ex.get('vn_text', ''),
            })

    # --- 4. WordDefinition ---
    if not vietnamese:
        stats['skipped'] += 1
        return

    def_extra = {}
    if relation_examples:
        def_extra['relations'] = relation_examples

    defn, def_created = WordDefinition.objects.get_or_create(
        entry=entry,
        meaning=vietnamese,
        defaults={'extra_data': def_extra},
    )
    if def_created:
        stats['created_definitions'] += 1
    elif relation_examples and not defn.extra_data.get('relations'):
        # Update relations if definition existed but had none
        defn.extra_data['relations'] = relation_examples
        defn.save(update_fields=['extra_data'])

    # --- 5. ExampleSentences ---
    existing_sentences = set(
        ExampleSentence.objects.filter(definition=defn).values_list('sentence', flat=True)
    )
    new_examples = []
    for ex_idx, ex in enumerate(sentence_examples):
        jp_html = ex.get('jp_html', '')
        if jp_html and jp_html not in existing_sentences:
            new_examples.append(ExampleSentence(
                definition=defn,
                sentence=jp_html,
                translation=ex.get('vn_text', ''),
                source=source,
                order=ex_idx,
            ))
    if new_examples:
        ExampleSentence.objects.bulk_create(new_examples)
        stats['created_examples'] += len(new_examples)

    # --- 6. SetItem + SetItemExample ---
    if vocab_set:
        set_item, _ = SetItem.objects.get_or_create(
            vocabulary_set=vocab_set,
            definition=defn,
            defaults={'display_order': order},
        )
        # Link this import's examples to the set_item
        all_examples = list(ExampleSentence.objects.filter(
            definition=defn, source=source,
        ))
        for ex_order, ex_obj in enumerate(all_examples):
            SetItemExample.objects.get_or_create(
                set_item=set_item,
                example=ex_obj,
                defaults={'order': ex_order},
            )


def _parse_lesson(lesson_str):
    """
    Parse lesson string into structured data.

    Input:  "Unit 01 – Danh từ A – Bài 1 | Từ vựng Mimikara Oboeru N2"
    Output: {
        'title': 'Unit 01 – Danh từ A – Bài 1',
        'chapter': 1,
        'chapter_name': 'Unit 01',
    }
    """
    # Split at | and take the first part as title
    title = lesson_str.split('|')[0].strip()

    # Extract unit/chapter number
    chapter = None
    chapter_name = ''
    m = re.match(r'(Unit\s*(\d+))', title, re.IGNORECASE)
    if m:
        chapter_name = m.group(1)
        chapter = int(m.group(2))

    return {
        'title': title,
        'chapter': chapter,
        'chapter_name': chapter_name,
    }


def distribute_jp_vocab(source='mimikara_n2', only_unassigned=True):
    """
    Auto-distribute imported JP words into VocabularySets grouped by lesson.

    Args:
        source: ExampleSentence source to link SetItemExamples for
        only_unassigned: if True, skip words already in a set

    Returns:
        dict with stats: sets_created, sets_reused, words_assigned, already_assigned
    """
    stats = {
        'sets_created': 0,
        'sets_reused': 0,
        'words_assigned': 0,
        'already_assigned': 0,
    }

    # 1. Find all JP vocabs with a lesson field
    jp_vocabs = Vocabulary.objects.filter(
        language=Vocabulary.Language.JAPANESE,
        extra_data__lesson__isnull=False,
    ).exclude(extra_data__lesson='')

    # 2. Group by lesson
    lesson_groups = defaultdict(list)
    for vocab in jp_vocabs:
        lesson = vocab.extra_data.get('lesson', '')
        if lesson:
            lesson_groups[lesson].append(vocab)

    if not lesson_groups:
        return stats

    # 3. Pre-compute vocab IDs already in ANY set (for consistent skip logic)
    already_in_set_ids = set()
    if only_unassigned:
        already_in_set_ids = set(
            SetItem.objects.filter(
                definition__entry__vocab__language=Vocabulary.Language.JAPANESE,
            ).values_list('definition__entry__vocab_id', flat=True)
        )

    # 4. Process each lesson group
    with transaction.atomic():
        set_number_counter = VocabularySet.objects.filter(
            language=Vocabulary.Language.JAPANESE,
            toeic_level__isnull=True,
        ).count()

        for lesson_str, vocabs in sorted(lesson_groups.items()):
            parsed = _parse_lesson(lesson_str)

            # Get or create VocabularySet for this lesson
            vocab_set, created = VocabularySet.objects.get_or_create(
                title=parsed['title'],
                language=Vocabulary.Language.JAPANESE,
                defaults={
                    'status': VocabularySet.Status.PUBLISHED,
                    'is_public': True,
                    'chapter': parsed['chapter'],
                    'chapter_name': parsed['chapter_name'],
                    'description': lesson_str,
                    'set_number': set_number_counter + 1,
                }
            )
            if created:
                stats['sets_created'] += 1
                set_number_counter += 1
            else:
                stats['sets_reused'] += 1

            # Sort vocabs by order
            vocabs.sort(key=lambda v: v.extra_data.get('order', 0))

            # 5. Assign each word
            for display_order, vocab in enumerate(vocabs):
                # Skip if already in ANY set (matches confirmation page logic)
                if only_unassigned and vocab.id in already_in_set_ids:
                    stats['already_assigned'] += 1
                    continue

                # Get first definition for this vocab
                defn = WordDefinition.objects.filter(entry__vocab=vocab).first()
                if not defn:
                    continue

                set_item, si_created = SetItem.objects.get_or_create(
                    vocabulary_set=vocab_set,
                    definition=defn,
                    defaults={'display_order': display_order},
                )

                if si_created:
                    stats['words_assigned'] += 1
                    already_in_set_ids.add(vocab.id)

                    # Link examples (mimikara source) to this set_item
                    examples = ExampleSentence.objects.filter(
                        definition=defn, source=source,
                    )
                    for ex_order, ex_obj in enumerate(examples):
                        SetItemExample.objects.get_or_create(
                            set_item=set_item,
                            example=ex_obj,
                            defaults={'order': ex_order},
                        )
                else:
                    stats['already_assigned'] += 1

    return stats
