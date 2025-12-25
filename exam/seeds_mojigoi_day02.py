# exam/seeds_mojigoi_day02.py

from exam.models import (
    ExamBook,
    ExamTemplate,
    ExamQuestion,
    ExamLevel,
    ExamCategory,
    ExamGroupType,
    QuestionType,
)


def seed_power_mojigoi_n2_day02():
    # 1) ExamBook (sách gốc – dùng lại sách N2 Mojigoi)
    book_defaults = {
        "title": "Power Drill Mojigoi N2",
        "level": ExamLevel.N2,
        "category": ExamCategory.MOJIGOI,
    }
    if hasattr(ExamBook, "description"):
        book_defaults["description"] = "Power Drill Mojigoi N2 – sách luyện Kanji / Từ vựng."
    if hasattr(ExamBook, "total_lessons"):
        # Ví dụ: 30 day
        book_defaults["total_lessons"] = 30
    if hasattr(ExamBook, "is_active"):
        book_defaults["is_active"] = True

    book, _ = ExamBook.objects.update_or_create(
        slug="power-drill-mojigoi-n2",
        defaults=book_defaults,
    )

    # 2) ExamTemplate (đề DAY 02)
    template_defaults = {
        "title": "DAY 02 – Kanji & Từ vựng",
        "level": ExamLevel.N2,
        "category": ExamCategory.MOJIGOI,
    }
    if hasattr(ExamTemplate, "book"):
        template_defaults["book"] = book
    if hasattr(ExamTemplate, "subtitle"):
        template_defaults["subtitle"] = "Power Drill Mojigoi N2 – Day 02"
    if hasattr(ExamTemplate, "group_type"):
        template_defaults["group_type"] = ExamGroupType.BY_DAY
    if hasattr(ExamTemplate, "lesson_index"):
        template_defaults["lesson_index"] = 2
    if hasattr(ExamTemplate, "main_question_type"):
        template_defaults["main_question_type"] = QuestionType.MCQ
    if hasattr(ExamTemplate, "time_limit_minutes"):
        template_defaults["time_limit_minutes"] = 25
    if hasattr(ExamTemplate, "is_active"):
        template_defaults["is_active"] = True
    if hasattr(ExamTemplate, "description"):
        template_defaults["description"] = (
            "Đề DAY 02 – 18 câu Kanji & Từ vựng từ Power Drill Mojigoi N2."
        )

    template, _ = ExamTemplate.objects.update_or_create(
        slug="power-drill-mojigoi-n2-day-02",
        defaults=template_defaults,
    )

    source_label = "Power Drill Mojigoi N2 Day 02"

    # 3) Danh sách câu hỏi
    questions_data = [
        # ========= Mondai 01 – Kanji: Cách đọc =========
        {
            "order": 1,
            "mondai": "01",
            "order_in_mondai": 1,
            "text": "台風が関東地方に（接近）しているそうだ。",
            "choices": ["せきん", "せいきん", "せつきん", "せっきん"],
            "correct_key": "4",
            "explanation_vi": (
                "台風が関東地方に（接近）しているそうだ。\n\n"
                "Nghe nói bão đang tiến gần đến khu vực Kanto.\n\n"
                "接近（せっきん）: tiếp cận, lại gần.\n"
                "例：台風が接近している。– Bão đang tiến gần."
            ),
        },
        {
            "order": 2,
            "mondai": "01",
            "order_in_mondai": 2,
            "text": "それでは、来月の（中旬）にまたご連絡します。",
            "choices": ["なかば", "なかごろ", "ちゅうかん", "ちゅうじゅん"],
            "correct_key": "4",
            "explanation_vi": (
                "それでは、来月の（中旬）にまたご連絡します。\n\n"
                "Vậy thì, tôi sẽ liên lạc lại với bạn vào giữa tháng sau.\n\n"
                "中旬（ちゅうじゅん）: trung tuần, khoảng giữa tháng.\n"
                "例：10月の中旬にイベントが開催される。"
            ),
        },
        {
            "order": 3,
            "mondai": "01",
            "order_in_mondai": 3,
            "text": "病気やけがに（備えて）、保険に入っておいたほうがいい。",
            "choices": ["ささえて", "そなえて", "そろえて", "ひかえて"],
            "correct_key": "2",
            "explanation_vi": (
                "病気やけがに（備えて）、保険に入っておいたほうがいい。\n\n"
                "Để phòng bệnh hoặc chấn thương, tốt hơn bạn nên tham gia bảo hiểm.\n\n"
                "備える（そなえる）: chuẩn bị, phòng bị.\n"
                "例：災害に備えて食料を貯蔵する。"
            ),
        },

        # ========= Mondai 02 – Kanji: Chọn Kanji =========
        {
            "order": 4,
            "mondai": "02",
            "order_in_mondai": 1,
            "text": "すみません、この（あたり）に銀行はありませんか。",
            "choices": ["当たり", "周り", "辺り", "返り"],
            "correct_key": "3",
            "explanation_vi": (
                "すみません、この（あたり）に銀行はありませんか。\n\n"
                "Xin lỗi, có ngân hàng nào ở khu vực này không?\n\n"
                "辺り（あたり）: vùng, khu vực xung quanh.\n"
                "例：公園の辺りを散策する。"
            ),
        },
        {
            "order": 5,
            "mondai": "02",
            "order_in_mondai": 2,
            "text": "家族のため、父は（けんめい）に働いた。",
            "choices": ["賢名", "賢命", "懸名", "懸命"],
            "correct_key": "4",
            "explanation_vi": (
                "家族のため、父は（けんめい）に働いた。\n\n"
                "Vì gia đình, cha tôi đã làm việc rất chăm chỉ.\n\n"
                "懸命（けんめい）: hết sức, hết mình.\n"
                "例：彼は懸命に仕事をしている。"
            ),
        },
        {
            "order": 6,
            "mondai": "02",
            "order_in_mondai": 3,
            "text": "その町のチームが勝って、観客はとても（よろこん）でいた。",
            "choices": ["喜で", "喜んで", "喜こんで", "喜ろこんで"],
            "correct_key": "2",
            "explanation_vi": (
                "その町のチームが勝って、観客はとても（よろこん）でいた。\n\n"
                "Đội của thị trấn đó đã thắng và khán giả rất vui mừng.\n\n"
                "喜んで（よろこんで）: vui mừng, hân hoan.\n"
                "例：彼の提案を喜んで受け入れた。"
            ),
        },

        # ========= Mondai 03 – Từ vựng: Điền vào chỗ trống =========
        {
            "order": 7,
            "mondai": "03",
            "order_in_mondai": 1,
            "text": "１時間も遅れてきたのに謝らない友達に（　　）が立った。",
            "choices": ["足", "心", "腹", "頭"],
            "correct_key": "3",
            "explanation_vi": (
                "１時間も遅れてきたのに謝らない友達に（腹）が立った。\n\n"
                "Tôi rất tức giận với bạn đến muộn một tiếng mà không xin lỗi.\n\n"
                "腹（はら）: bụng; 腹が立つ: tức giận."
            ),
        },
        {
            "order": 8,
            "mondai": "03",
            "order_in_mondai": 2,
            "text": "その話は本当だ。（　　）私はその事故を見たのだから。",
            "choices": ["いまに", "げんに", "じつに", "まさに"],
            "correct_key": "2",
            "explanation_vi": (
                "その話は本当だ。（げんに）私はその事故を見たのだから。\n\n"
                "Câu chuyện đó là sự thật. Thực tế là tôi đã chứng kiến vụ tai nạn đó.\n\n"
                "げんに: thực sự, thực tế là.\n"
                "例：げんに彼のアイディアは良かった。"
            ),
        },
        {
            "order": 9,
            "mondai": "03",
            "order_in_mondai": 3,
            "text": "（　　）を使ってみて、とてもよかったので、この洗剤を買うことにした。",
            "choices": ["リスト", "カタログ", "サンプル", "パンフレット"],
            "correct_key": "3",
            "explanation_vi": (
                "（サンプル）を使ってみて、とてもよかったので、この洗剤を買うことにした。\n\n"
                "Sau khi dùng thử mẫu, tôi thấy rất tốt nên quyết định mua bột giặt này.\n\n"
                "サンプル: mẫu thử, sample sản phẩm."
            ),
        },
        {
            "order": 10,
            "mondai": "03",
            "order_in_mondai": 4,
            "text": (
                "A：明日から北海道へ行ってきます。\n"
                "B：いいですね。（　　）、森さんも行くと言っていましたよ。"
            ),
            "choices": ["そういえば", "そうすると", "それにしても", "それはそれは"],
            "correct_key": "1",
            "explanation_vi": (
                "A：明日から北海道へ行ってきます。\n"
                "B：いいですね。（そういえば）、森さんも行くと言っていましたよ。\n\n"
                "A: Tôi sẽ đi Hokkaido từ ngày mai.\n"
                "B: Được đấy nhỉ. Nhân tiện, tôi nghe nói anh Mori cũng sẽ đi đấy.\n\n"
                "そういえば: nếu nhắc tới chuyện đó, nói mới nhớ."
            ),
        },

        # ========= Mondai 04 – Từ vựng: Từ ghép =========
        {
            "order": 11,
            "mondai": "04",
            "order_in_mondai": 1,
            "text": "コンピューターが突然原因不明の（　　）作動を起こした。",
            "choices": ["不", "違", "誤", "失"],
            "correct_key": "3",
            "explanation_vi": (
                "コンピューターが突然原因不明の（誤）作動を起こした。\n\n"
                "Máy tính đột nhiên gặp sự cố hoạt động không rõ nguyên nhân.\n\n"
                "誤作動（ごさどう）: hoạt động sai, trục trặc."
            ),
        },
        {
            "order": 12,
            "mondai": "04",
            "order_in_mondai": 2,
            "text": "作曲（　　）になるため、音楽大学に進んだ。",
            "choices": ["手", "者", "家", "師"],
            "correct_key": "3",
            "explanation_vi": (
                "作曲（家）になるため、音楽大学に進んだ。\n\n"
                "Để trở thành nhạc sĩ, tôi đã học lên đại học âm nhạc.\n\n"
                "作曲家（さっきょくか）: nhà soạn nhạc."
            ),
        },
        {
            "order": 13,
            "mondai": "04",
            "order_in_mondai": 3,
            "text": "彼ははじめから責任（　　）が強い。",
            "choices": ["観", "感", "心", "性"],
            "correct_key": "2",
            "explanation_vi": (
                "彼ははじめから責任（感）が強い。\n\n"
                "Ngay từ đầu anh ấy đã có ý thức trách nhiệm rất cao.\n\n"
                "責任感（せきにんかん）: cảm giác trách nhiệm."
            ),
        },

        # ========= Mondai 05 – Từ vựng: Từ cận nghĩa =========
        {
            "order": 14,
            "mondai": "05",
            "order_in_mondai": 1,
            "text": "そのニュースは（たちまち）世界中に広まった。",
            "choices": ["すぐに", "ついに", "だんだん", "ようやく"],
            "correct_key": "1",
            "explanation_vi": (
                "そのニュースは（たちまち）世界中に広まった。\n\n"
                "Tin tức đó đã nhanh chóng lan ra khắp thế giới.\n\n"
                "たちまち ≒ すぐに: ngay lập tức."
            ),
        },
        {
            "order": 15,
            "mondai": "05",
            "order_in_mondai": 2,
            "text": "彼はノートに（せっせと）何かを書いていた。",
            "choices": ["速く", "熱心に", "上手に", "楽しそうに"],
            "correct_key": "2",
            "explanation_vi": (
                "彼はノートに（せっせと）何かを書いていた。\n\n"
                "Anh ấy đã chăm chỉ viết gì đó vào sổ tay.\n\n"
                "せっせと ≒ 熱心に（ねっしんに）: siêng năng, chăm chỉ."
            ),
        },
        {
            "order": 16,
            "mondai": "05",
            "order_in_mondai": 3,
            "text": "課長は今（ミーティング）中で、ここにはおりません。",
            "choices": ["会議", "出張", "研修", "休暇"],
            "correct_key": "1",
            "explanation_vi": (
                "課長は今（ミーティング）中で、ここにはおりません。\n\n"
                "Trưởng phòng đang trong cuộc họp và không có mặt ở đây.\n\n"
                "ミーティング ≒ 会議（かいぎ）: cuộc họp."
            ),
        },

        # ========= Mondai 06 – Từ vựng: Cách dùng từ =========
        {
            "order": 17,
            "mondai": "06",
            "order_in_mondai": 1,
            "text": "「わざと」: cố ý, cố tình. Chọn câu dùng đúng.",
            "choices": [
                "その選手はお金のために、（わざと）試合に負けた。",
                "お忙しいところ、（わざと）来てくださってありがとうございます。",
                "この着物は、結婚式のために（わざと）作ってもらった特別なものだ。",
                "母は、１０円でも安かったら遠くのスーパーまで（わざと）買いに行く。",
            ],
            "correct_key": "1",
            "explanation_vi": (
                "わざと: cố ý, cố tình.\n\n"
                "① その選手はお金のために、（わざと）試合に負けた。✔\n"
                "→ Tuyển thủ đó cố tình thua trận vì tiền.\n\n"
                "Các câu còn lại không dùng わざと tự nhiên."
            ),
        },
        {
            "order": 18,
            "mondai": "06",
            "order_in_mondai": 2,
            "text": "「引き返す（ひきかえす）」: quay trở lại (nơi ban đầu). Chọn câu dùng đúng.",
            "choices": [
                "借りたCDを友達に（引き返し）た。",
                "肉が焼けてきたら、（引き返して）裏も焼いてください。",
                "使った道具は、すぐに元の場所に（引き返し）てください。",
                "忘れ物をしたので、急いで家に（引き返し）た。",
            ],
            "correct_key": "4",
            "explanation_vi": (
                "引き返す（ひきかえす）: quay trở lại, quay ngược lại (nơi ban đầu).\n\n"
                "④ 忘れ物をしたので、急いで家に（引き返し）た。✔\n"
                "→ Vì quên đồ nên tôi vội quay về nhà.\n\n"
                "Các câu khác cần dùng các động từ khác như 返す・戻す."
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
