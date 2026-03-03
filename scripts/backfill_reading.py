"""
Backfill extra_data.reading from WordEntry.ipa for all JP vocabulary.
Run with: python manage.py shell < scripts/backfill_reading.py
"""
from vocab.models import Vocabulary, WordEntry

updated = 0
skipped = 0

jp_vocabs = Vocabulary.objects.filter(language="jp")
print(f"Found {jp_vocabs.count()} JP vocab entries")

for v in jp_vocabs.iterator():
    # Get the first entry with non-empty ipa
    entry = WordEntry.objects.filter(vocab=v).exclude(ipa="").first()
    if not entry or not entry.ipa:
        skipped += 1
        continue

    extra = v.extra_data or {}
    if extra.get("reading"):
        # Already has reading
        skipped += 1
        continue

    extra["reading"] = entry.ipa
    v.extra_data = extra
    v.save(update_fields=["extra_data"])
    updated += 1
    if updated % 50 == 0:
        print(f"  Updated {updated} so far...")

print(f"\nDone! Updated: {updated}, Skipped: {skipped}")
