# exam/seeds_mojigoi_patterns.py

from exam.models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamLevel,
    ExamCategory,
    ExamGroupType,
    QuestionType,
)


# Cấu hình từng Mondaì → 1 đề "theo dạng"
PATTERN_CONFIG = {
    # Mondai 01 – Kanji: Cách đọc
    "01": {
        "slug": "power-drill-mojigoi-n2-pattern-01-kanji-reading",
        "title": "N2 Mojigoi – Kanji: Cách đọc (Mondai 01)",
        "subtitle": "Power Drill Mojigoi N2 – Tổng hợp tất cả Mondai 01",
        "main_question_type": QuestionType.MCQ,
        "time_limit_minutes": 25,
        "lesson_index": 101,  # chỉ để sort, khác với DAY 01/02
    },
    # Mondai 02 – Kanji: Chọn Kanji
    "02": {
        "slug": "power-drill-mojigoi-n2-pattern-02-kanji-choose",
        "title": "N2 Mojigoi – Kanji: Chọn chữ đúng (Mondai 02)",
        "subtitle": "Power Drill Mojigoi N2 – Tổng hợp tất cả Mondai 02",
        "main_question_type": QuestionType.MCQ,
        "time_limit_minutes": 25,
        "lesson_index": 102,
    },
    # Mondai 03 – Từ vựng: Điền vào chỗ trống
    "03": {
        "slug": "power-drill-mojigoi-n2-pattern-03-vocab-fill",
        "title": "N2 Mojigoi – Từ vựng: Điền chỗ trống (Mondai 03)",
        "subtitle": "Power Drill Mojigoi N2 – Tổng hợp tất cả Mondai 03",
        "main_question_type": QuestionType.MCQ,
        "time_limit_minutes": 25,
        "lesson_index": 103,
    },
    # Mondai 04 – Từ vựng: Từ ghép
    "04": {
        "slug": "power-drill-mojigoi-n2-pattern-04-vocab-compound",
        "title": "N2 Mojigoi – Từ vựng: Từ ghép (Mondai 04)",
        "subtitle": "Power Drill Mojigoi N2 – Tổng hợp tất cả Mondai 04",
        "main_question_type": QuestionType.MCQ,
        "time_limit_minutes": 25,
        "lesson_index": 104,
    },
    # Mondai 05 – Từ vựng: Từ cận nghĩa
    "05": {
        "slug": "power-drill-mojigoi-n2-pattern-05-vocab-near-synonym",
        "title": "N2 Mojigoi – Từ vựng: Từ cận nghĩa (Mondai 05)",
        "subtitle": "Power Drill Mojigoi N2 – Tổng hợp tất cả Mondai 05",
        "main_question_type": QuestionType.MCQ,
        "time_limit_minutes": 25,
        "lesson_index": 105,
    },
    # Mondai 06 – Từ vựng: Cách dùng từ
    "06": {
        "slug": "power-drill-mojigoi-n2-pattern-06-vocab-usage",
        "title": "N2 Mojigoi – Từ vựng: Cách dùng từ (Mondai 06)",
        "subtitle": "Power Drill Mojigoi N2 – Tổng hợp tất cả Mondai 06",
        "main_question_type": QuestionType.MCQ,
        "time_limit_minutes": 25,
        "lesson_index": 106,
    },
}


def seed_power_mojigoi_n2_patterns():
    """
    Từ data DAY 01, DAY 02, ... của Power Drill Mojigoi N2,
    tạo thêm các đề 'ôn theo dạng' (BY_PATTERN) cho từng Mondai.
    """

    # 1) Lấy Book gốc
    book = ExamBook.objects.get(slug="power-drill-mojigoi-n2")

    total_templates = 0

    for mondai_code, cfg in PATTERN_CONFIG.items():
        # 2) Lọc tất cả câu hỏi trong BOOK này thuộc mondai X
        qset = (
            ExamQuestion.objects.filter(
                template__book=book,
                mondai=mondai_code,
            )
            .select_related("template")
            .order_by("template__lesson_index", "order_in_mondai", "id")
        )

        if not qset.exists():
            print(f"⚠️ Không tìm thấy câu thuộc Mondai {mondai_code} cho book '{book.title}', bỏ qua.")
            continue

        # 3) Tạo / update ExamTemplate kiểu BY_PATTERN
        template_defaults = {
            "book": book,
            "title": cfg["title"],
            "level": book.level or ExamLevel.N2,
            "category": book.category or ExamCategory.MOJIGOI,
            "group_type": ExamGroupType.BY_PATTERN,
            "lesson_index": cfg.get("lesson_index", 100),
            "subtitle": cfg.get("subtitle", ""),
            "main_question_type": cfg.get("main_question_type", QuestionType.MCQ),
            "time_limit_minutes": cfg.get("time_limit_minutes", 25),
            "is_active": True,
        }

        pattern_template, _ = ExamTemplate.objects.update_or_create(
            slug=cfg["slug"],
            defaults=template_defaults,
        )

        source_label = f"{book.title} – Mondai {mondai_code} (tổng hợp)"

        # 4) Copy câu hỏi sang template mới (1 → nhiều)
        created = 0
        updated = 0

        for idx, original in enumerate(qset, start=1):
            question_defaults = {
                "question_type": original.question_type,
                "text": original.text,
                "explanation_vi": original.explanation_vi,
                "data": original.data,
                "correct_answer": original.correct_answer,
            }

            # Meta JLPT
            if hasattr(ExamQuestion, "source"):
                # giữ source cũ + note đang là đề pattern
                old_source = getattr(original, "source", "") or ""
                if old_source:
                    question_defaults["source"] = f"{old_source} | Pattern Mondai {mondai_code}"
                else:
                    question_defaults["source"] = source_label

            if hasattr(ExamQuestion, "mondai"):
                question_defaults["mondai"] = original.mondai
            if hasattr(ExamQuestion, "order_in_mondai"):
                question_defaults["order_in_mondai"] = original.order_in_mondai

            obj, was_created = ExamQuestion.objects.update_or_create(
                template=pattern_template,
                order=idx,
                defaults=question_defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        print(
            f"✅ Mondai {mondai_code}: {pattern_template} – tổng {qset.count()} câu "
            f"(tạo mới {created}, cập nhật {updated})"
        )
        total_templates += 1

    print(f"🎯 Hoàn tất. Đã tạo / cập nhật {total_templates} đề 'ôn theo dạng' cho {book.title}.")
