"""
Shared import logic for Japanese vocabulary.

Supports auto-grouping by metadata.lesson into separate VocabularySets,
with chapter/section detection from filenames or lesson ordering.

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
"""
import logging
import re
from collections import defaultdict, OrderedDict
from django.db import transaction

from vocab.models import (
    Vocabulary, WordEntry, WordDefinition, ExampleSentence,
    VocabularySet, SetItem, SetItemExample,
)

logger = logging.getLogger(__name__)


def import_jp_vocab_data(items, vocab_set=None, source='mimikara_n2', default_pos='noun'):
    """
    Import Japanese vocabulary from structured JSON data.
    Supports multiple JSON formats (Mimikara, Tango, generic).

    Args:
        items: list of dicts
        vocab_set: optional VocabularySet to add words to
        source: ExampleSentence.source value
        default_pos: default part_of_speech

    Returns:
        dict with counts
    """
    stats = {
        'created_vocabs': 0,
        'existing_vocabs': 0,
        'created_definitions': 0,
        'existing_definitions': 0,
        'created_examples': 0,
        'added_to_set': 0,
        'skipped': 0,
        'skip_reasons': [],
    }

    with transaction.atomic():
        for idx, item in enumerate(items):
            try:
                _import_single_item(item, vocab_set, source, default_pos, idx, stats)
            except Exception as e:
                logger.warning("Skipping item %d: %s", idx, e)
                stats['skipped'] += 1
                if len(stats['skip_reasons']) < 3:
                    stats['skip_reasons'].append(f"Exception #{idx}: {str(e)[:100]}")

    return stats


def import_jp_vocab_grouped(file_items_list, collection, source='other', default_pos='noun'):
    """
    Import Japanese vocabulary with auto-grouping by lesson into separate
    VocabularySets within a collection.

    Each unique metadata.lesson → 1 VocabularySet.
    Chapter/section info is extracted from filenames when available.

    Args:
        file_items_list: list of (filename_or_none, items_list) tuples.
            Each tuple is one file's worth of data.
        collection: VocabSource to attach sets to.
        source: ExampleSentence.source value.
        default_pos: default part_of_speech.

    Returns:
        dict with total stats + sets_created info.
    """
    total_stats = {
        'created_vocabs': 0,
        'existing_vocabs': 0,
        'created_definitions': 0,
        'existing_definitions': 0,
        'created_examples': 0,
        'added_to_set': 0,
        'skipped': 0,
        'skip_reasons': [],
        'sets_created': 0,
        'sets_detail': [],
    }

    # ---- Step 1: Build groups keyed by (chapter, section, lesson_topic) ----
    # Each group = one VocabularySet
    groups = OrderedDict()  # key -> { 'chapter': int, 'section': int, 'topic': str, 'items': [] }

    for filename, items in file_items_list:
        # Try to extract chapter/section from filename
        file_chapter = None
        file_section = None
        if filename:
            ch_match = re.search(r'chapter[_-](\d+)', filename, re.IGNORECASE)
            sec_match = re.search(r'section[_-](\d+)', filename, re.IGNORECASE)
            if ch_match:
                file_chapter = int(ch_match.group(1))
            if sec_match:
                file_section = int(sec_match.group(1))

        # Get lesson/topic from first item's metadata
        topic = ''
        if items:
            metadata = items[0].get('metadata', {})
            if isinstance(metadata, dict):
                lesson_raw = metadata.get('lesson', '') or ''
            else:
                lesson_raw = str(metadata)

            # "Từ vựng N2 - Chủ đề Gia đình" → "Chủ đề Gia đình"
            if ' - ' in lesson_raw:
                topic = lesson_raw.split(' - ', 1)[1].strip()
            elif ' – ' in lesson_raw:
                topic = lesson_raw.split(' – ', 1)[1].strip()
            else:
                topic = lesson_raw.strip()

        if not topic:
            topic = filename or f'Set {len(groups) + 1}'

        # Build a unique group key
        # If we have chapter+section from filename, use that.
        # Otherwise use the topic string as grouping key.
        if file_chapter is not None:
            key = (file_chapter, file_section or 1, topic)
        else:
            key = (None, None, topic)

        if key not in groups:
            groups[key] = {
                'chapter': file_chapter,
                'section': file_section or 1,
                'topic': topic,
                'items': [],
            }
        groups[key]['items'].extend(items)

    # ---- Step 2: Auto-assign chapter numbers for groups without them ----
    # Group by topic prefix to detect natural chapters
    has_chapters = any(g['chapter'] is not None for g in groups.values())

    if not has_chapters:
        # No chapter info from filenames. Try to detect from lesson patterns.
        # Strategy: each unique lesson becomes its own set in chapter 1
        # unless we detect "Unit X" / "Chapter X" / "Bài X" patterns
        chapter_counter = 1
        prev_chapter = None
        for key, group in groups.items():
            topic = group['topic']
            # Try to detect chapter from topic: "Unit 1 ...", "Chapter 2 ..."
            ch_match = re.match(
                r'(?:Unit|Chapter|Chương|Bài|Lesson)\s*(\d+)',
                topic, re.IGNORECASE
            )
            if ch_match:
                group['chapter'] = int(ch_match.group(1))
            else:
                # Each group is its own chapter
                group['chapter'] = chapter_counter
                chapter_counter += 1
            group['section'] = 1

    # ---- Step 3: Determine set_number ordering and chapter_names ----
    sorted_groups = sorted(
        groups.values(),
        key=lambda g: (g['chapter'] or 0, g['section'] or 0)
    )

    # Determine chapter_name = first section's topic within each chapter
    chapter_names = {}
    for g in sorted_groups:
        ch = g['chapter']
        if ch and ch not in chapter_names:
            chapter_names[ch] = g['topic']

    # ---- Step 4: Determine starting set_number ----
    existing_max = VocabularySet.objects.filter(
        collection=collection
    ).order_by('-set_number').values_list('set_number', flat=True).first()
    next_set_number = (existing_max or 0) + 1

    # ---- Step 5: Create sets and import items ----
    with transaction.atomic():
        for g in sorted_groups:
            chapter = g['chapter']
            topic = g['topic']
            items = g['items']
            ch_name = chapter_names.get(chapter, topic)

            if not items:
                continue

            # Create VocabularySet
            vocab_set = VocabularySet.objects.create(
                title=topic,
                collection=collection,
                language=collection.language or 'jp',
                is_public=True,
                status=VocabularySet.Status.PUBLISHED,
                set_number=next_set_number,
                chapter=chapter,
                chapter_name=ch_name,
            )
            next_set_number += 1
            total_stats['sets_created'] += 1

            # Import items into this set
            stats = import_jp_vocab_data(
                items=items,
                vocab_set=vocab_set,
                source=source,
                default_pos=default_pos,
            )

            # Accumulate stats
            for k in ['created_vocabs', 'existing_vocabs', 'created_definitions',
                       'existing_definitions', 'created_examples', 'added_to_set',
                       'skipped']:
                total_stats[k] += stats.get(k, 0)
            total_stats['skip_reasons'].extend(stats.get('skip_reasons', []))

            total_stats['sets_detail'].append({
                'title': topic,
                'chapter': chapter,
                'count': stats.get('added_to_set', 0),
            })

    return total_stats


