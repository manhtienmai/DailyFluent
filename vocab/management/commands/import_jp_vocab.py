"""
Management command to import Japanese vocabulary from Mimikara-format JSON.

Usage:
    python manage.py import_jp_vocab path/to/file.json
    python manage.py import_jp_vocab path/to/file.json --set-id=123
    python manage.py import_jp_vocab path/to/file.json --pos=verb --source=other
"""
import json
from django.core.management.base import BaseCommand
from vocab.models import VocabularySet
from vocab.services.jp_import import import_jp_vocab_data


class Command(BaseCommand):
    help = 'Import Japanese vocabulary from Mimikara-format JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file')
        parser.add_argument('--set-id', type=int, default=None, help='VocabularySet ID to add words to')
        parser.add_argument('--pos', type=str, default='noun', help='Default part_of_speech (default: noun)')
        parser.add_argument('--source', type=str, default='other', help='ExampleSentence source (default: other)')

    def handle(self, *args, **options):
        file_path = options['file_path']
        set_id = options['set_id']
        default_pos = options['pos']
        source = options['source']

        # Load JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f'Invalid JSON: {e}'))
            return

        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR('JSON must be a list of objects.'))
            return

        # Resolve VocabularySet
        vocab_set = None
        if set_id:
            try:
                vocab_set = VocabularySet.objects.get(pk=set_id)
                self.stdout.write(f'Adding words to set: {vocab_set.title}')
            except VocabularySet.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'VocabularySet with ID {set_id} not found.'))
                return

        self.stdout.write(f'Importing {len(data)} items (pos={default_pos}, source={source})...')

        stats = import_jp_vocab_data(
            items=data,
            vocab_set=vocab_set,
            source=source,
            default_pos=default_pos,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Done! Vocabs: {stats['created_vocabs']}, "
            f"Definitions: {stats['created_definitions']}, "
            f"Examples: {stats['created_examples']}, "
            f"Skipped: {stats['skipped']}"
        ))
