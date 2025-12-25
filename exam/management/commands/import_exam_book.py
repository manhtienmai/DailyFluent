# exam/management/commands/import_exam_book.py
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

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
    help = "Import 1 exam book (book + day tests + questions + pattern tests) từ file JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Đường dẫn tới file JSON (ví dụ: exam/data/power_mojigoi_n2.json)",
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])

        if not json_path.exists():
            raise CommandError(f"File không tồn tại: {json_path}")

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"Lỗi JSON: {e}")

        book_data = data.get("book")
        days = data.get("days", [])
        patterns = data.get("patterns", [])

        if not book_data:
            raise CommandError("File JSON thiếu key 'book'")

        # Lấy max_length slug để tránh lỗi DataError (value too long for type character varying)
        book_slug_field = ExamBook._meta.get_field("slug")
        tmpl_slug_field = ExamTemplate._meta.get_field("slug")
        max_book_slug_len = book_slug_field.max_length or 50
        max_tmpl_slug_len = tmpl_slug_field.max_length or 50

        def make_slug(base: str, max_len: int) -> str:
            s = slugify(base) or "item"
            return s[:max_len]

        with transaction.atomic():
            # ============ 1) Book ============
            book_title = book_data.get("title")
            if not book_title:
                raise CommandError("Book thiếu 'title'")

            raw_book_slug = book_data.get("slug") or book_title
            book_slug = make_slug(raw_book_slug, max_book_slug_len)

            level = book_data.get("level")
            if level and level not in dict(ExamLevel.choices):
                raise CommandError(
                    f"Level '{level}' không hợp lệ. Hợp lệ: {list(dict(ExamLevel.choices).keys())}"
                )

            category = book_data.get("category")
            if category and category not in dict(ExamCategory.choices):
                raise CommandError(
                    f"Category '{category}' không hợp lệ. Hợp lệ: {list(dict(ExamCategory.choices).keys())}"
                )

            book_defaults = {
                "title": book_title,
                "level": level or ExamLevel.N2,
                "category": category or ExamCategory.MOJIGOI,
                "description": book_data.get("description", ""),
                "total_lessons": book_data.get("total_lessons", 0),
                "is_active": book_data.get("is_active", True),
            }

            book, _ = ExamBook.objects.update_or_create(
                slug=book_slug,
                defaults=book_defaults,
            )

            self.stdout.write(
                self.style.SUCCESS(f"📘 Book: {book.title} (slug={book.slug})")
            )

            # ============ 2) DAY TESTS (group_type=DAY) ============
            total_day_templates = 0

            for day in days:
                questions = day.get("questions", [])
                if not questions:
                    continue

                day_number = day.get("day")
                tmpl_title = day.get("title") or (
                    f"DAY {day_number:02d}" if isinstance(day_number, int) else "No title"
                )

                raw_tmpl_slug = day.get("slug") or f"{book.slug}-{tmpl_title}"
                tmpl_slug = make_slug(raw_tmpl_slug, max_tmpl_slug_len)

                group_type = day.get("group_type") or ExamGroupType.BY_DAY
                if group_type not in dict(ExamGroupType.choices):
                    raise CommandError(
                        f"group_type '{group_type}' không hợp lệ. "
                        f"Hợp lệ: {list(dict(ExamGroupType.choices).keys())}"
                    )

                lesson_index = day.get("lesson_index") or (day_number or 1)
                time_limit = day.get("time_limit_minutes")
                main_q_type = day.get("main_question_type") or QuestionType.MCQ
                if main_q_type not in dict(QuestionType.choices):
                    raise CommandError(
                        f"main_question_type '{main_q_type}' không hợp lệ. "
                        f"Hợp lệ: {list(dict(QuestionType.choices).keys())}"
                    )

                tmpl_defaults = {
                    "book": book,
                    "title": tmpl_title,
                    "description": day.get("description", ""),
                    "level": book.level,
                    "category": book.category,
                    "group_type": group_type,
                    "lesson_index": lesson_index,
                    "subtitle": day.get("subtitle", ""),
                    "main_question_type": main_q_type,
                    "time_limit_minutes": time_limit,
                    "is_active": day.get("is_active", True),
                }

                template, _ = ExamTemplate.objects.update_or_create(
                    slug=tmpl_slug,
                    defaults=tmpl_defaults,
                )

                created_q = 0
                updated_q = 0

                for q in questions:
                    order = q.get("order")
                    if order is None:
                        raise CommandError(
                            f"Một câu hỏi thiếu 'order' trong day '{tmpl_slug}'"
                        )

                    # Cho phép JSON truyền thêm 'data' (vd: passage cho Dokkai)
                    data_payload = q.get("data", {}) or {}

                    choices = q.get("choices", [])
                    if choices:
                        choices_payload = [
                            {"key": str(idx + 1), "text": text}
                            for idx, text in enumerate(choices)
                        ]
                        data_payload["choices"] = choices_payload

                    question_type = q.get("question_type", main_q_type)
                    if question_type not in dict(QuestionType.choices):
                        raise CommandError(
                            f"question_type '{question_type}' không hợp lệ. "
                            f"Hợp lệ: {list(dict(QuestionType.choices).keys())}"
                        )

                    q_defaults = {
                        "question_type": question_type,
                        "text": q.get("text", ""),
                        "explanation_vi": q.get("explanation_vi", ""),
                        "data": data_payload,
                        "correct_answer": q.get("correct_key", ""),
                        "source": q.get("source", book.title),
                        "mondai": q.get("mondai", ""),
                        "order_in_mondai": q.get("order_in_mondai", 1),
                    }

                    obj, is_created = ExamQuestion.objects.update_or_create(
                        template=template,
                        order=order,
                        defaults=q_defaults,
                    )
                    if is_created:
                        created_q += 1
                    else:
                        updated_q += 1

                total_day_templates += 1

                self.stdout.write(
                    f"  [DAY] {template.title}: {template.questions.count()} câu "
                    f"(tạo mới {created_q}, cập nhật {updated_q})"
                )

            # ============ 3) PATTERN TESTS (group_type=PATTERN) ============
            total_pattern_templates = 0

            for idx, pat in enumerate(patterns, start=1):
                mondai_in = pat.get("mondai_in", [])
                if not mondai_in:
                    # Nếu không khai báo thì bỏ qua pattern này
                    continue

                pat_title = pat.get("title") or f"Pattern {idx}"
                raw_pat_slug = pat.get("slug") or f"{book.slug}-{pat_title}"
                pat_slug = make_slug(raw_pat_slug, max_tmpl_slug_len)

                group_type = pat.get("group_type") or ExamGroupType.BY_PATTERN
                if group_type not in dict(ExamGroupType.choices):
                    raise CommandError(
                        f"[pattern {pat_title}] group_type '{group_type}' không hợp lệ. "
                        f"Hợp lệ: {list(dict(ExamGroupType.choices).keys())}"
                    )

                lesson_index = pat.get("lesson_index") or idx
                time_limit = pat.get("time_limit_minutes")
                main_q_type = pat.get("main_question_type") or QuestionType.MCQ
                if main_q_type not in dict(QuestionType.choices):
                    raise CommandError(
                        f"[pattern {pat_title}] main_question_type '{main_q_type}' không hợp lệ."
                    )

                tmpl_defaults = {
                    "book": book,
                    "title": pat_title,
                    "description": pat.get("description", ""),
                    "level": book.level,
                    "category": book.category,
                    "group_type": group_type,
                    "lesson_index": lesson_index,
                    "subtitle": pat.get("subtitle", ""),
                    "main_question_type": main_q_type,
                    "time_limit_minutes": time_limit,
                    "is_active": pat.get("is_active", True),
                }

                pattern_template, _ = ExamTemplate.objects.update_or_create(
                    slug=pat_slug,
                    defaults=tmpl_defaults,
                )

                # Lấy tất cả câu thuộc book + mondai nằm trong mondai_in
                source_questions = (
                    ExamQuestion.objects.filter(
                        template__book=book,
                        mondai__in=mondai_in,
                    )
                    .select_related("template")
                    .order_by("mondai", "order_in_mondai", "id")
                )

                created_q = 0
                updated_q = 0

                for order, src_q in enumerate(source_questions, start=1):
                    q_defaults = {
                        "question_type": src_q.question_type,
                        "text": src_q.text,
                        "explanation_vi": src_q.explanation_vi,
                        "data": src_q.data,
                        "correct_answer": src_q.correct_answer,
                        "source": src_q.source or book.title,
                        "mondai": src_q.mondai,
                        "order_in_mondai": src_q.order_in_mondai,
                    }

                    obj, is_created = ExamQuestion.objects.update_or_create(
                        template=pattern_template,
                        order=order,
                        defaults=q_defaults,
                    )
                    if is_created:
                        created_q += 1
                    else:
                        updated_q += 1

                total_pattern_templates += 1

                self.stdout.write(
                    f"  [PATTERN] {pattern_template.title}: "
                    f"{pattern_template.questions.count()} câu "
                    f"(tạo mới {created_q}, cập nhật {updated_q})"
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ DONE: {book.title} – "
                    f"{total_day_templates} bài DAY, "
                    f"{total_pattern_templates} bài PATTERN"
                )
            )
