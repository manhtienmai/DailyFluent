"""
Management command: load EN10 Exam data (đề thi Tiếng Anh vào lớp 10).

Scans exam/fixtures/ for files matching 'en10_de_so_*.json' and creates:
  - 1 ExamBook  (level=EN10, "Đề thi Tiếng Anh vào lớp 10")
  - 1 ExamTemplate per fixture file
  - N ExamQuestion per template (from sections → questions)

Also loads matching review files (en10_de_so_*_review.json) into
the template's `data` field under key 'review_items'.

Usage:
    python manage.py load_en10_exam              # load all en10_de_so_*.json
    python manage.py load_en10_exam --clear       # clear existing EN10 exams first
"""

import json
import glob
import re
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load EN10 exam fixtures (đề thi Tiếng Anh vào lớp 10) into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing EN10 exam data before loading",
        )

    def handle(self, *args, **options):
        from exam.models import (
            ExamBook, ExamTemplate, ExamQuestion,
            ExamLevel, ExamCategory, ExamGroupType, QuestionType,
        )

        fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"

        # Find all exam fixture files (exclude _review files)
        exam_files = sorted(
            f for f in fixtures_dir.glob("en10_de_so_*.json")
            if "_review" not in f.name
        )

        if not exam_files:
            self.stdout.write(self.style.ERROR(
                f"No EN10 exam fixtures found in {fixtures_dir}"
            ))
            return

        self.stdout.write(f"Found {len(exam_files)} exam fixture(s)")

        # Get or create the ExamBook for EN10
        book, book_created = ExamBook.objects.get_or_create(
            slug="tieng-anh-vao-lop-10",
            defaults={
                "title": "Đề thi Tiếng Anh vào lớp 10",
                "level": ExamLevel.EN10,
                "is_active": True,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"ExamBook: {'created' if book_created else 'exists'} — {book.title}"
            )
        )

        if options["clear"]:
            # Delete existing templates (cascade deletes questions)
            deleted, _ = ExamTemplate.objects.filter(
                book=book, level=ExamLevel.EN10
            ).delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {deleted} existing EN10 exam objects")
            )

        total_templates = 0
        total_questions = 0

        for exam_file in exam_files:
            with open(exam_file, "r", encoding="utf-8") as f:
                exam_data = json.load(f)

            title = exam_data.get("title", exam_file.stem)
            description = exam_data.get("description", "")
            time_limit = exam_data.get("time_limit_minutes", 60)
            sections = exam_data.get("sections", [])

            # Extract lesson index from filename: en10_de_so_1.json → 1
            match = re.search(r"en10_de_so_(\d+)", exam_file.stem)
            lesson_idx = int(match.group(1)) if match else 1

            # Create or update ExamTemplate
            template, t_created = ExamTemplate.objects.update_or_create(
                book=book,
                lesson_index=lesson_idx,
                level=ExamLevel.EN10,
                category=ExamCategory.ENGLISH,
                defaults={
                    "title": title,
                    "description": description,
                    "time_limit_minutes": time_limit,
                    "group_type": ExamGroupType.STANDALONE,
                    "main_question_type": QuestionType.MCQ,
                    "is_active": True,
                    "is_public": False,
                },
            )

            # Load review data if exists
            review_file = fixtures_dir / f"{exam_file.stem}_review.json"
            if review_file.exists():
                with open(review_file, "r", encoding="utf-8") as f:
                    review_data = json.load(f)
                template.data = template.data or {}
                template.data["review_items"] = review_data.get("items", [])
                template.save(update_fields=["data"])
                self.stdout.write(
                    f"  → Loaded {len(review_data.get('items', []))} review items"
                )

            # Delete existing questions for this template (idempotent reload)
            if not t_created:
                template.questions.all().delete()

            # Create questions from sections
            q_order = 0
            for section in sections:
                section_type = section.get("type", "")
                section_title = section.get("title", "")
                passage_text = section.get("passage_text", "")

                for q in section.get("questions", []):
                    q_order += 1
                    choices = q.get("choices", [])
                    correct = q.get("correct_answer", "")
                    explanation = q.get("explanation_json", {})

                    ExamQuestion.objects.create(
                        template=template,
                        order=q_order,
                        question_type=QuestionType.MCQ,
                        text=q.get("text", ""),
                        correct_answer=correct,
                        explanation_json=explanation,
                        data={
                            "choices": choices,
                            "section_type": section_type,
                            "section_title": section_title,
                            "passage_text": passage_text if passage_text else None,
                            "question_num": q.get("num"),
                        },
                    )

            total_templates += 1
            total_questions += q_order

            action = "created" if t_created else "updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {action}: {title} — {q_order} questions"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nEN10 Exam data loaded: {total_templates} templates, "
                f"{total_questions} questions total"
            )
        )
