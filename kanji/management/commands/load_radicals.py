"""
Management command: load all 214 Kangxi Radicals (Bộ thủ).

Usage:
    python manage.py load_radicals
"""
from django.core.management.base import BaseCommand

from kanji.admin import _import_kanji_json
from kanji.models import KanjiLesson, Kanji, KanjiVocab

from .radicals_data import (
    RADICALS_1, RADICALS_2, RADICALS_3A, RADICALS_3B,
    RADICALS_4A, RADICALS_4B, RADICALS_5,
)
from .radicals_data2 import (
    RADICALS_6, RADICALS_7, RADICALS_8, RADICALS_9, RADICALS_10_17,
)

BT_DATA = [
  {"jlpt_level": "BT", "lesson_id": 1, "topic": "1 nét", "kanji_list": RADICALS_1},
  {"jlpt_level": "BT", "lesson_id": 2, "topic": "2 nét", "kanji_list": RADICALS_2},
  {"jlpt_level": "BT", "lesson_id": 3, "topic": "3 nét (phần 1)", "kanji_list": RADICALS_3A},
  {"jlpt_level": "BT", "lesson_id": 4, "topic": "3 nét (phần 2)", "kanji_list": RADICALS_3B},
  {"jlpt_level": "BT", "lesson_id": 5, "topic": "4 nét (phần 1)", "kanji_list": RADICALS_4A},
  {"jlpt_level": "BT", "lesson_id": 6, "topic": "4 nét (phần 2)", "kanji_list": RADICALS_4B},
  {"jlpt_level": "BT", "lesson_id": 7, "topic": "5 nét", "kanji_list": RADICALS_5},
  {"jlpt_level": "BT", "lesson_id": 8, "topic": "6 nét", "kanji_list": RADICALS_6},
  {"jlpt_level": "BT", "lesson_id": 9, "topic": "7 nét", "kanji_list": RADICALS_7},
  {"jlpt_level": "BT", "lesson_id": 10, "topic": "8 nét", "kanji_list": RADICALS_8},
  {"jlpt_level": "BT", "lesson_id": 11, "topic": "9 nét", "kanji_list": RADICALS_9},
  {"jlpt_level": "BT", "lesson_id": 12, "topic": "10-17 nét", "kanji_list": RADICALS_10_17},
]


class Command(BaseCommand):
    help = "Load all 214 Kangxi Radicals (Bộ thủ)"

    def handle(self, *args, **options):
        self.stdout.write("Loading 214 Radicals (Bo thu)...")
        stats = _import_kanji_json(BT_DATA, replace=True)
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created:\n"
            f"  - {stats['lessons']} lessons\n"
            f"  - {stats['kanji']} radicals\n"
            f"  - {stats['vocab']} vocab examples\n"
        ))