def _extract_fields(item, item_idx, default_pos):
    """
    Extract fields from a JSON item, supporting multiple formats.
    Returns a dict with normalized field names or None if item is invalid.
    """
    # --- Word (kanji) ---
    # Try multiple paths: word_info.kanji → word → kanji → text
    word_info = item.get('word_info', {})
    if isinstance(word_info, str):
        kanji = word_info
        word_info = {}
    else:
        kanji = (
            word_info.get('kanji', '') or
            word_info.get('word', '') or
            word_info.get('text', '')
        )
    if not kanji:
        kanji = item.get('word', '') or item.get('kanji', '') or item.get('text', '')
    kanji = kanji.strip()
    if not kanji:
        return {'_skip_reason': f"No kanji found. Keys: {list(item.keys())[:10]}"}


    # --- Reading ---
    reading = (
        word_info.get('reading', '') or
        item.get('reading', '') or
        item.get('kana', '') or
        item.get('hiragana', '')
    )

    # --- HTML display ---
    html_display = (
        word_info.get('html_display', '') or
        item.get('html_display', '') or
        item.get('display', '')
    )

    # --- Meanings (Vietnamese) ---
    meanings = item.get('meanings', {})
    if isinstance(meanings, str):
        vietnamese = meanings
        han_viet = ''
    elif isinstance(meanings, list):
        # ["nghĩa 1", "nghĩa 2"] → join
        vietnamese = ', '.join(str(m) for m in meanings if m)
        han_viet = ''
    else:
        vietnamese = (
            meanings.get('vietnamese', '') or
            meanings.get('vi', '') or
            meanings.get('meaning', '') or
            meanings.get('translation', '')
        )
        han_viet = meanings.get('han_viet', '') or meanings.get('hanviet', '')

    # Fallback: try top-level meaning fields
    if not vietnamese:
        vietnamese = (
            item.get('meaning', '') or
            item.get('vietnamese', '') or
            item.get('vi', '') or
            item.get('translation', '') or
            item.get('definition', '')
        )
        # If meaning is a list
        if isinstance(vietnamese, list):
            vietnamese = ', '.join(str(m) for m in vietnamese if m)

    # --- Metadata ---
    metadata = item.get('metadata', {})
    if isinstance(metadata, str):
        lesson = metadata
        audio = ''
    else:
        lesson = metadata.get('lesson', '') or item.get('lesson', '') or item.get('unit', '')
        audio = metadata.get('audio', '') or item.get('audio', '')

    # --- Han viet fallback ---
    if not han_viet:
        han_viet = item.get('han_viet', '') or item.get('hanviet', '')

    # --- Examples ---
    examples = item.get('examples', []) or item.get('sentences', []) or []
    if isinstance(examples, str):
        examples = [{'type': 'sentence', 'jp_text': examples}]

    # --- Other fields ---
    source_id = item.get('id', '') or item.get('source_id', '')
    order = item.get('original_number', None) or item.get('order', None) or item.get('number', None)
    if order is None:
        order = item_idx
    pos = item.get('part_of_speech', '') or item.get('pos', '') or default_pos

    return {
        'kanji': kanji,
        'reading': reading,
        'html_display': html_display,
        'vietnamese': vietnamese.strip() if isinstance(vietnamese, str) else '',
        'han_viet': han_viet,
        'lesson': lesson,
        'audio': audio,
        'source_id': str(source_id),
        'order': order,
        'pos': pos,
        'examples': examples,
    }


