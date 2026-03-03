"""Link all KanjiVocab to Vocabulary records."""
from django.core.management.base import BaseCommand
from kanji.models import KanjiVocab
from vocab.models import Vocabulary, WordEntry, WordDefinition


class Command(BaseCommand):
    help = "Link all KanjiVocab to Vocabulary records"

    def handle(self, *args, **options):
        linked = 0
        for kv in KanjiVocab.objects.filter(vocabulary=None):
            vocab_obj, _ = Vocabulary.objects.get_or_create(
                word=kv.word,
                defaults={'language': 'jp', 'extra_data': {'reading': kv.reading}},
            )
            entry, _ = WordEntry.objects.get_or_create(
                vocab=vocab_obj, part_of_speech='',
                defaults={'ipa': kv.reading},
            )
            WordDefinition.objects.get_or_create(
                entry=entry, meaning=kv.meaning,
            )
            kv.vocabulary = vocab_obj
            kv.save(update_fields=['vocabulary'])
            linked += 1
        self.stdout.write(self.style.SUCCESS(f"Linked {linked} KanjiVocab to Vocabulary"))
