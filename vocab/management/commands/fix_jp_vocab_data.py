"""
Management command to fix missing fields in Japanese vocabulary data.

Phase 1: Copy reading from extra_data to WordEntry.ipa
Phase 2: Use Gemini AI to batch-fill missing han_viet, reading, part_of_speech

Usage:
    python manage.py fix_jp_vocab_data                    # Run all fixes
    python manage.py fix_jp_vocab_data --dry-run          # Preview only
    python manage.py fix_jp_vocab_data --audit-only       # Show stats only
    python manage.py fix_jp_vocab_data --batch-size=30    # Custom batch size
    python manage.py fix_jp_vocab_data --phase=1          # Run phase 1 only
    python manage.py fix_jp_vocab_data --phase=2          # Run phase 2 only
"""
import sys
import json
import time
import re
import logging
from django.core.management.base import BaseCommand
from django.db.models import Q
from vocab.models import Vocabulary, WordEntry

logger = logging.getLogger(__name__)

GEMINI_PROMPT = """Bạn là chuyên gia tiếng Nhật. Cho danh sách từ vựng tiếng Nhật dưới đây, hãy bổ sung các trường còn thiếu.

Quy tắc:
1. "han_viet": Âm Hán Việt viết HOA, VD: "TÂM LÝ", "KINH TẾ". Nếu từ thuần Nhật (hiragana/katakana, không có Hán tự) thì trả về chuỗi rỗng "".
2. "reading": Cách đọc bằng hiragana. VD: "しんり". Nếu từ đã là hiragana thì giữ nguyên. Katakana thì chuyển sang katakana.
3. "part_of_speech": Loại từ. Dùng các giá trị: "noun", "verb", "adj-i", "adj-na", "adverb", "particle", "expression", "counter", "prefix", "suffix", "conjunction", "interjection", "pronoun", "noun/verb" (cho danh từ + する). Nếu từ có ＜する＞ thì là "noun/verb".

QUAN TRỌNG: 
- Chỉ trả về JSON array, KHÔNG có markdown code block hay text thừa.
- Mỗi object trong array phải có đúng 4 trường: "word", "han_viet", "reading", "part_of_speech".

Danh sách từ cần xử lý:
{words_json}

Trả về JSON array:"""


