import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from exam.models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamLevel,
    ExamCategory,
    ExamGroupType,
    QuestionType,
)


class Command(BaseCommand):
    help = "Import choukai exam data (ExamQuestion + audio) from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Path to the choukai JSON file (e.g. exam/data/choukai_n3_sample.json)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse file and show summary without writing to database",
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_path"]).resolve()
        dry_run = options["dry_run"]

        if not json_path.exists():
            raise CommandError(f"File not found: {json_path}")

        self.base_dir = json_path.parent  # dùng để resolve audio_file

        self.stdout.write(self.style.NOTICE(f"Loading file: {json_path}"))

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "book" not in data or "templates" not in data:
            raise CommandError("JSON must contain 'book' and 'templates' keys")

        book_data = data["book"]
        templates_data = data["templates"]

        if not isinstance(templates_data, list) or not templates_data:
            raise CommandError("'templates' must be a non-empty list")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY RUN mode (no DB writes).")
            )

        with transaction.atomic():
            book = self._create_or_get_book(book_data, dry_run=dry_run)
            self._import_templates(book, templates_data, dry_run=dry_run)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "Dry run completed. Rolling back transaction."
                    )
                )
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("Done."))

    # ---------------------------
    # Helpers
    # ---------------------------

    def _create_or_get_book(self, book_data: dict, dry_run: bool) -> ExamBook:
        title = book_data.get("title")
        level = book_data.get("level")
        category = book_data.get("category")

        if not title or not level or not category:
            raise CommandError("book.title, book.level, book.category are required")

        if level not in ExamLevel.values:
            raise CommandError(f"Invalid book.level: {level}")
        if category not in ExamCategory.values:
            raise CommandError(f"Invalid book.category: {category}")

        description = book_data.get("description", "")
        total_lessons = book_data.get("total_lessons", 0)

        book, created = ExamBook.objects.get_or_create(
            title=title,
            defaults={
                "level": level,
                "category": category,
                "description": description,
                "total_lessons": total_lessons,
            },
        )

        if not created:
            book.level = level
            book.category = category
            book.description = description
            book.total_lessons = total_lessons
            if not dry_run:
                book.save()

        msg = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{msg} ExamBook: {book.title} (id={book.id})")
        )
        return book

    def _import_templates(self, book: ExamBook, templates_data: list, dry_run: bool):
        for idx, tmpl_data in enumerate(templates_data, start=1):
            self.stdout.write(
                self.style.NOTICE(
                    f"Importing template #{idx}: {tmpl_data.get('title')}"
                )
            )
            template = self._create_template(book, tmpl_data, dry_run=dry_run)
            self._create_questions(template, tmpl_data.get("questions", []), dry_run)

    def _create_template(self, book: ExamBook, tmpl_data: dict, dry_run: bool) -> ExamTemplate:
        title = tmpl_data.get("title")
        level = tmpl_data.get("level") or book.level
        category = tmpl_data.get("category") or book.category

        if not title:
            raise CommandError("template.title is required")

        if level not in ExamLevel.values:
            raise CommandError(f"Invalid template.level: {level}")
        if category not in ExamCategory.values:
            raise CommandError(f"Invalid template.category: {category}")

        description = tmpl_data.get("description", "")
        group_type = tmpl_data.get("group_type", ExamGroupType.STANDALONE)
        lesson_index = tmpl_data.get("lesson_index", 1)
        subtitle = tmpl_data.get("subtitle", "")
        main_question_type = tmpl_data.get("main_question_type", QuestionType.MCQ)
        time_limit_minutes = tmpl_data.get("time_limit_minutes")

        if group_type not in ExamGroupType.values:
            raise CommandError(f"Invalid group_type: {group_type}")

        template, created = ExamTemplate.objects.get_or_create(
            book=book,
            title=title,
            defaults={
                "description": description,
                "level": level,
                "category": category,
                "group_type": group_type,
                "lesson_index": lesson_index,
                "subtitle": subtitle,
                "main_question_type": main_question_type,
                "time_limit_minutes": time_limit_minutes,
            },
        )

        if not created:
            template.description = description
            template.level = level
            template.category = category
            template.group_type = group_type
            template.lesson_index = lesson_index
            template.subtitle = subtitle
            template.main_question_type = main_question_type
            template.time_limit_minutes = time_limit_minutes
            if not dry_run:
                template.save()

        msg = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{msg} ExamTemplate: {template} (id={template.id})")
        )
        return template

    def _create_questions(self, template: ExamTemplate, questions_data: list, dry_run: bool):
        if not questions_data:
            self.stdout.write(self.style.WARNING("  No questions in template."))
            return

        for q_data in questions_data:
            order = q_data.get("order")
            if order is None:
                raise CommandError("Each question must have 'order'")

            qtype = q_data.get("question_type", QuestionType.MCQ)
            if qtype not in QuestionType.values:
                raise CommandError(f"Invalid question_type: {qtype}")

            text = q_data.get("text") or ""
            data = q_data.get("data", {}) or {}
            correct_answer = str(q_data.get("correct_answer", "")).strip()
            if not correct_answer:
                raise CommandError(
                    f"Question order={order} is missing 'correct_answer'"
                )

            source = q_data.get("source", "")
            mondai = q_data.get("mondai", "")
            order_in_mondai = q_data.get("order_in_mondai", order)

            audio_meta = q_data.get("audio_meta", {}) or {}
            audio_file_rel = q_data.get("audio_file")

            question = ExamQuestion(
                template=template,
                order=order,
                question_type=qtype,
                text=text,
                data=data,
                correct_answer=correct_answer,
                source=source,
                mondai=mondai,
                order_in_mondai=order_in_mondai,
                audio_meta=audio_meta,
            )

        
            if not dry_run:
                question.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Question order={order} "
                    f"id={question.id if not dry_run else 'dry'} "
                    f"(audio={'yes' if audio_file_rel else 'no'})"
                )
            )
