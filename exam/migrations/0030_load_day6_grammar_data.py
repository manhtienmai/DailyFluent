"""
Data migration: Load Day 6 grammar content (Prepositions + Word Stress) into EN10GrammarTopic.

Reads from exam/fixtures/en10_grammar_topics.json and upserts all topics.
This runs automatically on deploy (`python manage.py migrate`).
"""

import json
from pathlib import Path
from django.db import migrations


def load_grammar_data(apps, schema_editor):
    EN10GrammarTopic = apps.get_model('exam', 'EN10GrammarTopic')

    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"
    topics_file = fixtures_dir / "en10_grammar_topics.json"

    if not topics_file.exists():
        print(f"  ⚠️  Fixture not found: {topics_file}")
        return

    with open(topics_file, "r", encoding="utf-8") as f:
        topics_data = json.load(f)

    created = 0
    updated = 0
    for item in topics_data:
        _, was_created = EN10GrammarTopic.objects.update_or_create(
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
        if was_created:
            created += 1
        else:
            updated += 1

    print(f"  Grammar Topics: {created} created, {updated} updated (total: {EN10GrammarTopic.objects.count()})")


def reverse_load(apps, schema_editor):
    """Remove only the topics added in this migration."""
    EN10GrammarTopic = apps.get_model('exam', 'EN10GrammarTopic')
    EN10GrammarTopic.objects.filter(topic_id__in=["prepositions", "word-stress"]).delete()
    print("  Removed prepositions and word-stress topics.")


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0029_add_en10_vocab_progress'),
    ]

    operations = [
        migrations.RunPython(load_grammar_data, reverse_load),
    ]
