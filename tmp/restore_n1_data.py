"""
One-off script to restore N1 kanji data from cached API response.
Run: python manage.py shell < tmp/restore_n1_data.py
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from kanji.models import KanjiLesson, Kanji

# N1 lesson data extracted from API cache
N1_LESSONS = [
    {"lesson_number": 1, "topic": "Bài 1 (1/5)", "order": 0},
    {"lesson_number": 2, "topic": "Bài 1 (2/5)", "order": 1},
    {"lesson_number": 3, "topic": "Bài 1 (3/5)", "order": 2},
    {"lesson_number": 4, "topic": "Bài 1 (4/5)", "order": 3},
    {"lesson_number": 5, "topic": "Bài 1 (5/5) + Bài 2 (1/1)", "order": 4},
]

# N1 kanji data extracted from API cache (lesson_number -> list of kanji)
N1_KANJIS = {
    1: [
        {"char": "維持", "sino_vi": "DUY TRÌ", "order": 0},
        {"char": "意図", "sino_vi": "Ý ĐỒ", "order": 1},
        {"char": "寄附", "sino_vi": "KÝ PHỤ", "order": 2},
        {"char": "拒否", "sino_vi": "CỰ PHỦ", "order": 3},
        {"char": "処置", "sino_vi": "XỬ TRÍ", "order": 4},
        {"char": "阻止", "sino_vi": "TRỞ CHỈ", "order": 5},
        {"char": "破棄", "sino_vi": "PHÁ KHÍ", "order": 6},
        {"char": "保護", "sino_vi": "BẢO HỘ", "order": 7},
        {"char": "保守", "sino_vi": "BẢO THỦ", "order": 8},
        {"char": "加味", "sino_vi": "GIA VỊ", "order": 9},
        {"char": "寄与", "sino_vi": "KÝ DỮ", "order": 10},
        {"char": "指揮", "sino_vi": "CHỈ HUY", "order": 11},
        {"char": "支持", "sino_vi": "CHI TRÌ", "order": 12},
        {"char": "自首", "sino_vi": "TỰ THÚ", "order": 13},
        {"char": "所持", "sino_vi": "SỞ TRÌ", "order": 14},
        {"char": "補助", "sino_vi": "BỔ TRỢ", "order": 15},
        {"char": "麻痺", "sino_vi": "MA TÝ", "order": 16},
        {"char": "餓死", "sino_vi": "NGẠ TỬ", "order": 17},
        {"char": "帰化", "sino_vi": "QUY HÓA", "order": 18},
        {"char": "危惧", "sino_vi": "NGUY CỤ", "order": 19},
        {"char": "起訴", "sino_vi": "KHỞI TỐ", "order": 20},
        {"char": "忌避", "sino_vi": "KỴ TỴ", "order": 21},
        {"char": "挙手", "sino_vi": "CỬ THỦ", "order": 22},
        {"char": "駆使", "sino_vi": "KHU SỬ", "order": 23},
        {"char": "駆除", "sino_vi": "KHU TRỪ", "order": 24},
        {"char": "固辞", "sino_vi": "CỐ TỪ", "order": 25},
        {"char": "誇示", "sino_vi": "KHOA THỊ", "order": 26},
        {"char": "示唆", "sino_vi": "THỊ TA", "order": 27},
    ],
    2: [
        {"char": "自負", "sino_vi": "TỰ PHỤ", "order": 0},
        {"char": "除去", "sino_vi": "TRỪ KHỨ", "order": 1},
        {"char": "図示", "sino_vi": "ĐỒ THỊ", "order": 2},
        {"char": "打破", "sino_vi": "ĐẢ PHÁ", "order": 3},
        {"char": "治癒", "sino_vi": "TRỊ DŨ", "order": 4},
        {"char": "卑下", "sino_vi": "TI HẠ", "order": 5},
        {"char": "補佐", "sino_vi": "BỔ TÁ", "order": 6},
        {"char": "拉致", "sino_vi": "LẠP TRÍ", "order": 7},
        {"char": "濾過", "sino_vi": "LỌC QUÁ", "order": 8},
        {"char": "意義", "sino_vi": "Ý NGHĨA", "order": 9},
        {"char": "異議", "sino_vi": "DỊ NGHỊ", "order": 10},
        {"char": "意地", "sino_vi": "Ý ĐỊA", "order": 11},
        {"char": "過疎", "sino_vi": "QUÁ SƠ", "order": 12},
        {"char": "規模", "sino_vi": "QUY MÔ", "order": 13},
        {"char": "義務", "sino_vi": "NGHĨA VỤ", "order": 14},
        {"char": "個々", "sino_vi": "CÁ CÁ", "order": 15},
        {"char": "誤差", "sino_vi": "NGỘ SAI", "order": 16},
        {"char": "磁気", "sino_vi": "TỪ KHÍ", "order": 17},
        {"char": "時期", "sino_vi": "THỜI KỲ", "order": 18},
        {"char": "自己", "sino_vi": "TỰ KỶ", "order": 19},
        {"char": "視野", "sino_vi": "THỊ DÃ", "order": 20},
        {"char": "砂利", "sino_vi": "SA LỢI", "order": 21},
        {"char": "趣旨", "sino_vi": "THÚ CHỈ", "order": 22},
        {"char": "種々", "sino_vi": "CHỦNG CHỦNG", "order": 23},
        {"char": "措置", "sino_vi": "THỐ TRÍ", "order": 24},
        {"char": "墓地", "sino_vi": "MỘ ĐỊA", "order": 25},
        {"char": "余地", "sino_vi": "DƯ ĐỊA", "order": 26},
        {"char": "危機", "sino_vi": "NGUY CƠ", "order": 27},
        {"char": "義理", "sino_vi": "NGHĨA LÝ", "order": 28},
        {"char": "下痢", "sino_vi": "HẠ LỴ", "order": 29},
        {"char": "語彙", "sino_vi": "NGỮ HỐI", "order": 30},
    ],
    3: [
        {"char": "語句", "sino_vi": "NGỮ CÚ", "order": 0},
        {"char": "孤児", "sino_vi": "CÔ NHI", "order": 1},
        {"char": "詐欺", "sino_vi": "TRÁ KHI", "order": 2},
        {"char": "歯科", "sino_vi": "XỈ KHOA", "order": 3},
        {"char": "自我", "sino_vi": "TỰ NGÃ", "order": 4},
        {"char": "磁器", "sino_vi": "TỪ KHÍ", "order": 5},
        {"char": "時差", "sino_vi": "THỜI SAI", "order": 6},
        {"char": "自主", "sino_vi": "TỰ CHỦ", "order": 7},
        {"char": "守備", "sino_vi": "THỦ BỊ", "order": 8},
        {"char": "助詞", "sino_vi": "TRỢ TỪ", "order": 9},
        {"char": "庶務", "sino_vi": "THỨ VỤ", "order": 10},
        {"char": "世辞", "sino_vi": "THẾ TỪ", "order": 11},
        {"char": "著書", "sino_vi": "TRỨ THƯ", "order": 12},
        {"char": "徒歩", "sino_vi": "ĐỒ BỘ", "order": 13},
        {"char": "秘書", "sino_vi": "BÍ THƯ", "order": 14},
        {"char": "不意", "sino_vi": "BẤT Ý", "order": 15},
        {"char": "部下", "sino_vi": "BỘ HẠ", "order": 16},
        {"char": "捕虜", "sino_vi": "BỔ LỖ", "order": 17},
        {"char": "未知", "sino_vi": "VỊ TRI", "order": 18},
        {"char": "余暇", "sino_vi": "DƯ HÀ", "order": 19},
        {"char": "利子", "sino_vi": "LỢI TỬ", "order": 20},
        {"char": "意気", "sino_vi": "Ý KHÍ", "order": 21},
        {"char": "囲碁", "sino_vi": "VI KỲ", "order": 22},
        {"char": "遺書", "sino_vi": "DI THƯ", "order": 23},
        {"char": "歌詞", "sino_vi": "CA TỪ", "order": 24},
        {"char": "過度", "sino_vi": "QUÁ ĐỘ", "order": 25},
        {"char": "可否", "sino_vi": "KHẢ PHỦ", "order": 26},
        {"char": "飢餓", "sino_vi": "CƠ NGẠ", "order": 27},
        {"char": "機器", "sino_vi": "CƠ KHÍ", "order": 28},
        {"char": "季語", "sino_vi": "QUÝ NGỮ", "order": 29},
        {"char": "機種", "sino_vi": "CƠ CHỦNG", "order": 30},
    ],
    4: [
        {"char": "旗手", "sino_vi": "KỲ THỦ", "order": 0},
        {"char": "既知", "sino_vi": "KÝ TRI", "order": 1},
        {"char": "虚偽", "sino_vi": "HƯ NGỤY", "order": 2},
        {"char": "虚無", "sino_vi": "HƯ VÔ", "order": 3},
        {"char": "呼気", "sino_vi": "HÔ KHÍ", "order": 4},
        {"char": "誤字", "sino_vi": "NGỘ TỰ", "order": 5},
        {"char": "語尾", "sino_vi": "NGỮ VĨ", "order": 6},
        {"char": "差異", "sino_vi": "SAI DỊ", "order": 7},
        {"char": "時価", "sino_vi": "THỜI GIÁ", "order": 8},
        {"char": "時下", "sino_vi": "THỜI HẠ", "order": 9},
        {"char": "時機", "sino_vi": "THỜI CƠ", "order": 10},
        {"char": "次期", "sino_vi": "THỨ KỲ", "order": 11},
        {"char": "私語", "sino_vi": "TƯ NGỮ", "order": 12},
        {"char": "死語", "sino_vi": "TỬ NGỮ", "order": 13},
        {"char": "事後", "sino_vi": "SỰ HẬU", "order": 14},
        {"char": "私費", "sino_vi": "TƯ PHÍ", "order": 15},
        {"char": "自費", "sino_vi": "TỰ PHÍ", "order": 16},
        {"char": "首位", "sino_vi": "THỦ VỊ", "order": 17},
        {"char": "主旨", "sino_vi": "CHỦ CHỈ", "order": 18},
        {"char": "種子", "sino_vi": "CHỦNG TỬ", "order": 19},
        {"char": "手話", "sino_vi": "THỦ THOẠI", "order": 20},
        {"char": "書記", "sino_vi": "THƯ KÝ", "order": 21},
        {"char": "齟齬", "sino_vi": "TRỮ NGỮ", "order": 22},
        {"char": "地価", "sino_vi": "ĐỊA GIÁ", "order": 23},
        {"char": "致死", "sino_vi": "TRÍ TỬ", "order": 24},
        {"char": "覇者", "sino_vi": "BÁ GIẢ", "order": 25},
        {"char": "馬車", "sino_vi": "MÃ XA", "order": 26},
        {"char": "避暑", "sino_vi": "TỴ THỬ", "order": 27},
        {"char": "比喩", "sino_vi": "TỶ DỤ", "order": 28},
        {"char": "部署", "sino_vi": "BỘ THỰ", "order": 29},
        {"char": "不和", "sino_vi": "BẤT HÒA", "order": 30},
    ],
    5: [
        {"char": "簿記", "sino_vi": "BỘ KÝ", "order": 0},
        {"char": "母語", "sino_vi": "MẪU NGỮ", "order": 1},
        {"char": "無期", "sino_vi": "VÔ KỲ", "order": 2},
        {"char": "路地", "sino_vi": "LỘ ĐỊA", "order": 3},
        {"char": "和語", "sino_vi": "HÒA NGỮ", "order": 4},
        {"char": "移行", "sino_vi": "DI HÀNH", "order": 5},
        {"char": "委託", "sino_vi": "ỦY THÁC", "order": 6},
        {"char": "違反", "sino_vi": "VI PHẠM", "order": 7},
        {"char": "依頼", "sino_vi": "Y LẠI", "order": 8},
        {"char": "汚染", "sino_vi": "Ô NHIỄM", "order": 9},
        {"char": "加減", "sino_vi": "GIA GIẢM", "order": 10},
        {"char": "企画", "sino_vi": "XÍ HOẠCH", "order": 11},
        {"char": "棄権", "sino_vi": "KHÍ QUYỀN", "order": 12},
        {"char": "記載", "sino_vi": "KÝ TÁI", "order": 13},
        {"char": "規制", "sino_vi": "QUY CHẾ", "order": 14},
        {"char": "偽造", "sino_vi": "NGỤY TẠO", "order": 15},
        {"char": "誤解", "sino_vi": "NGỘ GIẢI", "order": 16},
        {"char": "故障", "sino_vi": "CỐ CHƯỚNG", "order": 17},
        {"char": "誇張", "sino_vi": "KHOA TRƯƠNG", "order": 18},
        {"char": "雇用", "sino_vi": "CỐ DỤNG", "order": 19},
        {"char": "孤立", "sino_vi": "CÔ LẬP", "order": 20},
        {"char": "作用", "sino_vi": "TÁC DỤNG", "order": 21},
        {"char": "飼育", "sino_vi": "TỰ DỤC", "order": 22},
        {"char": "自覚", "sino_vi": "TỰ GIÁC", "order": 23},
        {"char": "志向", "sino_vi": "CHÍ HƯỚNG", "order": 24},
        {"char": "思考", "sino_vi": "TƯ KHẢO", "order": 25},
        {"char": "施行", "sino_vi": "THI HÀNH", "order": 26},
    ],
}

# Create lessons and kanji
created_lessons = 0
created_kanjis = 0

for lesson_data in N1_LESSONS:
    lesson, created = KanjiLesson.objects.get_or_create(
        jlpt_level="N1",
        lesson_number=lesson_data["lesson_number"],
        defaults={
            "topic": lesson_data["topic"],
            "order": lesson_data["order"],
        },
    )
    if created:
        created_lessons += 1
    
    kanjis = N1_KANJIS.get(lesson_data["lesson_number"], [])
    for k_data in kanjis:
        _, k_created = Kanji.objects.get_or_create(
            char=k_data["char"],
            defaults={
                "lesson": lesson,
                "sino_vi": k_data["sino_vi"],
                "order": k_data["order"],
            },
        )
        if k_created:
            created_kanjis += 1

print(f"Created {created_lessons} lessons, {created_kanjis} kanji entries.")