def _import_single_item(item, vocab_set, source, default_pos, item_idx, stats):
    """Import a single vocabulary item."""
    # --- Extract fields (multi-format) ---
    fields = _extract_fields(item, item_idx, default_pos)
    if fields is None or fields.get('_skip_reason'):
        stats['skipped'] += 1
        if fields and len(stats.get('skip_reasons', [])) < 5:
            stats.setdefault('skip_reasons', []).append(fields.get('_skip_reason', 'Unknown'))
        return

    kanji = fields['kanji']
    reading = fields['reading']
    html_display = fields['html_display']
    vietnamese = fields['vietnamese']
    han_viet = fields['han_viet']
    lesson = fields['lesson']
    audio = fields['audio']
    source_id = fields['source_id']
    order = fields['order']
    pos = fields['pos']
    examples = fields['examples']

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
        stats['existing_vocabs'] += 1
        # Merge extra_data for existing vocab
        changed = False
        for key, val in extra_data.items():
            if val and vocab.extra_data.get(key) != val:
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
        if isinstance(ex, str):
            sentence_examples.append({'jp_text': ex, 'jp_html': ex, 'vn_text': ''})
        elif ex.get('type', 'sentence') == 'sentence' or 'jp_text' in ex or 'sentence' in ex:
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
    # If no vietnamese meaning, try to use the word's existing definition
    # or use the kanji itself as a placeholder
    if not vietnamese:
        # Check if this vocab already has a definition
        existing_defn = WordDefinition.objects.filter(entry__vocab=vocab).first()
        if existing_defn:
            defn = existing_defn
            stats['existing_definitions'] += 1
        else:
            # Use kanji as placeholder meaning
            defn = WordDefinition.objects.create(
                entry=entry,
                meaning=kanji,
            )
            stats['created_definitions'] += 1
    else:
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
        else:
            stats['existing_definitions'] += 1
            if relation_examples and not defn.extra_data.get('relations'):
                defn.extra_data['relations'] = relation_examples
                defn.save(update_fields=['extra_data'])

    # --- 5. ExampleSentences ---
    existing_sentences = set(
        ExampleSentence.objects.filter(definition=defn).values_list('sentence', flat=True)
    )
    new_examples = []
    for ex_idx, ex in enumerate(sentence_examples):
        # Try multiple fields for the sentence text
        sentence_text = (
            ex.get('jp_html', '') or
            ex.get('sentence', '') or
            ex.get('jp_text', '') or
            ex.get('japanese', '') or
            ex.get('text', '')
        )
        translation = (
            ex.get('vn_text', '') or
            ex.get('translation', '') or
            ex.get('vi_text', '') or
            ex.get('meaning', '')
        )
        if sentence_text and sentence_text not in existing_sentences:
            new_examples.append(ExampleSentence(
                definition=defn,
                sentence=sentence_text,
                translation=translation,
                source=source,
                order=ex_idx,
            ))
            existing_sentences.add(sentence_text)
    if new_examples:
        ExampleSentence.objects.bulk_create(new_examples)
        stats['created_examples'] += len(new_examples)

    # --- 6. SetItem + SetItemExample (ALWAYS create if vocab_set given) ---
    if vocab_set:
        set_item, si_created = SetItem.objects.get_or_create(
            vocabulary_set=vocab_set,
            definition=defn,
            defaults={'display_order': order},
        )
        if si_created:
            stats['added_to_set'] += 1

        # Link this import's examples to the set_item
        all_examples = list(ExampleSentence.objects.filter(definition=defn))
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
