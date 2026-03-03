"""
Management command: Generate TTS audio for vocabulary words.

Usage:
    python manage.py generate_tts --language en --limit 50
    python manage.py generate_tts --language jp --limit 20 --force
    python manage.py generate_tts --entry-id 123
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate TTS audio for WordEntry records (Google TTS → Azure → DB)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--language",
            type=str,
            default="en",
            choices=["en", "jp"],
            help="Language to generate audio for (default: en)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Max number of entries to process (default: 50)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing audio URLs",
        )
        parser.add_argument(
            "--entry-id",
            type=int,
            default=None,
            help="Process a single WordEntry by ID",
        )

    def handle(self, *args, **options):
        from vocab.tts_service import generate_audio_for_entry, batch_generate

        entry_id = options.get("entry_id")

        if entry_id:
            self.stdout.write(f"Processing single entry ID={entry_id}...")
            try:
                result = generate_audio_for_entry(entry_id, force=options["force"])
                self.stdout.write(self.style.SUCCESS(f"Done: {result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
            return

        language = options["language"]
        limit = options["limit"]
        force = options["force"]

        self.stdout.write(
            f"Batch TTS: language={language}, limit={limit}, force={force}"
        )

        result = batch_generate(language=language, limit=limit, force=force)

        if "error" in result:
            self.stdout.write(self.style.ERROR(result["error"]))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"\nBatch complete: {result['success']}/{result['total']} success, "
                f"{result['errors']} errors"
            )
        )

        if result.get("error_list"):
            self.stdout.write(self.style.WARNING("\nErrors:"))
            for err in result["error_list"]:
                self.stdout.write(f"  • {err}")
