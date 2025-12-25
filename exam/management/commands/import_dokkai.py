import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from exam.models import (
    ExamBook,
    ExamTemplate,
    ReadingPassage,
    ExamQuestion,
    ExamLevel,
    ExamCategory,
    ExamGroupType,
    QuestionType,
)


class Command(BaseCommand):
    help = "Import dokkai exam data (ReadingPassage + ExamQuestion PARAGRAPH) from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Path to the dokkai JSON file (e.g. exam/data/power_dokkai_n3.json)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse file and show summary without writing to database",
        )

        parser.add_argument(
            "--update-existing",
            action="store_true",
            help=(
                "If set, existing passages/questions will be UPDATED instead of only skipping "
                "them. New ones are still created as usual."
            ),
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])
        dry_run = options["dry_run"]
        update_existing = options["update_existing"]

        if not json_path.exists():
            raise CommandError(f"File not found: {json_path}")

        self.stdout.write(self.style.NOTICE(f"Loading file: {json_path}"))

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate main structure
        if "book" not in data or "templates" not in data:
            raise CommandError("JSON must contain 'book' and 'templates' keys")

        book_data = data["book"]
        templates_data = data["templates"]

        if not isinstance(templates_data, list) or not templates_data:
            raise CommandError("'templates' must be a non-empty list")

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY RUN mode (no DB writes)."))
        if update_existing:
            self.stdout.write(self.style.WARNING("UPDATE EXISTING mode enabled."))

        with transaction.atomic():
            book = self._create_or_get_book(book_data, dry_run=dry_run)
            self._import_templates(
                book,
                templates_data,
                dry_run=dry_run,
                update_existing=update_existing,
            )

            if dry_run:
                self.stdout.write(self.style.WARNING("Dry run completed. Rolling back transaction."))
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("Done."))

    # ---------------------------
    # Helpers
    # ---------------------------

    def _create_or_get_book(self, book_data: dict, dry_run: bool) -> ExamBook:
        """
        Book: get_or_create theo title.
        - Nếu chưa có → tạo mới
        - Nếu đã có   → cập nhật level/category/description/total_lessons
        """
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
            # update basic fields if exist
            book.level = level
            book.category = category
            book.description = description
            book.total_lessons = total_lessons
            if not dry_run:
                book.save()

        msg = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{msg} ExamBook: {book.title} (id={book.id})"))
        return book

    def _import_templates(self, book: ExamBook, templates_data: list, dry_run: bool, update_existing: bool):
        for idx, tmpl_data in enumerate(templates_data, start=1):
            self.stdout.write(self.style.NOTICE(f"Importing template #{idx}: {tmpl_data.get('title')}"))

            template = self._create_template(book, tmpl_data, dry_run=dry_run)
            # Map passage_order -> ReadingPassage
            passage_map = self._create_passages(
                template,
                tmpl_data.get("passages", []),
                dry_run=dry_run,
                update_existing=update_existing,
            )
            self._create_questions(
                template,
                passage_map,
                tmpl_data.get("questions", []),
                dry_run=dry_run,
                update_existing=update_existing,
            )

    def _create_template(self, book: ExamBook, tmpl_data: dict, dry_run: bool) -> ExamTemplate:
        """
        Template: get_or_create theo (book, title).
        - Nếu đã có → update meta (level/category/description/...)
        """
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
        main_question_type = tmpl_data.get("main_question_type", QuestionType.PARAGRAPH)
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
        self.stdout.write(self.style.SUCCESS(f"{msg} ExamTemplate: {template} (id={template.id})"))
        return template

    def _create_passages(self, template: ExamTemplate, passages_data: list, dry_run: bool, update_existing: bool):
        """
        Chỉ tạo passage mới nếu (template, order) chưa tồn tại.
        Nếu đã có thì:
        - Mặc định: reuse, KHÔNG chỉnh sửa text/title/data
        - Nếu --update-existing: update nội dung passage theo JSON

        Nếu DB đã lỡ có nhiều passage cùng (template, order),
        sẽ lấy bản earliest (id nhỏ nhất) làm chuẩn.
        """
        passage_map = {}

        for p_data in passages_data:
            order = p_data.get("order")
            if order is None:
                raise CommandError("Each passage must have 'order'")

            title = p_data.get("title", "")
            text = p_data.get("text") or ""
            extra_data = p_data.get("data", {}) or {}

            qs = ReadingPassage.objects.filter(template=template, order=order).order_by("id")
            if qs.exists():
                passage = qs.first()
                if qs.count() > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Found {qs.count()} passages for (template={template.id}, order={order}), "
                            f"using id={passage.id}"
                        )
                    )

                if update_existing:
                    passage.title = title
                    passage.text = text
                    passage.data = extra_data
                    if not dry_run:
                        passage.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Updated existing Passage order={order} id={passage.id}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Reuse existing Passage order={order} id={passage.id}"
                        )
                    )
            else:
                passage = ReadingPassage(
                    template=template,
                    order=order,
                    title=title,
                    text=text,
                    data=extra_data,
                )
                if not dry_run:
                    passage.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created Passage order={order} id={passage.id if not dry_run else 'dry'}"
                    )
                )

            passage_map[order] = passage

        return passage_map

    def _create_questions(
        self,
        template: ExamTemplate,
        passage_map: dict,
        questions_data: list,
        dry_run: bool,
        update_existing: bool,
    ):
        """
        Câu hỏi:
        - Mặc định (không --update-existing):
            + Nếu đã tồn tại (theo key) -> SKIP, không sửa.
            + Nếu chưa tồn tại -> CREATE.
        - Nếu có --update-existing:
            + Nếu đã tồn tại -> UPDATE fields theo JSON.
            + Nếu chưa có -> CREATE.

        Key nhận diện:
        - Nếu có 'mondai': (template, mondai, order_in_mondai)
        - Nếu không mondai: (template, order)

        Nếu DB đã lỡ có nhiều question cùng key -> chọn bản earliest (id nhỏ nhất).
        """
        for q_data in questions_data:
            order = q_data.get("order")
            if order is None:
                raise CommandError("Each question must have 'order'")

            qtype = q_data.get("question_type", QuestionType.MCQ)
            if qtype not in QuestionType.values:
                raise CommandError(f"Invalid question_type: {qtype}")

            passage_order = q_data.get("passage_order")
            passage = passage_map.get(passage_order) if passage_order is not None else None

            text = q_data.get("text") or ""
            data = q_data.get("data", {}) or {}
            correct_answer = str(q_data.get("correct_answer", "")).strip()

            if not correct_answer:
                raise CommandError(f"Question order={order} is missing 'correct_answer'")

            source = q_data.get("source", "")
            mondai = q_data.get("mondai", "")
            order_in_mondai = q_data.get("order_in_mondai", order)

            # ===== Check tồn tại hay chưa =====
            filters = {"template": template}
            if mondai:
                filters["mondai"] = mondai
                filters["order_in_mondai"] = order_in_mondai
                key_desc = f"mondai={mondai}, order_in_mondai={order_in_mondai}"
            else:
                filters["order"] = order
                key_desc = f"order={order}"

            qs = ExamQuestion.objects.filter(**filters).order_by("id")

            if qs.exists():
                existing_q = qs.first()
                if qs.count() > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Found {qs.count()} questions for ({key_desc}), using id={existing_q.id}"
                        )
                    )

                if not update_existing:
                    # Đã tồn tại: skip
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Skip existing Question ({key_desc}) id={existing_q.id}"
                        )
                    )
                    continue

                # --update-existing: cập nhật nội dung
                existing_q.passage = passage
                existing_q.order = order
                existing_q.question_type = qtype
                existing_q.text = text
                existing_q.data = data
                existing_q.correct_answer = correct_answer
                existing_q.source = source
                existing_q.mondai = mondai
                existing_q.order_in_mondai = order_in_mondai

                if not dry_run:
                    existing_q.save()

                self.stdout.write(
                    self.style.WARNING(
                        f"  Updated existing Question ({key_desc}) id={existing_q.id}"
                    )
                )
                continue

            # ===== Tạo câu hỏi mới =====
            question = ExamQuestion(
                template=template,
                passage=passage,
                order=order,
                question_type=qtype,
                text=text,
                data=data,
                correct_answer=correct_answer,
                source=source,
                mondai=mondai,
                order_in_mondai=order_in_mondai,
            )

            if not dry_run:
                question.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Created Question {key_desc} "
                    f"(passage_order={passage_order}) id={question.id if not dry_run else 'dry'}"
                )
            )
