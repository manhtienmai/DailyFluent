"""
Management command to load EN10 vocabulary topics from fixture JSON.

Usage:
    python manage.py load_en10_vocab
    python manage.py load_en10_vocab --clear
"""
import json
import os

from django.core.management.base import BaseCommand
from exam.models import EN10VocabTopic


class Command(BaseCommand):
    help = "Load EN10 vocabulary topics from exam/fixtures/en10_vocab_topics.json"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Remove existing data before loading")

    def handle(self, *args, **options):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "fixtures",
            "en10_vocab_topics.json",
        )

        if not os.path.exists(fixture_path):
            self.stderr.write(self.style.ERROR(f"Fixture not found: {fixture_path}"))
            return

        if options["clear"]:
            deleted, _ = EN10VocabTopic.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing vocab topics"))

        with open(fixture_path, "r", encoding="utf-8") as f:
            topics = json.load(f)

        created = 0
        updated = 0
        total_words = 0

        for topic_data in topics:
            obj, was_created = EN10VocabTopic.objects.update_or_create(
                slug=topic_data["slug"],
                defaults={
                    "title": topic_data["title"],
                    "title_vi": topic_data["title_vi"],
                    "emoji": topic_data["emoji"],
                    "order": topic_data["order"],
                    "words": topic_data["words"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
            total_words += len(topic_data["words"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Vocab Topics: {created} created, {updated} updated "
                f"(total: {created + updated}, {total_words} words)"
            )
        )
