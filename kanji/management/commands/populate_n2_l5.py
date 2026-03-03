# -*- coding: utf-8 -*-
"""
Management command to populate N2 Lesson 5 kanji + vocabulary with JLPT tags.
Run: python manage.py populate_n2_l5
"""
from django.core.management.base import BaseCommand
from kanji.models import KanjiLesson, Kanji, KanjiVocab


class Command(BaseCommand):
    help = 'Populate N2 Lesson 5 kanji and vocabulary with JLPT tags'

    def handle(self, *args, **options):
        # Create lesson if not exists
        lesson, created = KanjiLesson.objects.get_or_create(
            jlpt_level='N2',
            lesson_number=5,
            defaults={'topic': 'Cuộc sống và xã hội', 'order': 5},
        )
        status = "Created" if created else "Already exists"
        self.stdout.write(f"Lesson: {status} (id={lesson.id})")

        KANJI_DATA = [
            (1,  '庫', 'コ',       '',          'Khố',      'kho'),
            (2,  '坂', 'ハン',     'さか',       'Phản',     'cái dốc'),
            (3,  '底', 'テイ',     'そこ',       'Để',       'đáy'),
            (4,  '寺', 'ジ',       'てら',       'Tự',       'chùa'),
            (5,  '希', 'キ',       '',           'Hy',       'hi hữu, hi vọng'),
            (6,  '仲', 'チュウ',   'なか',       'Trọng',    'trọng tài'),
            (7,  '栄', 'エイ',     'さか.える',  'Vinh',     'vinh quang, vinh hạnh'),
            (8,  '札', 'サツ',     'ふだ',       'Trát',     'tiền giấy'),
            (9,  '板', 'バン、ハン', 'いた',     'Bản',      'tấm bảng'),
            (10, '包', 'ホウ',     'つつ.む',    'Bao',      'bao bọc'),
            (11, '焼', 'ショウ',   'や.く、や.ける', 'Thiêu', 'thiêu đốt'),
            (12, '章', 'ショウ',   '',           'Chương',   'chương sách'),
            (13, '照', 'ショウ',   'て.る、て.らす、て.れる', 'Chiếu', 'tham chiếu'),
            (14, '秒', 'ビョウ',   '',           'Miểu',     'giây (1/60 phút)'),
            (15, '皮', 'ヒ',       'かわ',       'Bì',       'da'),
            (16, '漁', 'ギョ、リョウ', '',       'Ngư',      'đánh cá'),
            (17, '貯', 'チョ',     '',           'Trữ',      'tàng trữ, lưu trữ'),
            (18, '柱', 'チュウ',   'はしら',     'Trụ, Trú', 'trụ cột'),
            (19, '祭', 'サイ',     'まつ.り、まつ.る', 'Tế, Sái', 'lễ hội'),
            (20, '筆', 'ヒツ',     'ふで',       'Bút',      'bút'),
        ]

        kanji_count = 0
        for order, char, onyomi, kunyomi, sino_vi, meaning_vi in KANJI_DATA:
            _, created = Kanji.objects.update_or_create(
                char=char,
                defaults={
                    'lesson': lesson,
                    'order': order,
                    'onyomi': onyomi,
                    'kunyomi': kunyomi,
                    'sino_vi': sino_vi,
                    'meaning_vi': meaning_vi,
                    'keyword': meaning_vi,
                },
            )
            kanji_count += 1
            s = "+" if created else "~"
            self.stdout.write(f"  {s} {char} ({sino_vi})")

        # Vocab with JLPT levels
        VOCAB_DATA = [
            # (kanji_char, word, reading, meaning, jlpt_level, priority)
            # 1. 庫
            ('庫', '倉庫', 'そうこ', 'kho, nhà kho', 'N2', 0),
            ('庫', '車庫', 'しゃこ', 'nhà để xe, ga-ra', 'N2', 1),
            ('庫', '金庫', 'きんこ', 'két sắt', 'N2', 2),
            ('庫', '冷蔵庫', 'れいぞうこ', 'tủ lạnh', 'N4', 3),
            # 2. 坂
            ('坂', '坂', 'さか', 'dốc, con dốc', 'N2', 0),
            ('坂', '上り坂', 'のぼりざか', 'dốc lên', 'N2', 1),
            ('坂', '下り坂', 'くだりざか', 'dốc xuống', 'N2', 2),
            # 3. 底
            ('底', '底', 'そこ', 'đáy', 'N2', 0),
            ('底', '海底', 'かいてい', 'đáy biển', 'N2', 1),
            ('底', '徹底', 'てってい', 'triệt để, toàn diện', 'N2', 2),
            # 4. 寺
            ('寺', '寺', 'てら', 'chùa, ngôi chùa', 'N3', 0),
            ('寺', 'お寺', 'おてら', 'ngôi chùa (kính ngữ)', 'N3', 1),
            # 5. 希
            ('希', '希望', 'きぼう', 'hi vọng, mong muốn', 'N3', 0),
            ('希', '希少', 'きしょう', 'hiếm, hi hữu', 'N1', 1),
            # 6. 仲
            ('仲', '仲間', 'なかま', 'bạn bè, đồng bọn', 'N3', 0),
            ('仲', '仲良し', 'なかよし', 'hòa thuận, thân thiết', 'N3', 1),
            ('仲', '仲人', 'ちゅうにん', 'người trung gian', 'N1', 2),
            # 7. 栄
            ('栄', '栄光', 'えいこう', 'vinh quang', 'N2', 0),
            ('栄', '栄養', 'えいよう', 'dinh dưỡng', 'N2', 1),
            ('栄', '繁栄', 'はんえい', 'phồn vinh, thịnh vượng', 'N1', 2),
            # 8. 札
            ('札', 'お札', 'おさつ', 'tiền giấy', 'N3', 0),
            ('札', '名札', 'なふだ', 'biển tên, thẻ tên', 'N2', 1),
            ('札', '切符', 'きっぷ', 'vé, phiếu', 'N3', 2),
            # 9. 板
            ('板', '板', 'いた', 'tấm ván, tấm bảng', 'N2', 0),
            ('板', '看板', 'かんばん', 'biển hiệu, bảng hiệu', 'N2', 1),
            ('板', '鉄板', 'てっぱん', 'tấm sắt', 'N2', 2),
            # 10. 包
            ('包', '包む', 'つつむ', 'gói, bọc', 'N3', 0),
            ('包', '包丁', 'ほうちょう', 'con dao', 'N3', 1),
            ('包', '包装', 'ほうそう', 'bao bì, đóng gói', 'N2', 2),
            # 11. 焼
            ('焼', '焼く', 'やく', 'nướng, đốt', 'N3', 0),
            ('焼', '焼ける', 'やける', 'bị cháy, bị rám nắng', 'N3', 1),
            ('焼', '夕焼け', 'ゆうやけ', 'hoàng hôn', 'N2', 2),
            # 12. 章
            ('章', '文章', 'ぶんしょう', 'bài văn, câu văn', 'N3', 0),
            ('章', '章', 'しょう', 'chương (sách)', 'N2', 1),
            # 13. 照
            ('照', '参照', 'さんしょう', 'tham chiếu, tham khảo', 'N2', 0),
            ('照', '照明', 'しょうめい', 'chiếu sáng', 'N2', 1),
            ('照', '日照り', 'ひでり', 'ánh nắng mặt trời', 'N2', 2),
            # 14. 秒
            ('秒', '秒', 'びょう', 'giây (đơn vị thời gian)', 'N3', 0),
            ('秒', '一秒', 'いちびょう', 'một giây', 'N3', 1),
            # 15. 皮
            ('皮', '皮', 'かわ', 'da, vỏ', 'N2', 0),
            ('皮', '毛皮', 'けがわ', 'da lông, lông thú', 'N2', 1),
            ('皮', '皮膚', 'ひふ', 'da (cơ thể)', 'N2', 2),
            # 16. 漁
            ('漁', '漁業', 'ぎょぎょう', 'ngư nghiệp, nghề cá', 'N2', 0),
            ('漁', '漁師', 'りょうし', 'ngư dân', 'N2', 1),
            ('漁', '漁港', 'ぎょこう', 'cảng cá', 'N1', 2),
            # 17. 貯
            ('貯', '貯金', 'ちょきん', 'tiền tiết kiệm', 'N3', 0),
            ('貯', '貯める', 'ためる', 'tích lũy, để dành', 'N3', 1),
            ('貯', '貯蔵', 'ちょぞう', 'dự trữ, tàng trữ', 'N1', 2),
            # 18. 柱
            ('柱', '柱', 'はしら', 'cột, trụ', 'N2', 0),
            ('柱', '電柱', 'でんちゅう', 'cột điện', 'N3', 1),
            ('柱', '大黒柱', 'だいこくちゅう', 'trụ cột, người chủ chốt', 'N1', 2),
            # 19. 祭
            ('祭', '祭り', 'まつり', 'lễ hội', 'N3', 0),
            ('祭', 'お祭り', 'おまつり', 'lễ hội (kính ngữ)', 'N3', 1),
            ('祭', '文化祭', 'ぶんかさい', 'lễ hội văn hóa', 'N2', 2),
            # 20. 筆
            ('筆', '筆', 'ふで', 'bút lông', 'N2', 0),
            ('筆', '鉛筆', 'えんぴつ', 'bút chì', 'N5', 1),
            ('筆', '筆者', 'ひっしゃ', 'tác giả', 'N1', 2),
        ]

        created_count = 0
        updated_count = 0
        for kanji_char, word, reading, meaning, jlpt, priority in VOCAB_DATA:
            try:
                kanji = Kanji.objects.get(char=kanji_char)
                _, created = KanjiVocab.objects.update_or_create(
                    kanji=kanji,
                    word=word,
                    defaults={
                        'reading': reading,
                        'meaning': meaning,
                        'jlpt_level': jlpt,
                        'priority': priority,
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Kanji.DoesNotExist:
                self.stderr.write(f"  SKIP: kanji {kanji_char} not found")
            except Exception as e:
                self.stderr.write(f"  ERROR: {word} - {e}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {created_count}, Updated {updated_count} vocab entries."
        ))
        self.stdout.write(f"Total kanji in lesson: {Kanji.objects.filter(lesson=lesson).count()}")
        self.stdout.write(f"Total vocab in lesson: {KanjiVocab.objects.filter(kanji__lesson=lesson).count()}")