class Command(BaseCommand):
    help = 'Fix missing fields in Japanese vocabulary (han_viet, reading, part_of_speech, ipa)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without saving',
        )
        parser.add_argument(
            '--audit-only', action='store_true',
            help='Only show statistics, no fixes',
        )
        parser.add_argument(
            '--batch-size', type=int, default=50,
            help='Words per Gemini API call (default: 50)',
        )
        parser.add_argument(
            '--phase', type=int, default=0,
            help='Run specific phase only (1 or 2, 0=all)',
        )

    def _write(self, msg, style=None):
        """Write with flush to ensure output is visible immediately."""
        if style:
            msg = style(msg)
        self.stdout.write(msg)
        self.stdout.flush()
        sys.stdout.flush()

    def handle(self, *args, **options):
        sys.stdout.reconfigure(encoding='utf-8')
        self.dry_run = options['dry_run']
        self.batch_size = options['batch_size']
        phase = options['phase']

        if options['audit_only']:
            self._audit()
            return

        if phase in (0, 1):
            self._phase1_copy_ipa()
        if phase in (0, 2):
            self._phase2_gemini_fill()

        self._write('\n✅ All done!', self.style.SUCCESS)
        self._audit()

    def _audit(self):
        """Show current data completeness stats."""
        jp = Vocabulary.objects.filter(language='jp')
        total = jp.count()

        missing_hv = sum(1 for v in jp if not v.extra_data.get('han_viet'))
        missing_rd = sum(1 for v in jp if not v.extra_data.get('reading'))

        jp_entries = WordEntry.objects.filter(vocab__language='jp')
        missing_pos = jp_entries.filter(Q(part_of_speech='') | Q(part_of_speech__isnull=True)).count()
        missing_ipa = jp_entries.filter(Q(ipa='') | Q(ipa__isnull=True)).count()

        self._write(f'\n📊 Audit: {total} JP vocab')
        self._write(f'  Missing han_viet:        {missing_hv}')
        self._write(f'  Missing reading:         {missing_rd}')
        self._write(f'  Missing part_of_speech:  {missing_pos}')
        self._write(f'  Missing ipa:             {missing_ipa}')

    def _phase1_copy_ipa(self):
        """Copy reading from Vocabulary.extra_data to WordEntry.ipa."""
        self._write('\n━━━ Phase 1: Copy reading → ipa ━━━', self.style.HTTP_INFO)

        entries = WordEntry.objects.filter(
            vocab__language='jp'
        ).filter(
            Q(ipa='') | Q(ipa__isnull=True)
        ).select_related('vocab')

        updated = 0
        for entry in entries:
            reading = entry.vocab.extra_data.get('reading', '')
            if reading:
                if not self.dry_run:
                    entry.ipa = reading
                    entry.save(update_fields=['ipa'])
                updated += 1

        action = 'Would copy' if self.dry_run else 'Copied'
        self._write(f'  {action} ipa for {updated} entries', self.style.SUCCESS)

    def _phase2_gemini_fill(self):
        """Use Gemini to batch-fill missing han_viet, reading, part_of_speech."""
        self._write('\n━━━ Phase 2: Gemini batch fill ━━━', self.style.HTTP_INFO)

        # Gather all vocab needing fixes
        jp_vocabs = list(Vocabulary.objects.filter(language='jp').prefetch_related('entries'))

        # Build work items: vocab objects that need at least one field fixed
        work_items = []
        for v in jp_vocabs:
            needs = {}
            if not v.extra_data.get('han_viet') and v.extra_data.get('han_viet') != '':
                # missing han_viet (never been set)
                needs['han_viet'] = True
            if not v.extra_data.get('reading'):
                needs['reading'] = True
            # Check if any entry is missing part_of_speech
            entries = list(v.entries.all())
            missing_pos_entries = [e for e in entries if not e.part_of_speech]
            if missing_pos_entries:
                needs['part_of_speech'] = True
            if needs:
                work_items.append((v, needs, entries))

        total_items = len(work_items)
        if total_items == 0:
            self._write('  No items need Gemini fixes.')
            return

        self._write(f'  Found {total_items} vocab needing AI fixes')

        if self.dry_run:
            self._write('  [DRY RUN] Would process in '
                        f'{(total_items + self.batch_size - 1) // self.batch_size} batches')
            # Show sample
            for v, needs, _ in work_items[:10]:
                self._write(f'    {v.word} → needs: {", ".join(needs.keys())}')
            return

        # Process in batches
        from vocab.services.gemini_service import GeminiService

        total_batches = (total_items + self.batch_size - 1) // self.batch_size
        total_updated = 0
        total_errors = 0

        for batch_idx in range(total_batches):
            start = batch_idx * self.batch_size
            end = min(start + self.batch_size, total_items)
            batch = work_items[start:end]

            self._write(f'  Batch {batch_idx + 1}/{total_batches} '
                       f'({start + 1}-{end}/{total_items})...')

            # Build prompt
            words_for_prompt = []
            for v, needs, entries in batch:
                item = {'word': v.word}
                # Give existing data as hints
                if v.extra_data.get('reading'):
                    item['reading_hint'] = v.extra_data['reading']
                words_for_prompt.append(item)

            words_json = json.dumps(words_for_prompt, ensure_ascii=False, indent=2)
            prompt = GEMINI_PROMPT.format(words_json=words_json)

            # Call Gemini
            try:
                raw_response = GeminiService.generate_text(prompt)
                results = self._parse_gemini_response(raw_response, batch)
            except Exception as e:
                logger.error(f'Gemini batch {batch_idx + 1} error: {e}')
                self._write(f'    Error: {e}', self.style.ERROR)
                total_errors += len(batch)
                time.sleep(2)
                continue

            # Apply results
            batch_updated = self._apply_results(results, batch)
            total_updated += batch_updated
            self._write(f'    Updated {batch_updated}/{len(batch)}')

            # Rate limiting — be nice to the API
            if batch_idx < total_batches - 1:
                time.sleep(1)

        self._write(
            f'  Phase 2 done: {total_updated} updated, {total_errors} errors',
            self.style.SUCCESS
        )

    def _parse_gemini_response(self, raw_text, batch):
        """Parse Gemini JSON response, handling markdown code blocks."""
        text = raw_text.strip()

        # Strip markdown code block if present
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*\n?', '', text)
            text = re.sub(r'\n?```\s*$', '', text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON array from text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                logger.error(f'Cannot parse Gemini response: {text[:200]}')
                return {}

        # Build word -> result mapping
        result_map = {}
        for item in data:
            word = item.get('word', '')
            if word:
                result_map[word] = item
        return result_map

    def _apply_results(self, results, batch):
        """Apply Gemini results to database."""
        updated = 0

        for v, needs, entries in batch:
            result = results.get(v.word)
            if not result:
                continue

            changed = False
            vocab_changed = False

            # Update han_viet
            if 'han_viet' in needs and result.get('han_viet') is not None:
                v.extra_data['han_viet'] = result['han_viet']
                vocab_changed = True

            # Update reading
            if 'reading' in needs and result.get('reading'):
                v.extra_data['reading'] = result['reading']
                vocab_changed = True

            if vocab_changed:
                v.save(update_fields=['extra_data'])
                changed = True

            # Update part_of_speech on entries
            if 'part_of_speech' in needs and result.get('part_of_speech'):
                pos = result['part_of_speech']
                # Check which POS values already exist for this vocab
                existing_pos = {e.part_of_speech for e in entries if e.part_of_speech}
                for entry in entries:
                    if not entry.part_of_speech:
                        # Skip if this POS already exists (unique constraint)
                        if pos in existing_pos:
                            continue
                        try:
                            entry.part_of_speech = pos
                            entry.save(update_fields=['part_of_speech'])
                            existing_pos.add(pos)
                            changed = True
                        except Exception:
                            continue
                        # Also copy reading to ipa if missing
                        if not entry.ipa and v.extra_data.get('reading'):
                            entry.ipa = v.extra_data['reading']
                            entry.save(update_fields=['ipa'])

            if changed:
                updated += 1

        return updated
