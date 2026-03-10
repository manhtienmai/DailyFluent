"""
Management command: delete all N1 kanji data (lessons, kanji, vocab, quiz, progress).

The N1 data currently contains multi-character vocabulary words instead of
single kanji characters, so it must be removed.

Usage:
    python manage.py delete_n1_kanji              # delete from local DB
    python manage.py delete_n1_kanji --dry-run     # preview only
"""

from django.core.management.base import BaseCommand

from kanji.models import (
    Kanji, KanjiLesson, KanjiVocab,
    KanjiQuizQuestion, UserKanjiProgress,
)


class Command(BaseCommand):
    help = "Delete all N1 kanji data (incorrect vocabulary words, not single kanji)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview deletion counts without actually deleting.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        n1_lessons = KanjiLesson.objects.filter(jlpt_level="N1")
        n1_kanji_ids = list(
            Kanji.objects.filter(lesson__in=n1_lessons).values_list("id", flat=True)
        )

        counts = {
            "KanjiLesson": n1_lessons.count(),
            "Kanji": len(n1_kanji_ids),
            "KanjiVocab": KanjiVocab.objects.filter(kanji_id__in=n1_kanji_ids).count(),
            "KanjiQuizQuestion": KanjiQuizQuestion.objects.filter(kanji_id__in=n1_kanji_ids).count(),
            "UserKanjiProgress": UserKanjiProgress.objects.filter(kanji_id__in=n1_kanji_ids).count(),
        }

        self.stdout.write(self.style.HTTP_INFO("\n=== N1 Kanji Data to Delete ==="))
        for model_name, count in counts.items():
            self.stdout.write(f"  {model_name}: {count} records")

        total = sum(counts.values())
        self.stdout.write(f"\n  Total: {total} records")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n*** DRY-RUN: No data was deleted. ***\n"))
            return

        # CASCADE from KanjiLesson will handle Kanji → KanjiVocab, KanjiQuizQuestion, UserKanjiProgress
        deleted_count, details = n1_lessons.delete()
        self.stdout.write(self.style.SUCCESS(f"\n[OK] Deleted {deleted_count} records total."))
        for model, count in details.items():
            self.stdout.write(f"  {model}: {count}")

        # Clear kanji_levels cache
        from django.core.cache import cache
        cache.delete("kanji_levels_v1")
        self.stdout.write(self.style.SUCCESS("[OK] Cleared kanji_levels cache.\n"))
