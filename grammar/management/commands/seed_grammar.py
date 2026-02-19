"""
Seed sample Grammar JLPT data — đầy đủ tất cả features.
Run: python manage.py seed_grammar
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from grammar.models import (
    GrammarBook,
    GrammarPoint,
    GrammarExample,
    GrammarExerciseSet,
    GrammarQuestion,
)


# ──────────────────────────────────────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────────────────────────────────────

BOOKS = [
    {
        "title": "Shin Kanzen Master N5",
        "slug": "shin-kanzen-master-n5",
        "level": "N5",
        "description": "Bộ sách luyện thi JLPT N5 phổ biến nhất, bao gồm ngữ pháp cơ bản.",
    },
    {
        "title": "Shin Kanzen Master N4",
        "slug": "shin-kanzen-master-n4",
        "level": "N4",
        "description": "Ngữ pháp N4 — bước tiếp theo sau khi hoàn thành N5.",
    },
    {
        "title": "Try! N3 Bunpou",
        "slug": "try-n3-bunpou",
        "level": "N3",
        "description": "Sách luyện ngữ pháp N3 với giải thích chi tiết và bài tập thực hành.",
    },
]

GRAMMAR_DATA = [
    # ─── N5 ───────────────────────────────────────────────────────────────────
    {
        "book_slug": "shin-kanzen-master-n5",
        "level": "N5",
        "order": 1,
        "title": "〜は〜です",
        "slug": "wa-desu",
        "reading": "は〜です",
        "meaning_vi": "... là ...",
        "formation": "N₁ は N₂ です",
        "summary": "Câu khẳng định cơ bản trong tiếng Nhật, tương đương 'là' trong tiếng Việt.",
        "explanation": (
            "「は」 là trợ từ chủ đề (topic marker), đánh dấu chủ đề của câu.\n"
            "「です」 là copula lịch sự, tương đương 'là / am / is / are' trong tiếng Anh.\n\n"
            "Cấu trúc này được dùng để:\n"
            "- Giới thiệu bản thân hoặc người khác\n"
            "- Mô tả sự vật, sự việc\n"
            "- Xác nhận thông tin"
        ),
        "notes": "「は」 được đọc là 'wa' (không phải 'ha') khi dùng làm trợ từ chủ đề.",
        "examples": [
            {
                "jp": "わたしは学生です。",
                "vi": "Tôi là học sinh.",
                "hs": 4, "he": 7,
            },
            {
                "jp": "これはほんです。",
                "vi": "Cái này là sách.",
                "hs": 4, "he": 7,
            },
            {
                "jp": "かれは先生です。",
                "vi": "Anh ấy là giáo viên.",
                "hs": 3, "he": 6,
            },
        ],
        "exercise_sets": [
            {
                "title": "Bài tập 〜は〜です",
                "slug": "ex-wa-desu",
                "description": "Luyện tập cấu trúc câu cơ bản は〜です",
                "questions": [
                    {
                        "type": "MCQ",
                        "order": 1,
                        "text": "わたし ___ 田中です。",
                        "choices": [
                            {"key": "1", "text": "が"},
                            {"key": "2", "text": "は"},
                            {"key": "3", "text": "を"},
                            {"key": "4", "text": "に"},
                        ],
                        "answer": "2",
                        "exp_jp": "「は」は主題を示す助詞です。",
                        "exp_vi": "「は」 là trợ từ chủ đề, đứng sau chủ thể của câu.",
                    },
                    {
                        "type": "MCQ",
                        "order": 2,
                        "text": "これはほん ___。",
                        "choices": [
                            {"key": "1", "text": "だ"},
                            {"key": "2", "text": "です"},
                            {"key": "3", "text": "ます"},
                            {"key": "4", "text": "でした"},
                        ],
                        "answer": "2",
                        "exp_jp": "丁寧形の文末は「です」を使います。",
                        "exp_vi": "Thể lịch sự dùng「です」ở cuối câu (thì hiện tại).",
                    },
                    {
                        "type": "SENTENCE_ORDER",
                        "order": 3,
                        "prefix": "",
                        "suffix": "。",
                        "tokens": ["わたし", "は", "がくせい", "です"],
                        "correct_order": [0, 1, 2, 3],
                        "star_position": 3,
                        "exp_jp": "正しい語順：（わたし）（は）（★がくせい）（です）。",
                        "exp_vi": "わたしはがくせいです。→ Tôi là học sinh. ★ = がくせい（学生）.",
                    },
                ],
            }
        ],
    },
    {
        "book_slug": "shin-kanzen-master-n5",
        "level": "N5",
        "order": 2,
        "title": "〜ている",
        "slug": "te-iru",
        "reading": "〜ている",
        "meaning_vi": "đang ..., trạng thái ...",
        "formation": "V-て形 + いる",
        "summary": "Diễn tả hành động đang xảy ra (tiến hành) hoặc trạng thái kết quả của một hành động.",
        "explanation": (
            "「〜ている」 có hai nghĩa chính:\n\n"
            "① Hành động đang tiến hành (progressive):\n"
            "→ 食べている = đang ăn\n\n"
            "② Trạng thái kết quả của hành động đã hoàn thành (resultant state):\n"
            "→ 結婚している = đã kết hôn (và đang trong trạng thái kết hôn)\n\n"
            "Dạng thông thường (casual): 〜てる (rút gọn từ 〜ている)"
        ),
        "notes": "Với động từ di chuyển (来る、行く、帰る...), 「〜ている」 biểu thị trạng thái kết quả, không phải hành động đang xảy ra.",
        "examples": [
            {"jp": "いま、テレビを見ています。", "vi": "Bây giờ tôi đang xem TV.", "hs": 9, "he": 12},
            {"jp": "かれは結婚しています。", "vi": "Anh ấy đã kết hôn.", "hs": 4, "he": 9},
            {"jp": "雨が降っています。", "vi": "Trời đang mưa.", "hs": 3, "he": 6},
        ],
        "exercise_sets": [
            {
                "title": "Bài tập 〜ている",
                "slug": "ex-te-iru",
                "description": "Luyện tập dạng tiến hành và trạng thái kết quả",
                "questions": [
                    {
                        "type": "MCQ",
                        "order": 1,
                        "text": "かのじょは音楽を ___ います。",
                        "choices": [
                            {"key": "1", "text": "聞い"},
                            {"key": "2", "text": "聞いて"},
                            {"key": "3", "text": "聞く"},
                            {"key": "4", "text": "聞き"},
                        ],
                        "answer": "2",
                        "exp_jp": "「〜ている」の前にはて形が必要です。「聞く」のて形は「聞いて」。",
                        "exp_vi": "Trước 「いる」 cần dùng て形. 「聞く」 → て形 là 「聞いて」.",
                    },
                    {
                        "type": "MCQ",
                        "order": 2,
                        "text": "かれは今どこにいますか？　— 部屋で寝て ___。",
                        "choices": [
                            {"key": "1", "text": "います"},
                            {"key": "2", "text": "ました"},
                            {"key": "3", "text": "ある"},
                            {"key": "4", "text": "いた"},
                        ],
                        "answer": "1",
                        "exp_jp": "現在進行形には「〜ています」を使います。",
                        "exp_vi": "Hiện tại đang xảy ra dùng 「〜ています」.",
                    },
                    {
                        "type": "SENTENCE_ORDER",
                        "order": 3,
                        "prefix": "わたしは今",
                        "suffix": "。",
                        "tokens": ["べんきょう", "して", "います", "にほんごを"],
                        "correct_order": [3, 0, 1, 2],
                        "star_position": 2,
                        "exp_jp": "正しい語順：わたしは今（にほんごを）（べんきょう）（して）（います）。",
                        "exp_vi": "Tôi đang học tiếng Nhật. → にほんごをべんきょうしています。",
                    },
                    {
                        "type": "MCQ",
                        "order": 4,
                        "text": "山田さんは ___ ていますか？（結婚）",
                        "choices": [
                            {"key": "1", "text": "結婚し"},
                            {"key": "2", "text": "結婚する"},
                            {"key": "3", "text": "結婚した"},
                            {"key": "4", "text": "結婚して"},
                        ],
                        "answer": "1",
                        "exp_jp": "「結婚する」のて形→「結婚して」、+いる→「結婚しています」。",
                        "exp_vi": "「結婚する」て形 = 「結婚して」 → 「結婚しています」",
                    },
                ],
            }
        ],
    },
    # ─── N4 ───────────────────────────────────────────────────────────────────
    {
        "book_slug": "shin-kanzen-master-n4",
        "level": "N4",
        "order": 1,
        "title": "〜ために",
        "slug": "tame-ni",
        "reading": "〜ために",
        "meaning_vi": "để (mục đích) / vì (nguyên nhân)",
        "formation": "V辞書形 + ために　／　Nの + ために",
        "summary": "Diễn tả mục đích của hành động hoặc nguyên nhân / lợi ích của ai đó.",
        "explanation": (
            "「ために」 có 2 cách dùng chính:\n\n"
            "① Mục đích (Purpose) — động từ ở thể từ điển:\n"
            "→ 日本語を学ぶために、毎日勉強している。\n"
            "   (Để học tiếng Nhật, tôi học mỗi ngày.)\n\n"
            "② Vì / cho / lợi ích của (For the sake of) — danh từ:\n"
            "→ 家族のために働いている。\n"
            "   (Làm việc vì gia đình.)\n\n"
            "③ Nguyên nhân (Cause — thường tiêu cực) — V た形 / い形 / な形:\n"
            "→ 雪が降ったために、電車が遅れた。\n"
            "   (Do tuyết rơi, tàu bị trễ.)"
        ),
        "notes": "Phân biệt với 「ように」: 「ために」 = mục đích rõ ràng, chủ động. 「ように」 = mục tiêu / trạng thái mong muốn.",
        "examples": [
            {"jp": "大学に入るために、毎日勉強しています。", "vi": "Để vào đại học, tôi học mỗi ngày.", "hs": 8, "he": 12},
            {"jp": "健康のために、走っています。", "vi": "Tôi chạy bộ vì sức khỏe.", "hs": 3, "he": 6},
            {"jp": "地震のために、電車が止まった。", "vi": "Do động đất, tàu đã dừng lại.", "hs": 5, "he": 9},
        ],
        "exercise_sets": [
            {
                "title": "Bài tập 〜ために",
                "slug": "ex-tame-ni",
                "description": "Phân biệt 3 cách dùng của ために",
                "questions": [
                    {
                        "type": "MCQ",
                        "order": 1,
                        "text": "日本語が上手になる ___ 、毎日練習しています。",
                        "choices": [
                            {"key": "1", "text": "ために"},
                            {"key": "2", "text": "ように"},
                            {"key": "3", "text": "から"},
                            {"key": "4", "text": "ので"},
                        ],
                        "answer": "1",
                        "exp_jp": "目的を表す「ために」。意志動詞が続く場合は「ために」を使います。",
                        "exp_vi": "「ために」diễn tả mục đích + động từ có ý chí. Đáp án đúng là ①.",
                    },
                    {
                        "type": "MCQ",
                        "order": 2,
                        "text": "子供 ___ 、おもちゃを買った。",
                        "choices": [
                            {"key": "1", "text": "のために"},
                            {"key": "2", "text": "のように"},
                            {"key": "3", "text": "のために"},
                            {"key": "4", "text": "について"},
                        ],
                        "answer": "1",
                        "exp_jp": "名詞の場合は「Nのために」の形を使います。",
                        "exp_vi": "Sau danh từ dùng 「Nのために」. Mua đồ chơi vì/cho con.",
                    },
                    {
                        "type": "SENTENCE_ORDER",
                        "order": 3,
                        "prefix": "JLPT N3に",
                        "suffix": "勉強しています。",
                        "tokens": ["ために", "合格する", "一生懸命", "毎日"],
                        "correct_order": [1, 0, 3, 2],
                        "star_position": 2,
                        "exp_jp": "JLPT N3に（合格する）（ために）（毎日）（一生懸命）勉強しています。",
                        "exp_vi": "Để đỗ JLPT N3, tôi học chăm chỉ mỗi ngày.",
                    },
                    {
                        "type": "MCQ",
                        "order": 4,
                        "text": "台風が来た ___ 、試合が中止になった。",
                        "choices": [
                            {"key": "1", "text": "ために"},
                            {"key": "2", "text": "ように"},
                            {"key": "3", "text": "ために"},
                            {"key": "4", "text": "のに"},
                        ],
                        "answer": "1",
                        "exp_jp": "「Vたために」は原因・理由を表します（多くは否定的な結果）。",
                        "exp_vi": "「Vたために」diễn tả nguyên nhân (thường dẫn đến kết quả tiêu cực).",
                    },
                    {
                        "type": "SENTENCE_ORDER",
                        "order": 5,
                        "prefix": "彼は",
                        "suffix": "働いています。",
                        "tokens": ["家族", "の", "ために", "一生懸命"],
                        "correct_order": [0, 1, 2, 3],
                        "star_position": 3,
                        "exp_jp": "彼は（家族）（の）（ために）（一生懸命）働いています。",
                        "exp_vi": "Anh ấy làm việc chăm chỉ vì gia đình. ★は「ために」。",
                    },
                ],
            }
        ],
    },
    # ─── N3 ───────────────────────────────────────────────────────────────────
    {
        "book_slug": "try-n3-bunpou",
        "level": "N3",
        "order": 1,
        "title": "〜に反して",
        "slug": "ni-hanshite",
        "reading": "〜にはんして",
        "meaning_vi": "trái với ..., ngược lại với ...",
        "formation": "N + に反して",
        "summary": "Diễn tả sự trái ngược với mong đợi, dự đoán, hay quy tắc nào đó.",
        "explanation": (
            "「〜に反して」 được dùng khi kết quả / thực tế trái ngược với:\n"
            "- Kỳ vọng、mong đợi (期待)\n"
            "- Dự đoán (予想)\n"
            "- Nguyện vọng (希望)\n"
            "- Quy tắc、luật lệ (規則・ルール)\n\n"
            "Có thể thay thế bằng: 「〜に反した N」 (dạng tính từ)\n\n"
            "Khác với「〜にもかかわらず」:\n"
            "→ 「に反して」 nhấn mạnh sự trái ngược về nội dung\n"
            "→ 「にもかかわらず」 nhấn mạnh sự bất chấp / không phụ thuộc"
        ),
        "notes": "Thường dùng với các danh từ như: 期待、予想、希望、意志、規則、約束、常識",
        "examples": [
            {"jp": "みんなの期待に反して、チームは負けてしまった。", "vi": "Trái với kỳ vọng của mọi người, đội đã thua.", "hs": 7, "he": 12},
            {"jp": "天気予報に反して、晴れた。", "vi": "Trái với dự báo thời tiết, trời nắng.", "hs": 6, "he": 11},
            {"jp": "両親の希望に反して、彼は芸術家になった。", "vi": "Trái với mong muốn của bố mẹ, anh ấy trở thành nghệ sĩ.", "hs": 7, "he": 12},
        ],
        "exercise_sets": [
            {
                "title": "Bài tập 〜に反して",
                "slug": "ex-ni-hanshite",
                "description": "Luyện tập cấu trúc N3 に反して",
                "questions": [
                    {
                        "type": "MCQ",
                        "order": 1,
                        "text": "みんなの期待 ___ 、彼は試験に落ちてしまった。",
                        "choices": [
                            {"key": "1", "text": "に反して"},
                            {"key": "2", "text": "にとって"},
                            {"key": "3", "text": "に対して"},
                            {"key": "4", "text": "について"},
                        ],
                        "answer": "1",
                        "exp_jp": "「期待に反して」は「期待に逆らって、期待と違って」という意味。",
                        "exp_vi": "「期待に反して」= trái với kỳ vọng. Kết quả thi cử trái với điều mọi người mong đợi.",
                    },
                    {
                        "type": "MCQ",
                        "order": 2,
                        "text": "先生の ___ 行動をとってはいけない。",
                        "choices": [
                            {"key": "1", "text": "規則に反した"},
                            {"key": "2", "text": "規則について"},
                            {"key": "3", "text": "規則にそった"},
                            {"key": "4", "text": "規則にかかわる"},
                        ],
                        "answer": "1",
                        "exp_jp": "「規則に反した行動」＝規則に違反した行動。「に反した」は連体修飾。",
                        "exp_vi": "「規則に反した行動」= hành động vi phạm quy tắc. Dạng「に反した」bổ nghĩa cho danh từ.",
                    },
                    {
                        "type": "SENTENCE_ORDER",
                        "order": 3,
                        "prefix": "天気予報",
                        "suffix": "一日中雨が降った。",
                        "tokens": ["に反して", "晴れるはずが", "、", "予想に"],
                        "correct_order": [3, 0, 1, 2],
                        "star_position": 1,
                        "exp_jp": "天気予報（予想に）（に反して）（晴れるはずが）（、）一日中雨が降った。",
                        "exp_vi": "Trái với dự báo thời tiết (đáng ra trời nắng), cả ngày mưa.",
                    },
                    {
                        "type": "MCQ",
                        "order": 4,
                        "text": "両親の反対 ___ 、二人は結婚した。",
                        "choices": [
                            {"key": "1", "text": "に反して"},
                            {"key": "2", "text": "にもかかわらず"},
                            {"key": "3", "text": "のために"},
                            {"key": "4", "text": "にそって"},
                        ],
                        "answer": "2",
                        "exp_jp": "「反対にもかかわらず」＝反対があったにもかかわらず（bất chấp sự phản đối）。「に反して」は使えない（名詞のみ）。",
                        "exp_vi": "「反対」là danh từ → 「にもかかわらず」(bất chấp) phù hợp hơn vì không có ý 'trái ngược về nội dung'.",
                    },
                    {
                        "type": "SENTENCE_ORDER",
                        "order": 5,
                        "prefix": "彼女は",
                        "suffix": "女優になった。",
                        "tokens": ["親の", "希望に", "反して", "ついに"],
                        "correct_order": [0, 1, 2, 3],
                        "star_position": 3,
                        "exp_jp": "彼女は（親の）（希望に）（★反して）（ついに）女優になった。",
                        "exp_vi": "Trái với mong muốn của cha mẹ, cuối cùng cô ấy trở thành diễn viên. ★は「反して」。",
                    },
                ],
            }
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# COMMAND
# ──────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed sample Grammar JLPT data (books, points, examples, exercises)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xóa toàn bộ data grammar cũ trước khi seed",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("⚠ Đang xóa data grammar cũ..."))
            GrammarQuestion.objects.all().delete()
            GrammarExerciseSet.objects.all().delete()
            GrammarExample.objects.all().delete()
            GrammarPoint.objects.filter(book__isnull=False).delete()
            GrammarBook.objects.all().delete()
            self.stdout.write(self.style.WARNING("✓ Đã xóa xong."))

        # 1. Books
        book_map = {}
        for b in BOOKS:
            book, created = GrammarBook.objects.update_or_create(
                slug=b["slug"],
                defaults={
                    "title": b["title"],
                    "level": b["level"],
                    "description": b["description"],
                    "is_active": True,
                },
            )
            book_map[b["slug"]] = book
            verb = "Tạo" if created else "Cập nhật"
            self.stdout.write(f"  📚 {verb}: {book}")

        # 2. Grammar Points + Examples + ExerciseSets
        for gd in GRAMMAR_DATA:
            book = book_map.get(gd["book_slug"])

            point, created = GrammarPoint.objects.update_or_create(
                slug=gd["slug"],
                defaults={
                    "title": gd["title"],
                    "level": gd["level"],
                    "reading": gd.get("reading", ""),
                    "meaning_vi": gd.get("meaning_vi", ""),
                    "formation": gd.get("formation", ""),
                    "summary": gd.get("summary", ""),
                    "explanation": gd.get("explanation", ""),
                    "notes": gd.get("notes", ""),
                    "book": book,
                    "order": gd.get("order", 0),
                    "is_active": True,
                },
            )
            verb = "Tạo" if created else "Cập nhật"
            self.stdout.write(f"  ✏  {verb}: {point}")

            # Examples
            if created:
                for i, ex in enumerate(gd.get("examples", [])):
                    GrammarExample.objects.create(
                        grammar_point=point,
                        sentence_jp=ex["jp"],
                        sentence_vi=ex["vi"],
                        highlight_start=ex.get("hs"),
                        highlight_end=ex.get("he"),
                        order=i,
                    )
                self.stdout.write(f"     → {len(gd.get('examples', []))} ví dụ")

            # Exercise Sets
            for es_data in gd.get("exercise_sets", []):
                es, es_created = GrammarExerciseSet.objects.update_or_create(
                    slug=es_data["slug"],
                    defaults={
                        "title": es_data["title"],
                        "description": es_data.get("description", ""),
                        "grammar_point": point,
                        "book": book,
                        "level": gd["level"],
                        "is_active": True,
                    },
                )
                verb_es = "Tạo" if es_created else "Cập nhật"
                self.stdout.write(f"     📝 {verb_es} bộ tập: {es}")

                if es_created:
                    for q_data in es_data.get("questions", []):
                        if q_data["type"] == "MCQ":
                            GrammarQuestion.objects.create(
                                exercise_set=es,
                                question_type=GrammarQuestion.MCQ,
                                order=q_data["order"],
                                question_text=q_data["text"],
                                choices=q_data["choices"],
                                correct_answer=q_data["answer"],
                                explanation_jp=q_data.get("exp_jp", ""),
                                explanation_vi=q_data.get("exp_vi", ""),
                            )
                        else:  # SENTENCE_ORDER
                            GrammarQuestion.objects.create(
                                exercise_set=es,
                                question_type=GrammarQuestion.SENTENCE_ORDER,
                                order=q_data["order"],
                                sentence_prefix=q_data.get("prefix", ""),
                                sentence_suffix=q_data.get("suffix", ""),
                                tokens=q_data.get("tokens", []),
                                correct_order=q_data.get("correct_order", []),
                                star_position=q_data.get("star_position", 1),
                                explanation_jp=q_data.get("exp_jp", ""),
                                explanation_vi=q_data.get("exp_vi", ""),
                            )

                    count = len(es_data.get("questions", []))
                    self.stdout.write(f"        → {count} câu hỏi")

                es.update_question_count()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "✅ Seed hoàn tất!\n"
            "   Truy cập /grammar/ để xem trang chủ ngữ pháp.\n"
            "   Admin: /admin/grammar/"
        ))
