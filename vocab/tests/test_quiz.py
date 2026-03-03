"""
TC-08: Quiz & Games Generation Tests.

Covers:
  - QuizQuestion model: unique (set_item, question_type), distractors
  - Quiz API: GET /vocab/courses/{slug}/set/{n}/quiz
  - MCQ generation logic: distractor selection, edge cases
  - VocabularySet → SetItem → WordDefinition chain
"""

import json
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()
API = "/api/v1/vocab"


# ===========================================================================
# Helpers to build vocab chain
# ===========================================================================
def _build_vocab_chain(word, meaning, pos="noun"):
    """Create Vocabulary → WordEntry → WordDefinition chain."""
    from vocab.models import Vocabulary, WordEntry, WordDefinition
    vocab, _ = Vocabulary.objects.get_or_create(word=word, defaults={"language": "en"})
    entry, _ = WordEntry.objects.get_or_create(vocab=vocab, part_of_speech=pos, defaults={"ipa": "/test/"})
    defn, _ = WordDefinition.objects.get_or_create(entry=entry, defaults={"meaning": meaning})
    return vocab, entry, defn


def _create_quiz_source(code="test_source", n_words=5):
    """Create VocabSource + VocabularySet + SetItems with N words."""
    from vocab.models import VocabSource, VocabularySet, SetItem

    source, _ = VocabSource.objects.get_or_create(
        code=code, defaults={"name": "Test Source", "source_type": "course"}
    )
    vset = VocabularySet.objects.create(
        collection=source, title="Set 1", set_number=1,
        status="published", language="en",
    )
    items = []
    for i in range(1, n_words + 1):
        _, _, defn = _build_vocab_chain(f"word{i}_{code}", f"nghĩa {i}")
        item = SetItem.objects.create(vocabulary_set=vset, definition=defn, display_order=i)
        items.append(item)
    return source, vset, items


# ===========================================================================
#  1. QuizQuestion model
# ===========================================================================
class QuizQuestionModelTests(TestCase):
    def setUp(self):
        self.source, self.vset, self.items = _create_quiz_source("qq_model", n_words=3)

    def test_create_quiz_question(self):
        from vocab.models import QuizQuestion
        qq = QuizQuestion.objects.create(
            set_item=self.items[0],
            question_type="meaning",
            correct_answer="nghĩa 1",
            distractors=["wrong1", "wrong2", "wrong3"],
        )
        self.assertEqual(qq.correct_answer, "nghĩa 1")
        self.assertEqual(len(qq.distractors), 3)

    def test_unique_set_item_question_type(self):
        from django.db import IntegrityError
        from vocab.models import QuizQuestion
        QuizQuestion.objects.create(
            set_item=self.items[0], question_type="meaning",
            correct_answer="a", distractors=[],
        )
        with self.assertRaises(IntegrityError):
            QuizQuestion.objects.create(
                set_item=self.items[0], question_type="meaning",
                correct_answer="b", distractors=[],
            )

    def test_different_types_ok(self):
        from vocab.models import QuizQuestion
        QuizQuestion.objects.create(
            set_item=self.items[0], question_type="meaning",
            correct_answer="a", distractors=[],
        )
        qq2 = QuizQuestion.objects.create(
            set_item=self.items[0], question_type="reading",
            correct_answer="b", distractors=[],
        )
        self.assertIsNotNone(qq2.id)


# ===========================================================================
#  2. Quiz API — basic flow
# ===========================================================================
class QuizAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("quizuser", "q@t.com", "pass1234")
        self.client.force_login(self.user)
        self.source, self.vset, self.items = _create_quiz_source("quiz_api", n_words=6)

    def test_get_quiz_returns_questions(self):
        resp = self.client.get(f"{API}/courses/{self.source.code}/set/1/quiz")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("questions", data)
        self.assertEqual(len(data["questions"]), 6)

    def test_quiz_has_correct_answer(self):
        resp = self.client.get(f"{API}/courses/{self.source.code}/set/1/quiz")
        data = resp.json()
        for q in data["questions"]:
            self.assertIn("correct_answer", q)
            self.assertIn(q["correct_answer"], q["choices"])

    def test_quiz_has_choices(self):
        resp = self.client.get(f"{API}/courses/{self.source.code}/set/1/quiz")
        data = resp.json()
        for q in data["questions"]:
            self.assertTrue(len(q["choices"]) >= 2)

    def test_quiz_correct_answer_in_choices(self):
        resp = self.client.get(f"{API}/courses/{self.source.code}/set/1/quiz")
        data = resp.json()
        for q in data["questions"]:
            self.assertIn(q["correct_answer"], q["choices"])


# ===========================================================================
#  3. Quiz edge cases
# ===========================================================================
class QuizEdgeCaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("edgeuser", "edge@t.com", "pass1234")
        self.client.force_login(self.user)

    def test_small_set_still_works(self):
        """A set with < 4 words should still generate quiz (fewer distractors)."""
        source, vset, items = _create_quiz_source("small_set", n_words=2)
        resp = self.client.get(f"{API}/courses/{source.code}/set/1/quiz")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["questions"]), 2)
        # Should have choices even if < 4
        for q in data["questions"]:
            self.assertTrue(len(q["choices"]) >= 1)

    def test_empty_set(self):
        """A set with 0 words should return empty questions."""
        source, vset, items = _create_quiz_source("empty_set", n_words=0)
        resp = self.client.get(f"{API}/courses/{source.code}/set/1/quiz")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["questions"]), 0)


# ===========================================================================
#  4. Vocab chain integrity
# ===========================================================================
class VocabChainTests(TestCase):
    """Test the Vocabulary → WordEntry → WordDefinition → SetItem chain."""

    def test_full_chain(self):
        from vocab.models import Vocabulary, WordEntry, WordDefinition
        vocab, entry, defn = _build_vocab_chain("example", "ví dụ", "noun")
        self.assertEqual(vocab.word, "example")
        self.assertEqual(entry.part_of_speech, "noun")
        self.assertEqual(defn.meaning, "ví dụ")

    def test_set_item_links_to_definition(self):
        source, vset, items = _create_quiz_source("chain_test", n_words=3)
        item = items[0]
        self.assertIsNotNone(item.definition)
        self.assertIsNotNone(item.definition.entry)
        self.assertIsNotNone(item.definition.entry.vocab)

    def test_set_item_meaning_accessible(self):
        source, vset, items = _create_quiz_source("meaning_test", n_words=2)
        meanings = [item.definition.meaning for item in items]
        self.assertEqual(len(meanings), 2)

    def test_word_entry_unique(self):
        """WordEntry is unique on (vocab, part_of_speech)."""
        from django.db import IntegrityError
        from vocab.models import Vocabulary, WordEntry
        vocab = Vocabulary.objects.create(word="unique_test")
        WordEntry.objects.create(vocab=vocab, part_of_speech="noun")
        with self.assertRaises(IntegrityError):
            WordEntry.objects.create(vocab=vocab, part_of_speech="noun")
