"""
Management command: load EN10 Grammar Topics and Phrasal Verbs data.

Usage:
    python manage.py load_en10_grammar          # seed all data
    python manage.py load_en10_grammar --clear   # clear existing data first
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load EN10 Grammar Topics and Phrasal Verbs into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing EN10 grammar data before loading",
        )

    def handle(self, *args, **options):
        from exam.models import EN10GrammarTopic, EN10PhrasalVerbSet

        if options["clear"]:
            EN10GrammarTopic.objects.all().delete()
            EN10PhrasalVerbSet.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing EN10 grammar data."))

        # ── Load Grammar Topics ──
        fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"

        topics_file = fixtures_dir / "en10_grammar_topics.json"
        if not topics_file.exists():
            self.stdout.write(self.style.ERROR(f"Fixture not found: {topics_file}"))
            return

        with open(topics_file, "r", encoding="utf-8") as f:
            topics_data = json.load(f)

        created_topics = 0
        updated_topics = 0
        for item in topics_data:
            _, created = EN10GrammarTopic.objects.update_or_create(
                topic_id=item["topic_id"],
                defaults={
                    "title": item["title"],
                    "title_vi": item["title_vi"],
                    "emoji": item["emoji"],
                    "description": item.get("description", ""),
                    "difficulty": item.get("difficulty", "easy"),
                    "order": item.get("order", 0),
                    "sections": item.get("sections", []),
                    "formulas": item.get("formulas", []),
                    "exercises": item.get("exercises", []),
                    "is_active": True,
                },
            )
            if created:
                created_topics += 1
            else:
                updated_topics += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Grammar Topics: {created_topics} created, {updated_topics} updated "
                f"(total: {EN10GrammarTopic.objects.count()})"
            )
        )

        # ── Load Phrasal Verbs ──
        pv_file = fixtures_dir / "en10_phrasal_verbs.json"
        if not pv_file.exists():
            self.stdout.write(self.style.ERROR(f"Fixture not found: {pv_file}"))
            return

        with open(pv_file, "r", encoding="utf-8") as f:
            pv_data = json.load(f)

        obj, created = EN10PhrasalVerbSet.objects.update_or_create(
            id=1,
            defaults={
                "title": pv_data.get("title", "Phrasal Verbs"),
                "verbs": pv_data.get("verbs", []),
                "fill_sentences": pv_data.get("fill_sentences", []),
                "quiz_questions": pv_data.get("quiz_questions", []),
                "is_active": True,
            },
        )

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Phrasal Verbs: {action} — "
                f"{len(obj.verbs)} verbs, {len(obj.fill_sentences)} fill, {len(obj.quiz_questions)} quiz"
            )
        )

        self.stdout.write(self.style.SUCCESS("\nEN10 Grammar data loaded successfully!"))
