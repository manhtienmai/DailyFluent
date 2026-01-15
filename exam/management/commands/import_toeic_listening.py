"""
Management command to import TOEIC Listening questions with bilingual transcripts.

Usage:
    python manage.py import_toeic_listening exam_slug path/to/data.json
    python manage.py import_toeic_listening exam_slug path/to/data.json --dry-run
"""
import json
from django.core.management.base import BaseCommand, CommandError
from exam.models import ExamTemplate, ExamQuestion, ListeningConversation, TOEICPart


class Command(BaseCommand):
    help = 'Import TOEIC Listening questions with bilingual transcripts from JSON'

    def add_arguments(self, parser):
        parser.add_argument('exam_slug', type=str, help='Slug of the ExamTemplate')
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and validate without saving to database',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing questions instead of skipping',
        )

    def handle(self, *args, **options):
        exam_slug = options['exam_slug']
        json_file = options['json_file']
        dry_run = options['dry_run']
        update_existing = options['update']

        # Get or validate template
        try:
            template = ExamTemplate.objects.get(slug=exam_slug)
        except ExamTemplate.DoesNotExist:
            raise CommandError(f'ExamTemplate with slug "{exam_slug}" not found')

        # Load JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'JSON file not found: {json_file}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON: {e}')

        self.stdout.write(f'Importing to: {template.title}')
        self.stdout.write(f'Found {len(data)} items in JSON')

        stats = {
            'single_created': 0,
            'single_updated': 0,
            'group_created': 0,
            'group_updated': 0,
            'conversation_created': 0,
            'skipped': 0,
        }

        for item in data:
            item_type = item.get('type', 'single')

            if item_type == 'single':
                self._process_single_question(
                    template, item, dry_run, update_existing, stats
                )
            elif item_type == 'group':
                self._process_group_questions(
                    template, item, dry_run, update_existing, stats
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Unknown type: {item_type}, skipping')
                )
                stats['skipped'] += 1

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Import Summary ==='))
        self.stdout.write(f'Single questions created: {stats["single_created"]}')
        self.stdout.write(f'Single questions updated: {stats["single_updated"]}')
        self.stdout.write(f'Group questions created: {stats["group_created"]}')
        self.stdout.write(f'Group questions updated: {stats["group_updated"]}')
        self.stdout.write(f'Conversations created: {stats["conversation_created"]}')
        self.stdout.write(f'Skipped: {stats["skipped"]}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes saved.'))

    def _process_single_question(self, template, item, dry_run, update_existing, stats):
        """Process a single question (Part 1/2)"""
        q_num = item.get('question_number')
        
        # Determine TOEIC part (1-6 = Part 1, 7-31 = Part 2)
        if q_num <= 6:
            toeic_part = TOEICPart.LISTENING_1
        else:
            toeic_part = TOEICPart.LISTENING_2

        # Check if exists
        existing = ExamQuestion.objects.filter(
            template=template,
            order=q_num
        ).first()

        if existing and not update_existing:
            self.stdout.write(f'  Q{q_num}: exists, skipping')
            stats['skipped'] += 1
            return

        # Prepare options data
        options = item.get('options', [])
        options_data = [
            {
                'label': opt.get('label', ''),
                'text': opt.get('text', ''),
                'text_vi': opt.get('text_vi', ''),
            }
            for opt in options
        ]

        # Find correct answer (first option is usually marked or we need external data)
        # For now, store in transcript_data, correct_answer should be set separately
        correct_answer = item.get('correct_answer', 'A')

        if not dry_run:
            if existing:
                existing.audio_transcript = item.get('audio_transcript', '')
                existing.audio_transcript_vi = item.get('audio_transcript_vi', '')
                existing.transcript_data = {'options': options_data}
                existing.toeic_part = toeic_part
                existing.save()
                self.stdout.write(f'  Q{q_num}: updated')
                stats['single_updated'] += 1
            else:
                ExamQuestion.objects.create(
                    template=template,
                    order=q_num,
                    toeic_part=toeic_part,
                    audio_transcript=item.get('audio_transcript', ''),
                    audio_transcript_vi=item.get('audio_transcript_vi', ''),
                    transcript_data={'options': options_data},
                    correct_answer=correct_answer,
                )
                self.stdout.write(f'  Q{q_num}: created')
                stats['single_created'] += 1
        else:
            self.stdout.write(f'  Q{q_num}: would {"update" if existing else "create"}')
            if existing:
                stats['single_updated'] += 1
            else:
                stats['single_created'] += 1

    def _process_group_questions(self, template, item, dry_run, update_existing, stats):
        """Process a group of questions (Part 3/4)"""
        group_range = item.get('group_range', '')  # e.g., "32-34"
        questions = item.get('questions', [])
        
        if not questions:
            self.stdout.write(self.style.WARNING(f'  Group {group_range}: no questions'))
            stats['skipped'] += 1
            return

        # Parse range to get first question number
        try:
            first_q = int(group_range.split('-')[0])
        except (ValueError, IndexError):
            first_q = questions[0].get('question_number', 0)

        # Determine TOEIC part (32-70 = Part 3, 71-100 = Part 4)
        if first_q <= 70:
            toeic_part = TOEICPart.LISTENING_3
        else:
            toeic_part = TOEICPart.LISTENING_4

        # Calculate conversation order within part
        if toeic_part == TOEICPart.LISTENING_3:
            conv_order = (first_q - 32) // 3 + 1
        else:
            conv_order = (first_q - 71) // 3 + 1

        # Parse transcript into lines
        transcript = item.get('conversation_transcript', '')
        transcript_vi = item.get('conversation_transcript_vi', '')
        
        # Parse transcript into structured lines
        lines_data = self._parse_transcript_lines(transcript, transcript_vi)

        # Create or update ListeningConversation
        conversation = None
        if not dry_run:
            conversation, created = ListeningConversation.objects.update_or_create(
                template=template,
                toeic_part=toeic_part,
                order=conv_order,
                defaults={
                    'transcript': transcript,
                    'transcript_vi': transcript_vi,
                    'transcript_data': {'lines': lines_data},
                    'audio': '',  # Audio file should be added separately
                }
            )
            if created:
                stats['conversation_created'] += 1
                self.stdout.write(f'  Conversation {group_range}: created')
            else:
                self.stdout.write(f'  Conversation {group_range}: updated')

        # Process each question in the group
        for q_item in questions:
            q_num = q_item.get('question_number')
            
            existing = ExamQuestion.objects.filter(
                template=template,
                order=q_num
            ).first()

            if existing and not update_existing:
                stats['skipped'] += 1
                continue

            # Prepare options
            options = q_item.get('options', [])
            options_data = [
                {
                    'label': opt.get('label', ''),
                    'text': opt.get('text', ''),
                    'text_vi': opt.get('text_vi', ''),
                }
                for opt in options
            ]

            correct_answer = q_item.get('correct_answer', 'A')

            if not dry_run:
                if existing:
                    existing.text = q_item.get('question_text', '')
                    existing.text_vi = q_item.get('question_text_vi', '')
                    existing.transcript_data = {'options': options_data}
                    existing.toeic_part = toeic_part
                    existing.listening_conversation = conversation
                    existing.save()
                    stats['group_updated'] += 1
                else:
                    ExamQuestion.objects.create(
                        template=template,
                        order=q_num,
                        toeic_part=toeic_part,
                        listening_conversation=conversation,
                        text=q_item.get('question_text', ''),
                        text_vi=q_item.get('question_text_vi', ''),
                        transcript_data={'options': options_data},
                        correct_answer=correct_answer,
                    )
                    stats['group_created'] += 1
            else:
                if existing:
                    stats['group_updated'] += 1
                else:
                    stats['group_created'] += 1

        self.stdout.write(f'  Group {group_range}: processed {len(questions)} questions')

    def _parse_transcript_lines(self, transcript, transcript_vi):
        """Parse transcript text into structured lines with speaker labels"""
        lines = []
        
        # Split by newlines
        en_lines = transcript.strip().split('\n') if transcript else []
        vi_lines = transcript_vi.strip().split('\n') if transcript_vi else []

        for i, en_line in enumerate(en_lines):
            en_line = en_line.strip()
            if not en_line:
                continue

            # Extract speaker (M: W: M1: M2: etc.)
            speaker = ''
            text = en_line
            if ':' in en_line[:5]:
                parts = en_line.split(':', 1)
                speaker = parts[0].strip()
                text = parts[1].strip() if len(parts) > 1 else ''

            # Get corresponding Vietnamese line
            vi_text = ''
            if i < len(vi_lines):
                vi_line = vi_lines[i].strip()
                if ':' in vi_line[:5]:
                    vi_text = vi_line.split(':', 1)[1].strip() if ':' in vi_line else vi_line
                else:
                    vi_text = vi_line

            lines.append({
                'speaker': speaker,
                'text': text,
                'text_vi': vi_text,
            })

        return lines
