"""
TC-09: Choukai (Listening Exam) Tests.

Covers:
  - Choukai API: GET /exam/choukai, GET /exam/choukai/{slug}
  - ExamBook (CHOUKAI category): creation, question counting
  - ListeningConversation model: unique (template, toeic_part, order)
  - Template questions integration
"""

from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()
API = "/api/v1/exam"


def _create_choukai_book(title="Choukai N2", level="N2"):
    from exam.models import ExamBook
    return ExamBook.objects.create(
        title=title, level=level, category="CHOUKAI", is_active=True,
    )


def _create_choukai_template(book, title="Mondai 1", n_questions=3):
    from exam.models import ExamTemplate, ExamQuestion
    template = ExamTemplate.objects.create(
        book=book, title=title, level=book.level,
        category="CHOUKAI", is_active=True,
    )
    questions = []
    for i in range(1, n_questions + 1):
        q = ExamQuestion.objects.create(
            template=template, text=f"Choukai Q{i}",
            question_type="MCQ", correct_answer="1", order=i,
            data={"choices": [
                {"key": "1", "text": f"Choice A-{i}"},
                {"key": "2", "text": f"Choice B-{i}"},
                {"key": "3", "text": f"Choice C-{i}"},
            ]},
        )
        questions.append(q)
    return template, questions


# ===========================================================================
#  1. Choukai list API
# ===========================================================================
class ChoukaiListAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("choukai", "c@t.com", "pass1234")
        self.client.force_login(self.user)
        self.book = _create_choukai_book()
        self.template, self.questions = _create_choukai_template(self.book, n_questions=5)

    def test_choukai_list(self):
        resp = self.client.get(f"{API}/choukai")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data) >= 1)

    def test_choukai_book_has_question_count(self):
        resp = self.client.get(f"{API}/choukai")
        data = resp.json()
        book = next(b for b in data if b["title"] == "Choukai N2")
        self.assertEqual(book["question_count"], 5)

    def test_choukai_book_fields(self):
        resp = self.client.get(f"{API}/choukai")
        data = resp.json()
        book = data[0]
        self.assertIn("id", book)
        self.assertIn("title", book)
        self.assertIn("slug", book)
        self.assertIn("level", book)

    def test_non_choukai_books_excluded(self):
        """Only CHOUKAI category books should appear."""
        from exam.models import ExamBook
        ExamBook.objects.create(
            title="MOJI Book", level="N2", category="MOJI", is_active=True,
        )
        resp = self.client.get(f"{API}/choukai")
        data = resp.json()
        titles = [b["title"] for b in data]
        self.assertNotIn("MOJI Book", titles)


# ===========================================================================
#  2. Choukai detail API
# ===========================================================================
class ChoukaiDetailAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("chdetail", "cd@t.com", "pass1234")
        self.client.force_login(self.user)
        self.book = _create_choukai_book("Detail Book")
        self.template, self.questions = _create_choukai_template(
            self.book, title="Mondai 1", n_questions=4,
        )

    def test_detail_success(self):
        resp = self.client.get(f"{API}/choukai/{self.book.slug}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["title"], "Detail Book")

    def test_detail_has_mondai_groups(self):
        resp = self.client.get(f"{API}/choukai/{self.book.slug}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("mondai_groups", data)
        self.assertTrue(len(data["mondai_groups"]) >= 1)

    def test_total_questions(self):
        resp = self.client.get(f"{API}/choukai/{self.book.slug}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_questions"], 4)

    def test_mondai_group_has_qids(self):
        resp = self.client.get(f"{API}/choukai/{self.book.slug}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        group = data["mondai_groups"][0]
        self.assertIn("qids", group)
        self.assertIn("count", group)
        self.assertTrue(group["count"] >= 1)


# ===========================================================================
#  3. ListeningConversation model
# ===========================================================================
class ListeningConversationModelTests(TestCase):
    def setUp(self):
        self.book = _create_choukai_book("LC Book")
        self.template, _ = _create_choukai_template(self.book, n_questions=0)

    def test_create_conversation(self):
        from exam.models import ListeningConversation
        lc = ListeningConversation.objects.create(
            template=self.template, toeic_part="L3", order=1,
            audio="test/audio.mp3", transcript="Hello",
        )
        self.assertEqual(lc.toeic_part, "L3")
        self.assertEqual(lc.order, 1)

    def test_unique_template_part_order(self):
        from exam.models import ListeningConversation
        ListeningConversation.objects.create(
            template=self.template, toeic_part="L3", order=1,
            audio="test/a.mp3",
        )
        with self.assertRaises(IntegrityError):
            ListeningConversation.objects.create(
                template=self.template, toeic_part="L3", order=1,
                audio="test/b.mp3",
            )

    def test_different_parts_ok(self):
        from exam.models import ListeningConversation
        ListeningConversation.objects.create(
            template=self.template, toeic_part="L3", order=1,
            audio="test/a.mp3",
        )
        lc2 = ListeningConversation.objects.create(
            template=self.template, toeic_part="L4", order=1,
            audio="test/b.mp3",
        )
        self.assertIsNotNone(lc2.id)

    def test_str(self):
        from exam.models import ListeningConversation
        lc = ListeningConversation.objects.create(
            template=self.template, toeic_part="L3", order=2,
            audio="test/a.mp3",
        )
        self.assertIn("Conversation 2", str(lc))


# ===========================================================================
#  4. Multiple books & templates
# ===========================================================================
class MultipleChoukaiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("multi", "m@t.com", "pass1234")
        self.client.force_login(self.user)

    def test_multiple_books(self):
        b1 = _create_choukai_book("Book 1")
        b2 = _create_choukai_book("Book 2")
        _create_choukai_template(b1, n_questions=3)
        _create_choukai_template(b2, n_questions=5)
        resp = self.client.get(f"{API}/choukai")
        data = resp.json()
        self.assertTrue(len(data) >= 2)

    def test_question_count_per_book(self):
        b1 = _create_choukai_book("CountBook1")
        _create_choukai_template(b1, title="T1", n_questions=3)
        _create_choukai_template(b1, title="T2", n_questions=4)
        resp = self.client.get(f"{API}/choukai")
        data = resp.json()
        book = next(b for b in data if b["title"] == "CountBook1")
        self.assertEqual(book["question_count"], 7)  # 3 + 4
