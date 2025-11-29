from exam.models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamLevel,
    ExamCategory,
    ExamGroupType,
    QuestionType,
)


def seed_power_mojigoi_n2_day01():
    # 1) ExamBook (sách gốc)
    book_defaults = {
        "title": "Power Drill Mojigoi N2",
        "level": ExamLevel.N2,
        "category": ExamCategory.MOJIGOI,
    }
    if hasattr(ExamBook, "description"):
        book_defaults["description"] = "Power Drill Mojigoi N2 – sách luyện Kanji / Từ vựng."
    if hasattr(ExamBook, "total_lessons"):
        book_defaults["total_lessons"] = 30
    if hasattr(ExamBook, "is_active"):
        book_defaults["is_active"] = True

    book, _ = ExamBook.objects.update_or_create(
        slug="power-drill-mojigoi-n2",
        defaults=book_defaults,
    )

    # 2) ExamTemplate (đề DAY 01)
    template_defaults = {
        "title": "DAY 01 – Kanji & Từ vựng",
        "level": ExamLevel.N2,
        "category": ExamCategory.MOJIGOI,
    }
    if hasattr(ExamTemplate, "book"):
        template_defaults["book"] = book
    if hasattr(ExamTemplate, "subtitle"):
        template_defaults["subtitle"] = "Power Drill Mojigoi N2 – Day 01"
    if hasattr(ExamTemplate, "group_type"):
        template_defaults["group_type"] = ExamGroupType.BY_DAY
    if hasattr(ExamTemplate, "lesson_index"):
        template_defaults["lesson_index"] = 1
    if hasattr(ExamTemplate, "main_question_type"):
        template_defaults["main_question_type"] = QuestionType.MCQ
    if hasattr(ExamTemplate, "time_limit_minutes"):
        template_defaults["time_limit_minutes"] = 25
    if hasattr(ExamTemplate, "duration_minutes"):
        template_defaults["duration_minutes"] = 25
    if hasattr(ExamTemplate, "is_active"):
        template_defaults["is_active"] = True
    if hasattr(ExamTemplate, "description"):
        template_defaults["description"] = (
            "Đề DAY 01 – 18 câu Kanji & Từ vựng từ Power Drill Mojigoi N2."
        )

    template, _ = ExamTemplate.objects.update_or_create(
        slug="power-drill-mojigoi-n2-day-01",
        defaults=template_defaults,
    )

    source_label = "Power Drill Mojigoi N2 Day 01"

    # 3) Danh sách câu hỏi
    questions_data = [
        # ========= Mondai 01 – Kanji: Cách đọc =========
        {
            "order": 1,
            "mondai": "01",
            "order_in_mondai": 1,
            "text": "私は遠くから彼女が働く（姿）をみていた。",
            "choices": ["すかた", "すがた", "すはた", "すはだ"],
            "correct_key": "2",
            "explanation_vi": (
                "私は遠くから彼女が働く（姿）をみていた。\n\n"
                "Từ xa tôi đã thấy bóng dáng cô ấy làm việc.\n\n"
                "姿（すがた）: hình dáng, dáng vẻ."
            ),
        },
        {
            "order": 2,
            "mondai": "01",
            "order_in_mondai": 2,
            "text": "スポーツをする時は、ときどき水分を（補った）ほうがいい。",
            "choices": ["とった", "あたった", "たもった", "おぎなった"],
            "correct_key": "4",
            "explanation_vi": (
                "スポーツをする時は、ときどき水分を（補った）ほうがいい。\n\n"
                "Khi chơi thể thao, thỉnh thoảng nên bổ sung nước.\n\n"
                "補う（おぎなう）【補】: bổ sung, bù đắp."
            ),
        },
        {
            "order": 3,
            "mondai": "01",
            "order_in_mondai": 3,
            "text": "３人に一人の（割合）で、その試験に合格している。",
            "choices": ["かつあい", "かっこう", "わりあい", "わりごう"],
            "correct_key": "3",
            "explanation_vi": (
                "３人に一人の（割合）で、その試験に合格している。\n\n"
                "Đậu kỳ thi đó với tỉ lệ trong 3 người có 1 người đỗ.\n\n"
                "割合（わりあい）: tỷ lệ, phần trăm."
            ),
        },

        # ========= Mondai 02 – Kanji: Chọn Kanji =========
        {
            "order": 4,
            "mondai": "02",
            "order_in_mondai": 1,
            "text": "では、明日の３時にそちらに（うかがいます）。",
            "choices": ["司います", "何います", "伺います", "荷いて"],
            "correct_key": "3",
            "explanation_vi": (
                "では、明日の３時にそちらに（うかがいます）。\n\n"
                "Vậy thì, tôi sẽ ghé qua vào lúc 3 giờ chiều mai.\n\n"
                "伺います（うかがいます）: khiêm nhường ngữ của 行きます／聞きます."
            ),
        },
        {
            "order": 5,
            "mondai": "02",
            "order_in_mondai": 2,
            "text": "最近は（れいぎ）を知らない人が多いように思う。",
            "choices": ["礼義", "礼儀", "礼議", "礼偽"],
            "correct_key": "2",
            "explanation_vi": (
                "最近は（れいぎ）を知らない人が多いように思う。\n\n"
                "Gần đây, tôi cảm thấy có nhiều người không biết lễ nghi.\n\n"
                "礼儀（れいぎ）: lễ nghi, phép lịch sự."
            ),
        },
        {
            "order": 6,
            "mondai": "02",
            "order_in_mondai": 3,
            "text": "（しゅうい）に迷惑がかからないように、静かに話してください。",
            "choices": ["周固", "周囲", "週周", "週囲"],
            "correct_key": "2",
            "explanation_vi": (
                "（しゅうい）に迷惑がかからないように、静かに話してください。\n\n"
                "Hãy nói chuyện nhỏ nhẹ để không làm phiền người xung quanh.\n\n"
                "周囲（しゅうい）: xung quanh, vùng lân cận."
            ),
        },

        # ========= Mondai 03 – Từ vựng: Điền vào chỗ trống =========
        {
            "order": 7,
            "mondai": "03",
            "order_in_mondai": 1,
            "text": "この計画が失敗したのは、リーダーである私の（　　）です。",
            "choices": ["義務", "成果", "責任", "任務"],
            "correct_key": "3",
            "explanation_vi": (
                "この計画が失敗したのは、リーダーである私の（責任）です。\n\n"
                "Việc kế hoạch này thất bại là trách nhiệm của tôi.\n\n"
                "責任（せきにん）: trách nhiệm."
            ),
        },
        {
            "order": 8,
            "mondai": "03",
            "order_in_mondai": 2,
            "text": "いくら忙しくても、（　　）日曜日くらいは休みたい。",
            "choices": ["せめて", "やっと", "けっこう", "どうやら"],
            "correct_key": "1",
            "explanation_vi": (
                "いくら忙しくても、（せめて）日曜日くらいは休みたい。\n\n"
                "Dù bận đến mấy, tôi cũng muốn nghỉ ít nhất là vào ngày Chủ nhật.\n\n"
                "せめて: ít nhất."
            ),
        },
        {
            "order": 9,
            "mondai": "03",
            "order_in_mondai": 3,
            "text": "会議が始まるまで３０分以上あるから、新聞でも読んで時間を（　　）。",
            "choices": ["もとう", "かけよう", "つぶそう", "とめとう"],
            "correct_key": "3",
            "explanation_vi": (
                "会議が始まるまで３０分以上あるから、新聞でも読んで時間を（つぶそう）。\n\n"
                "Còn hơn 30 phút nữa mới bắt đầu cuộc họp, nên hãy đọc báo để giết thời gian.\n\n"
                "時間をつぶす: giết thời gian."
            ),
        },
        {
            "order": 10,
            "mondai": "03",
            "order_in_mondai": 4,
            "text": "明日、来週の旅行の（　　）をしましょう。",
            "choices": ["見合い", "言い合い", "打ち合わせ", "待ち合わせ"],
            "correct_key": "3",
            "explanation_vi": (
                "明日、来週の旅行の（打ち合わせ）をしましょう。\n\n"
                "Ngày mai, chúng ta hãy tổ chức cuộc họp để thảo luận về chuyến đi tuần sau.\n\n"
                "打ち合わせ（うちあわせ）: cuộc họp, bàn bạc."
            ),
        },

        # ========= Mondai 04 – Từ vựng: Từ ghép =========
        {
            "order": 11,
            "mondai": "04",
            "order_in_mondai": 1,
            "text": "この問題を解くのに（　　）一日かかった。",
            "choices": ["完", "全", "本", "丸"],
            "correct_key": "4",
            "explanation_vi": (
                "この問題を解くのに（丸）一日かかった。\n\n"
                "Tôi mất cả một ngày tròn để giải quyết vấn đề này.\n\n"
                "丸一日（まるいちにち）: cả một ngày."
            ),
        },
        {
            "order": 12,
            "mondai": "04",
            "order_in_mondai": 2,
            "text": "履歴（　　）にはかならず写真を貼ってください。",
            "choices": ["紙", "書", "証", "状"],
            "correct_key": "2",
            "explanation_vi": (
                "履歴（書）にはかならず写真を貼ってください。\n\n"
                "Nhất định phải dán ảnh vào bản lý lịch.\n\n"
                "履歴書（りれきしょ）: sơ yếu lý lịch, CV."
            ),
        },
        {
            "order": 13,
            "mondai": "04",
            "order_in_mondai": 3,
            "text": "ボランティア活動に積極（　　）に参加している。",
            "choices": ["気", "感", "性", "的"],
            "correct_key": "4",
            "explanation_vi": (
                "ボランティア活動に積極（的）に参加している。\n\n"
                "Tôi đang tích cực tham gia vào các hoạt động tình nguyện.\n\n"
                "積極的（せっきょくてき）: tích cực."
            ),
        },

        # ========= Mondai 05 – Từ vựng: Từ cận nghĩa =========
        {
            "order": 14,
            "mondai": "05",
            "order_in_mondai": 1,
            "text": "この寒さだと（おそらく）明日は雪が降るだろう。",
            "choices": ["たぶん", "絶対に", "次第に", "たしかに"],
            "correct_key": "1",
            "explanation_vi": (
                "この寒さだと（おそらく）明日は雪が降るだろう。\n\n"
                "Với cái lạnh này, có lẽ ngày mai sẽ tuyết rơi.\n\n"
                "おそらく ≒ たぶん: có lẽ."
            ),
        },
        {
            "order": 15,
            "mondai": "05",
            "order_in_mondai": 2,
            "text": "（やむをえない）事情で大学をやめることになった。",
            "choices": ["くやしい", "はずかしい", "しかたがない", "もったいない"],
            "correct_key": "3",
            "explanation_vi": (
                "（やむをえない）事情で大学をやめることになった。\n\n"
                "Tôi phải thôi đại học vì lý do không thể tránh khỏi.\n\n"
                "やむをえない ≒ しかたがない: không còn cách nào khác."
            ),
        },
        {
            "order": 16,
            "mondai": "05",
            "order_in_mondai": 3,
            "text": "デパートで小学校の同級生に（ばったり）会った。",
            "choices": ["偶然", "自然に", "部合よく", "久しぶりに"],
            "correct_key": "1",
            "explanation_vi": (
                "デパートで小学校の同級生に（ばったり）会った。\n\n"
                "Tôi đã tình cờ gặp bạn học tiểu học ở trung tâm thương mại.\n\n"
                "ばったり ≒ 偶然（ぐうぜん）: tình cờ, bất ngờ gặp."
            ),
        },

        # ========= Mondai 06 – Từ vựng: Cách dùng từ =========
        {
            "order": 17,
            "mondai": "06",
            "order_in_mondai": 1,
            "text": "「等しい（ひとしい）」: bằng nhau, ngang nhau. Chọn câu dùng đúng.",
            "choices": [
                "この二つの三角形の面積は（等しい）。",
                "私は毎日（等しい）道を通って通勤している。",
                "チーム全員が（等しい）気持ちで試合に挑んだ。",
                "私と彼は、小学校から高校まで学校が（等しい）。",
            ],
            "correct_key": "1",
            "explanation_vi": (
                "等しい（ひとしい）: bằng nhau, ngang nhau, như nhau.\n\n"
                "① この二つの三角形の面積は（等しい）。✔\n"
                "→ Diện tích của hai tam giác này bằng nhau.\n\n"
                "Các câu còn lại tự nhiên hơn với 同じ."
            ),
        },
        {
            "order": 18,
            "mondai": "06",
            "order_in_mondai": 2,
            "text": "「あいにく」: không may, thật đáng tiếc. Chọn câu dùng đúng.",
            "choices": [
                "（あいにく）なので、コーヒーでもいかがですか。",
                "（あいにく）その日は予定があって参加できません。",
                "（あいにく）の天気で、海に行くのにちょうどいいですね。",
                "（あいにく）部長は席におりますので、少々お待ちください。",
            ],
            "correct_key": "2",
            "explanation_vi": (
                "あいにく【生憎】: không may, thật đáng tiếc.\n\n"
                "② （あいにく）その日は予定があって参加できません。✔\n"
                "→ Thật tiếc là hôm đó tôi có lịch nên không tham gia được."
            ),
        },
    ]

    # 4) Tạo / cập nhật ExamQuestion
    created = 0
    updated = 0

    for q in questions_data:
        choices_payload = [
            {"key": str(idx + 1), "text": text}
            for idx, text in enumerate(q["choices"])
        ]
        data = {"choices": choices_payload}

        question_defaults = {
            "question_type": QuestionType.MCQ,
            "text": q["text"],
            "explanation_vi": q["explanation_vi"],
            "data": data,
            "correct_answer": q["correct_key"],
        }
        # Các field mở rộng, chỉ set nếu model có
        if hasattr(ExamQuestion, "source"):
            question_defaults["source"] = source_label
        if hasattr(ExamQuestion, "mondai"):
            question_defaults["mondai"] = q["mondai"]
        if hasattr(ExamQuestion, "order_in_mondai"):
            question_defaults["order_in_mondai"] = q["order_in_mondai"]

        obj, was_created = ExamQuestion.objects.update_or_create(
            template=template,
            order=q["order"],
            defaults=question_defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    print(f"✅ Đã seed đề: {template}")
    try:
        print(
            f"   Câu hỏi trong DB: {template.questions.count()} "
            f"(tạo mới {created}, cập nhật {updated})"
        )
    except Exception:
        print(
            f"   Đã xử lý {len(questions_data)} câu "
            f"(tạo mới {created}, cập nhật {updated})"
        )
