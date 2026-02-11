"""
Management command to auto-distribute imported JP words into VocabularySets by lesson.

Usage:
    python manage.py distribute_jp_vocab
    python manage.py distribute_jp_vocab --include-assigned
"""
from django.core.management.base import BaseCommand
from vocab.services.jp_import import distribute_jp_vocab


class Command(BaseCommand):
    help = 'Auto-distribute imported JP vocabulary into VocabularySets grouped by lesson'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-assigned', action='store_true',
            help='Also process words already in a set (default: skip them)',
        )
        parser.add_argument(
            '--source', type=str, default='mimikara_n2',
            help='ExampleSentence source for SetItemExample linking (default: mimikara_n2)',
        )

    def handle(self, *args, **options):
        only_unassigned = not options['include_assigned']
        source = options['source']

        self.stdout.write(
            f'Distributing JP words by lesson '
            f'(only_unassigned={only_unassigned}, source={source})...'
        )

        stats = distribute_jp_vocab(source=source, only_unassigned=only_unassigned)

        self.stdout.write(self.style.SUCCESS(
            f"Done! Sets created: {stats['sets_created']}, "
            f"Sets reused: {stats['sets_reused']}, "
            f"Words assigned: {stats['words_assigned']}, "
            f"Already assigned: {stats['already_assigned']}"
        ))
