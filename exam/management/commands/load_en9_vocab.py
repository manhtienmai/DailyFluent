"""
Management command to load EN9 vocabulary topics from fixture JSON.

Creates:
  - EN10VocabTopic (reused model, slugs prefixed with en9-)
  - Vocabulary (core word, language=en)
  - WordEntry (pos, ipa)
  - WordDefinition (meaning)
  - M2M: EN10VocabTopic.vocabularies ↔ Vocabulary

Usage:
    python manage.py load_en9_vocab
    python manage.py load_en9_vocab --clear
"""
import json
import os

from django.core.management.base import BaseCommand

from exam.models import EN10VocabTopic
from vocab.models import Vocabulary, WordEntry, WordDefinition


class Command(BaseCommand):
    help = "Load EN9 vocabulary topics → Vocabulary + WordEntry + WordDefinition + M2M"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Remove existing EN9 data before loading")

    def handle(self, *args, **options):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "fixtures",
            "en9_vocab_topics.json",
        )

        if not os.path.exists(fixture_path):
            self.stderr.write(self.style.ERROR(f"Fixture not found: {fixture_path}"))
            return

        if options["clear"]:
            deleted, _ = EN10VocabTopic.objects.filter(slug__startswith="en9-").delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing EN9 vocab topics"))

        with open(fixture_path, "r", encoding="utf-8") as f:
            topics = json.load(f)

        topics_created = 0
        topics_updated = 0
        vocab_created = 0
        entry_created = 0
        defn_created = 0
        total_words = 0

        for topic_data in topics:
            # 1. Create/update EN10VocabTopic (reused for EN9)
            topic, was_created = EN10VocabTopic.objects.update_or_create(
                slug=topic_data["slug"],
                defaults={
                    "title": topic_data["title"],
                    "title_vi": topic_data["title_vi"],
                    "emoji": topic_data["emoji"],
                    "order": topic_data["order"],
                    "words": topic_data["words"],  # keep JSON for backward compat
                },
            )
            if was_created:
                topics_created += 1
            else:
                topics_updated += 1

            # 2. For each word → Vocabulary + WordEntry + WordDefinition + M2M
            vocab_ids = []
            for w in topic_data.get("words", []):
                word_text = w.get("word", "").strip()
                if not word_text:
                    continue

                # 2a. Vocabulary (unique by word)
                vocab, v_created = Vocabulary.objects.get_or_create(
                    word=word_text,
                    defaults={"language": "en"},
                )
                if v_created:
                    vocab_created += 1
                vocab_ids.append(vocab.id)

                # Normalize POS
                pos_raw = w.get("pos", "").strip().lower()
                pos_map = {
                    "noun": "n", "n": "n",
                    "verb": "v", "v": "v",
                    "adjective": "adj", "adj": "adj",
                    "adverb": "adv", "adv": "adv",
                    "preposition": "prep", "prep": "prep",
                    "conjunction": "conj", "conj": "conj",
                    "pronoun": "pron", "pron": "pron",
                    "interjection": "interj", "interj": "interj",
                    "phrasal verb": "phrasal verb",
                    "phrase": "phrase",
                    "idiom": "idiom",
                }
                pos = pos_map.get(pos_raw, pos_raw)

                # 2b. WordEntry (unique by vocab + pos)
                entry, e_created = WordEntry.objects.get_or_create(
                    vocab=vocab,
                    part_of_speech=pos,
                    defaults={
                        "ipa": w.get("ipa", ""),
                    },
                )
                if e_created:
                    entry_created += 1
                elif w.get("ipa") and not entry.ipa:
                    entry.ipa = w["ipa"]
                    entry.save(update_fields=["ipa"])

                # 2c. WordDefinition
                meaning = w.get("meaning", "").strip()
                if meaning:
                    defn, d_created = WordDefinition.objects.get_or_create(
                        entry=entry,
                        defaults={"meaning": meaning},
                    )
                    if d_created:
                        defn_created += 1

                total_words += 1

            # 3. M2M link: topic.vocabularies
            topic.vocabularies.set(vocab_ids)

        self.stdout.write(
            self.style.SUCCESS(
                f"Topics: {topics_created} created, {topics_updated} updated\n"
                f"  Vocabulary: {vocab_created} new\n"
                f"  WordEntry:  {entry_created} new\n"
                f"  WordDefn:   {defn_created} new\n"
                f"  Total words processed: {total_words}"
            )
        )
