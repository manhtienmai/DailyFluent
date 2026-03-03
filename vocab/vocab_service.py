"""
Vocab Word Service — manages the Vocabulary → WordEntry → WordDefinition chain.

Follows SOLID:
- SRP: Separates word creation/linking logic from API routing
- DRY: Reusable across save_highlight, kanji add_to_study, etc.

Previously this logic was an 88-line God Method in vocab/api.py save_highlight().
"""

from django.db import transaction


class VocabWordService:
    """
    Manages the Vocabulary chain creation and linking to user study sets.
    """

    @staticmethod
    def save_or_create_word(
        user,
        word: str,
        language: str = "jp",
        reading: str = "",
        meaning_vi: str = "",
        han_viet: str = "",
        context_sentence: str = "",
        set_title: str = "Từ đã đánh dấu",
        set_description: str = "Từ vựng được đánh dấu từ bài luyện tập",
        create_fsrs: bool = True,
    ) -> dict:
        """
        Create or get a word through the full Vocabulary chain,
        add it to a user's study set, and optionally create an FSRS card.

        Steps:
          1. Get/create Vocabulary
          2. Get/create WordEntry
          3. Get/create WordDefinition
          4. Add context sentence as ExampleSentence (if provided)
          5. Get/create user's study VocabularySet
          6. Add SetItem (avoid duplicates)
          7. Create FsrsCardStateEn (if create_fsrs=True)
          8. Store han_viet in extra_data (if provided)

        Returns:
            dict with success, word, meaning, set_id, is_new
        """
        from vocab.models import (
            Vocabulary,
            WordEntry,
            WordDefinition,
            ExampleSentence,
            VocabularySet,
            SetItem,
            FsrsCardStateEn,
        )

        word_text = word.strip()
        if not word_text:
            return {"error": "Word is empty"}

        with transaction.atomic():
            # 1. Vocabulary
            vocab, _ = Vocabulary.objects.get_or_create(
                word=word_text,
                defaults={"language": language},
            )

            # 2. WordEntry
            entry, _ = WordEntry.objects.get_or_create(
                vocab=vocab,
                part_of_speech="",
                defaults={"ipa": reading},
            )
            if reading and not entry.ipa:
                entry.ipa = reading
                entry.save(update_fields=["ipa"])

            # 3. WordDefinition
            meaning = meaning_vi or f"({word_text})"
            defn, _ = WordDefinition.objects.get_or_create(
                entry=entry,
                defaults={"meaning": meaning},
            )
            if meaning_vi and defn.meaning == f"({word_text})":
                defn.meaning = meaning_vi
                defn.save(update_fields=["meaning"])

            # 4. Context sentence
            if context_sentence.strip():
                ExampleSentence.objects.get_or_create(
                    definition=defn,
                    sentence=context_sentence.strip(),
                    defaults={"source": "user", "translation": ""},
                )

            # 5. User's study set
            study_set, _ = VocabularySet.objects.get_or_create(
                owner=user,
                title=set_title,
                defaults={
                    "language": language,
                    "status": "published",
                    "description": set_description,
                },
            )

            # 6. SetItem
            set_item, created_item = SetItem.objects.get_or_create(
                vocabulary_set=study_set,
                definition=defn,
            )

            # 7. FSRS card
            if create_fsrs:
                FsrsCardStateEn.objects.get_or_create(
                    user=user,
                    vocab=vocab,
                    defaults={"state": 0},  # New
                )

            # 8. Han Viet metadata
            if han_viet:
                extra = vocab.extra_data or {}
                extra["han_viet"] = han_viet
                vocab.extra_data = extra
                vocab.save(update_fields=["extra_data"])

        return {
            "success": True,
            "word": word_text,
            "meaning": defn.meaning,
            "set_id": study_set.id,
            "is_new": created_item,
        }
