"""
Management command: clear all kanji data and load N5 sample data.

Usage:
    python manage.py load_kanji_n5
    python manage.py load_kanji_n5 --no-clear
"""
from django.core.management.base import BaseCommand

from kanji.admin import _import_kanji_json
from kanji.models import KanjiLesson, Kanji, KanjiVocab, UserKanjiProgress

N5_DATA = [
  {
    "jlpt_level": "N5",
    "lesson_id": 1,
    "topic": "Kanji made from picture 1 (element)",
    "kanji_list": [
      {"character": "日", "han_viet": "Nhat", "onyomi": ["\u30cb\u30c1", "\u30b8\u30c4"], "kunyomi": ["\u3072", "-\u3073", "-\u304b"], "meaning_vi": "Mat troi, ngay", "examples": [{"word": "\u65e5\u672c", "hiragana": "\u306b\u307b\u3093", "meaning": "Nhat Ban"}, {"word": "\u65e5\u66dc\u65e5", "hiragana": "\u306b\u3061\u3088\u3046\u3073", "meaning": "Chu nhat"}, {"word": "\u6bce\u65e5", "hiragana": "\u307e\u3044\u306b\u3061", "meaning": "Hang ngay"}, {"word": "\u4eca\u65e5", "hiragana": "\u304d\u3087\u3046", "meaning": "Hom nay"}]},
      {"character": "月", "han_viet": "Nguyet", "onyomi": ["\u30b2\u30c4", "\u30ac\u30c4"], "kunyomi": ["\u3064\u304d"], "meaning_vi": "Mat trang, thang", "examples": [{"word": "\u6708\u66dc\u65e5", "hiragana": "\u3052\u3064\u3088\u3046\u3073", "meaning": "Thu Hai"}, {"word": "\u4e00\u6708", "hiragana": "\u3044\u3061\u304c\u3064", "meaning": "Thang mot"}, {"word": "\u4eca\u6708", "hiragana": "\u3053\u3093\u3052\u3064", "meaning": "Thang nay"}, {"word": "\u6708", "hiragana": "\u3064\u304d", "meaning": "Mat trang"}]},
      {"character": "金", "han_viet": "Kim", "onyomi": ["\u30ad\u30f3", "\u30b3\u30f3"], "kunyomi": ["\u304b\u306d", "\u304b\u306a-"], "meaning_vi": "Vang, tien", "examples": [{"word": "\u91d1\u66dc\u65e5", "hiragana": "\u304d\u3093\u3088\u3046\u3073", "meaning": "Thu Sau"}, {"word": "\u304a\u91d1", "hiragana": "\u304a\u304b\u306d", "meaning": "Tien"}, {"word": "\u304a\u91d1\u6301\u3061", "hiragana": "\u304a\u304b\u306d\u3082\u3061", "meaning": "Nguoi giau"}, {"word": "\u73fe\u91d1", "hiragana": "\u3052\u3093\u304d\u3093", "meaning": "Tien mat"}]},
      {"character": "水", "han_viet": "Thuy", "onyomi": ["\u30b9\u30a4"], "kunyomi": ["\u307f\u305a"], "meaning_vi": "Nuoc", "examples": [{"word": "\u6c34\u66dc\u65e5", "hiragana": "\u3059\u3044\u3088\u3046\u3073", "meaning": "Thu Tu"}, {"word": "\u6c34", "hiragana": "\u307f\u305a", "meaning": "Nuoc"}, {"word": "\u6c34\u6cf3", "hiragana": "\u3059\u3044\u3048\u3044", "meaning": "Boi loi"}, {"word": "\u6c34\u9053", "hiragana": "\u3059\u3044\u3069\u3046", "meaning": "Nuoc may"}]},
      {"character": "火", "han_viet": "Hoa", "onyomi": ["\u30ab"], "kunyomi": ["\u3072"], "meaning_vi": "Lua", "examples": [{"word": "\u706b\u66dc\u65e5", "hiragana": "\u304b\u3088\u3046\u3073", "meaning": "Thu Ba"}, {"word": "\u706b", "hiragana": "\u3072", "meaning": "Lua"}, {"word": "\u706b\u4e8b", "hiragana": "\u304b\u3058", "meaning": "Hoa hoan"}, {"word": "\u82b1\u706b", "hiragana": "\u306f\u306a\u3073", "meaning": "Phao hoa"}]},
      {"character": "木", "han_viet": "Moc", "onyomi": ["\u30e2\u30af", "\u30dc\u30af"], "kunyomi": ["\u304d"], "meaning_vi": "Cay", "examples": [{"word": "\u6728\u66dc\u65e5", "hiragana": "\u3082\u304f\u3088\u3046\u3073", "meaning": "Thu Nam"}, {"word": "\u6728", "hiragana": "\u304d", "meaning": "Cay"}, {"word": "\u6728\u6750", "hiragana": "\u3082\u304f\u3056\u3044", "meaning": "Vat lieu go"}]},
      {"character": "土", "han_viet": "Tho", "onyomi": ["\u30c9", "\u30c8"], "kunyomi": ["\u3064\u3061"], "meaning_vi": "Dat", "examples": [{"word": "\u571f\u66dc\u65e5", "hiragana": "\u3069\u3088\u3046\u3073", "meaning": "Thu Bay"}, {"word": "\u571f", "hiragana": "\u3064\u3061", "meaning": "Dat"}, {"word": "\u571f\u5730", "hiragana": "\u3068\u3061", "meaning": "Dat dai"}, {"word": "\u304a\u571f\u7523", "hiragana": "\u304a\u307f\u3084\u3052", "meaning": "Qua dac san"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 2,
    "topic": "Kanji made from picture 2 (nature)",
    "kanji_list": [
      {"character": "車", "han_viet": "Xa", "onyomi": ["\u30b7\u30e3"], "kunyomi": ["\u304f\u308b\u307e"], "meaning_vi": "Xe", "examples": [{"word": "\u96fb\u8eca", "hiragana": "\u3067\u3093\u3057\u3083", "meaning": "Tau dien"}, {"word": "\u8eca", "hiragana": "\u304f\u308b\u307e", "meaning": "Xe o to"}, {"word": "\u81ea\u8ee2\u8eca", "hiragana": "\u3058\u3066\u3093\u3057\u3083", "meaning": "Xe dap"}, {"word": "\u81ea\u52d5\u8eca", "hiragana": "\u3058\u3069\u3046\u3057\u3083", "meaning": "Xe hoi"}]},
      {"character": "門", "han_viet": "Mon", "onyomi": ["\u30e2\u30f3"], "kunyomi": ["\u304b\u3069"], "meaning_vi": "Cong", "examples": [{"word": "\u5c02\u9580", "hiragana": "\u305b\u3093\u3082\u3093", "meaning": "Chuyen mon"}, {"word": "\u9580", "hiragana": "\u3082\u3093", "meaning": "Cong"}, {"word": "\u6821\u9580", "hiragana": "\u3053\u3046\u3082\u3093", "meaning": "Cong truong"}]},
      {"character": "田", "han_viet": "Dien", "onyomi": ["\u30c7\u30f3"], "kunyomi": ["\u305f"], "meaning_vi": "Ruong", "examples": [{"word": "\u7530\u3093\u307c", "hiragana": "\u305f\u3093\u307c", "meaning": "Ruong lua"}, {"word": "\u6c34\u7530", "hiragana": "\u3059\u3044\u3067\u3093", "meaning": "Ruong nuoc"}, {"word": "\u7530\u820e", "hiragana": "\u3044\u306a\u304b", "meaning": "Que huong"}, {"word": "\u5c71\u7530\u3055\u3093", "hiragana": "\u3084\u307e\u3060\u3055\u3093", "meaning": "Anh/Chi Yamada"}]},
      {"character": "山", "han_viet": "Son", "onyomi": ["\u30b5\u30f3"], "kunyomi": ["\u3084\u307e"], "meaning_vi": "Nui", "examples": [{"word": "\u5bcc\u58eb\u5c71", "hiragana": "\u3075\u3058\u3055\u3093", "meaning": "Nui Phu Si"}, {"word": "\u5c71", "hiragana": "\u3084\u307e", "meaning": "Nui"}, {"word": "\u767b\u5c71", "hiragana": "\u3068\u3056\u3093", "meaning": "Leo nui"}, {"word": "\u706b\u5c71", "hiragana": "\u304b\u3056\u3093", "meaning": "Nui lua"}]},
      {"character": "川", "han_viet": "Xuyen", "onyomi": ["\u30bb\u30f3"], "kunyomi": ["\u304b\u308f"], "meaning_vi": "Song", "examples": [{"word": "\u5ddd", "hiragana": "\u304b\u308f", "meaning": "Song"}, {"word": "\u5c0f\u5ddd", "hiragana": "\u304a\u304c\u308f", "meaning": "Suoi nho"}, {"word": "\u30ca\u30a4\u30eb\u5ddd", "hiragana": "\u306a\u3044\u308b\u304c\u308f", "meaning": "Song Nile"}]},
      {"character": "雨", "han_viet": "Vu", "onyomi": ["\u30a6"], "kunyomi": ["\u3042\u3081", "\u3042\u307e-"], "meaning_vi": "Mua", "examples": [{"word": "\u96e8", "hiragana": "\u3042\u3081", "meaning": "Mua"}, {"word": "\u5927\u96e8", "hiragana": "\u304a\u304a\u3042\u3081", "meaning": "Mua lon"}, {"word": "\u6885\u96e8", "hiragana": "\u3064\u3086", "meaning": "Mua mua"}]},
      {"character": "天", "han_viet": "Thien", "onyomi": ["\u30c6\u30f3"], "kunyomi": ["\u3042\u3081", "\u3042\u307e"], "meaning_vi": "Troi", "examples": [{"word": "\u5929\u6c17", "hiragana": "\u3066\u3093\u304d", "meaning": "Thoi tiet"}, {"word": "\u5929\u56fd", "hiragana": "\u3066\u3093\u3054\u304f", "meaning": "Thien duong"}, {"word": "\u5929\u624d", "hiragana": "\u3066\u3093\u3055\u3044", "meaning": "Thien tai"}]},
      {"character": "気", "han_viet": "Khi", "onyomi": ["\u30ad", "\u30b1"], "kunyomi": ["\u3044\u304d"], "meaning_vi": "Khi, tinh than", "examples": [{"word": "\u5143\u6c17", "hiragana": "\u3052\u3093\u304d", "meaning": "Khoe manh"}, {"word": "\u5929\u6c17", "hiragana": "\u3066\u3093\u304d", "meaning": "Thoi tiet"}, {"word": "\u96fb\u6c17", "hiragana": "\u3067\u3093\u304d", "meaning": "Dien"}, {"word": "\u6c17\u6301\u3061", "hiragana": "\u304d\u3082\u3061", "meaning": "Cam giac"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 3,
    "topic": "Kanji for human relationships 1",
    "kanji_list": [
      {"character": "父", "han_viet": "Phu", "onyomi": ["\u30d5"], "kunyomi": ["\u3061\u3061"], "meaning_vi": "Bo", "examples": [{"word": "\u304a\u7236\u3055\u3093", "hiragana": "\u304a\u3068\u3046\u3055\u3093", "meaning": "Bo (nguoi khac)"}, {"word": "\u7236", "hiragana": "\u3061\u3061", "meaning": "Bo (minh)"}, {"word": "\u7956\u7236", "hiragana": "\u305d\u3075", "meaning": "Ong"}]},
      {"character": "母", "han_viet": "Mau", "onyomi": ["\u30dc"], "kunyomi": ["\u306f\u306f"], "meaning_vi": "Me", "examples": [{"word": "\u304a\u6bcd\u3055\u3093", "hiragana": "\u304a\u304b\u3042\u3055\u3093", "meaning": "Me (nguoi khac)"}, {"word": "\u6bcd", "hiragana": "\u306f\u306f", "meaning": "Me (minh)"}, {"word": "\u7956\u6bcd", "hiragana": "\u305d\u307c", "meaning": "Ba"}]},
      {"character": "私", "han_viet": "Tu", "onyomi": ["\u30b7"], "kunyomi": ["\u308f\u305f\u3057", "\u308f\u305f\u304f\u3057"], "meaning_vi": "Toi", "examples": [{"word": "\u79c1", "hiragana": "\u308f\u305f\u3057", "meaning": "Toi"}, {"word": "\u79c1\u305f\u3061", "hiragana": "\u308f\u305f\u3057\u305f\u3061", "meaning": "Chung toi"}, {"word": "\u79c1\u7acb\u5927\u5b66", "hiragana": "\u3057\u308a\u3064\u3060\u3044\u304c\u304f", "meaning": "Dai hoc tu thuc"}]},
      {"character": "兄", "han_viet": "Huynh", "onyomi": ["\u30b1\u30a4", "\u30ad\u30e7\u30a6"], "kunyomi": ["\u3042\u306b"], "meaning_vi": "Anh trai", "examples": [{"word": "\u304a\u5144\u3055\u3093", "hiragana": "\u304a\u306b\u3044\u3055\u3093", "meaning": "Anh trai (nguoi khac)"}, {"word": "\u5144", "hiragana": "\u3042\u306b", "meaning": "Anh trai (minh)"}, {"word": "\u5144\u5f1f", "hiragana": "\u304d\u3087\u3046\u3060\u3044", "meaning": "Anh em"}]},
      {"character": "姉", "han_viet": "Ty", "onyomi": ["\u30b7"], "kunyomi": ["\u3042\u306d"], "meaning_vi": "Chi gai", "examples": [{"word": "\u304a\u59c9\u3055\u3093", "hiragana": "\u304a\u306d\u3048\u3055\u3093", "meaning": "Chi gai (nguoi khac)"}, {"word": "\u59c9", "hiragana": "\u3042\u306d", "meaning": "Chi gai (minh)"}, {"word": "\u59c9\u59b9", "hiragana": "\u3057\u307e\u3044", "meaning": "Chi em"}]},
      {"character": "弟", "han_viet": "De", "onyomi": ["\u30c6\u30a4"], "kunyomi": ["\u304a\u3068\u3046\u3068"], "meaning_vi": "Em trai", "examples": [{"word": "\u5f1f", "hiragana": "\u304a\u3068\u3046\u3068", "meaning": "Em trai"}, {"word": "\u5f1f\u3055\u3093", "hiragana": "\u304a\u3068\u3046\u3068\u3055\u3093", "meaning": "Em trai (nguoi khac)"}, {"word": "\u5f1f\u5b50", "hiragana": "\u3067\u3057", "meaning": "De tu"}]},
      {"character": "妹", "han_viet": "Muoi", "onyomi": ["\u30de\u30a4"], "kunyomi": ["\u3044\u3082\u3046\u3068"], "meaning_vi": "Em gai", "examples": [{"word": "\u59b9", "hiragana": "\u3044\u3082\u3046\u3068", "meaning": "Em gai"}, {"word": "\u59b9\u3055\u3093", "hiragana": "\u3044\u3082\u3046\u3068\u3055\u3093", "meaning": "Em gai (nguoi khac)"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 4,
    "topic": "Numbers",
    "kanji_list": [
      {"character": "一", "han_viet": "Nhat", "onyomi": ["\u30a4\u30c1", "\u30a4\u30c4"], "kunyomi": ["\u3072\u3068-"], "meaning_vi": "Mot", "examples": [{"word": "\u4e00\u3064", "hiragana": "\u3072\u3068\u3064", "meaning": "1 cai"}, {"word": "\u4e00\u4eba", "hiragana": "\u3072\u3068\u308a", "meaning": "1 nguoi"}, {"word": "\u4e00\u65e5", "hiragana": "\u3064\u3044\u305f\u3061", "meaning": "Ngay mung 1"}, {"word": "\u4e00\u6708", "hiragana": "\u3044\u3061\u304c\u3064", "meaning": "Thang 1"}]},
      {"character": "二", "han_viet": "Nhi", "onyomi": ["\u30cb"], "kunyomi": ["\u3075\u305f"], "meaning_vi": "Hai", "examples": [{"word": "\u4e8c\u3064", "hiragana": "\u3075\u305f\u3064", "meaning": "2 cai"}, {"word": "\u4e8c\u4eba", "hiragana": "\u3075\u305f\u308a", "meaning": "2 nguoi"}, {"word": "\u4e8c\u65e5", "hiragana": "\u3075\u3064\u304b", "meaning": "Ngay mung 2"}, {"word": "\u4e8c\u6708", "hiragana": "\u306b\u304c\u3064", "meaning": "Thang 2"}]},
      {"character": "三", "han_viet": "Tam", "onyomi": ["\u30b5\u30f3"], "kunyomi": ["\u307f", "\u307f\u3063-"], "meaning_vi": "Ba", "examples": [{"word": "\u4e09\u3064", "hiragana": "\u307f\u3063\u3064", "meaning": "3 cai"}, {"word": "\u4e09\u65e5", "hiragana": "\u307f\u3063\u304b", "meaning": "Ngay mung 3"}, {"word": "\u4e09\u6708", "hiragana": "\u3055\u3093\u304c\u3064", "meaning": "Thang 3"}]},
      {"character": "四", "han_viet": "Tu", "onyomi": ["\u30b7"], "kunyomi": ["\u3088", "\u3088\u3093"], "meaning_vi": "Bon", "examples": [{"word": "\u56db\u3064", "hiragana": "\u3088\u3063\u3064", "meaning": "4 cai"}, {"word": "\u56db\u65e5", "hiragana": "\u3088\u3063\u304b", "meaning": "Ngay mung 4"}, {"word": "\u56db\u6708", "hiragana": "\u3057\u304c\u3064", "meaning": "Thang 4"}]},
      {"character": "五", "han_viet": "Ngu", "onyomi": ["\u30b4"], "kunyomi": ["\u3044\u3064"], "meaning_vi": "Nam", "examples": [{"word": "\u4e94\u3064", "hiragana": "\u3044\u3064\u3064", "meaning": "5 cai"}, {"word": "\u4e94\u65e5", "hiragana": "\u3044\u3064\u304b", "meaning": "Ngay mung 5"}, {"word": "\u4e94\u6708", "hiragana": "\u3054\u304c\u3064", "meaning": "Thang 5"}]},
      {"character": "六", "han_viet": "Luc", "onyomi": ["\u30ed\u30af"], "kunyomi": ["\u3080", "\u3080\u3063-"], "meaning_vi": "Sau", "examples": [{"word": "\u516d\u3064", "hiragana": "\u3080\u3063\u3064", "meaning": "6 cai"}, {"word": "\u516d\u65e5", "hiragana": "\u3080\u3044\u304b", "meaning": "Ngay mung 6"}, {"word": "\u516d\u6708", "hiragana": "\u308d\u304f\u304c\u3064", "meaning": "Thang 6"}]},
      {"character": "七", "han_viet": "That", "onyomi": ["\u30b7\u30c1"], "kunyomi": ["\u306a\u306a", "\u306a\u306e"], "meaning_vi": "Bay", "examples": [{"word": "\u4e03\u3064", "hiragana": "\u306a\u306a\u3064", "meaning": "7 cai"}, {"word": "\u4e03\u65e5", "hiragana": "\u306a\u306e\u304b", "meaning": "Ngay mung 7"}, {"word": "\u4e03\u6708", "hiragana": "\u3057\u3061\u304c\u3064", "meaning": "Thang 7"}]},
      {"character": "八", "han_viet": "Bat", "onyomi": ["\u30cf\u30c1"], "kunyomi": ["\u3084", "\u3084\u3063-"], "meaning_vi": "Tam", "examples": [{"word": "\u516b\u3064", "hiragana": "\u3084\u3063\u3064", "meaning": "8 cai"}, {"word": "\u516b\u65e5", "hiragana": "\u3088\u3046\u304b", "meaning": "Ngay mung 8"}, {"word": "\u516b\u6708", "hiragana": "\u306f\u3061\u304c\u3064", "meaning": "Thang 8"}]},
      {"character": "九", "han_viet": "Cuu", "onyomi": ["\u30ad\u30e5\u30a6", "\u30af"], "kunyomi": ["\u3053\u3053\u306e"], "meaning_vi": "Chin", "examples": [{"word": "\u4e5d\u3064", "hiragana": "\u3053\u3053\u306e\u3064", "meaning": "9 cai"}, {"word": "\u4e5d\u65e5", "hiragana": "\u3053\u3053\u306e\u304b", "meaning": "Ngay mung 9"}, {"word": "\u4e5d\u6708", "hiragana": "\u304f\u304c\u3064", "meaning": "Thang 9"}]},
      {"character": "十", "han_viet": "Thap", "onyomi": ["\u30b8\u30e5\u30a6"], "kunyomi": ["\u3068\u304a", "\u3068"], "meaning_vi": "Muoi", "examples": [{"word": "\u5341", "hiragana": "\u3068\u304a", "meaning": "10 cai"}, {"word": "\u5341\u65e5", "hiragana": "\u3068\u304a\u304b", "meaning": "Ngay mung 10"}, {"word": "\u5341\u6708", "hiragana": "\u3058\u3085\u3046\u304c\u3064", "meaning": "Thang 10"}, {"word": "\u5341\u5206", "hiragana": "\u3058\u3085\u3046\u3076\u3093", "meaning": "Du"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 5,
    "topic": "Numbers 2",
    "kanji_list": [
      {"character": "百", "han_viet": "Bach", "onyomi": ["\u30d2\u30e3\u30af"], "kunyomi": ["\u3082\u3082"], "meaning_vi": "Tram", "examples": [{"word": "\u767e", "hiragana": "\u3072\u3083\u304f", "meaning": "100"}, {"word": "\u4e09\u767e", "hiragana": "\u3055\u3093\u3073\u3083\u304f", "meaning": "300"}, {"word": "\u516d\u767e", "hiragana": "\u308d\u3063\u3074\u3083\u304f", "meaning": "600"}]},
      {"character": "千", "han_viet": "Thien", "onyomi": ["\u30bb\u30f3"], "kunyomi": ["\u3061"], "meaning_vi": "Nghin", "examples": [{"word": "\u5343", "hiragana": "\u305b\u3093", "meaning": "1000"}, {"word": "\u4e09\u5343", "hiragana": "\u3055\u3093\u305c\u3093", "meaning": "3000"}, {"word": "\u5343\u8449", "hiragana": "\u3061\u3070", "meaning": "Tinh Chiba"}]},
      {"character": "万", "han_viet": "Van", "onyomi": ["\u30de\u30f3"], "kunyomi": ["\u3088\u308d\u305a"], "meaning_vi": "Van (Muoi nghin)", "examples": [{"word": "\u4e00\u4e07", "hiragana": "\u3044\u3061\u307e\u3093", "meaning": "1 van (10.000)"}, {"word": "\u4e07\u56fd", "hiragana": "\u3070\u3093\u3053\u304f", "meaning": "Van quoc"}, {"word": "\u4e07\u6b73", "hiragana": "\u3070\u3093\u3056\u3044", "meaning": "Van tue"}]},
      {"character": "円", "han_viet": "Vien", "onyomi": ["\u30a8\u30f3"], "kunyomi": ["\u307e\u308b", "\u3048\u3093"], "meaning_vi": "Yen, tron", "examples": [{"word": "\u767e\u5186", "hiragana": "\u3072\u3083\u304f\u3048\u3093", "meaning": "100 yen"}, {"word": "\u5186\u9ad8", "hiragana": "\u3048\u3093\u3060\u304b", "meaning": "Yen tang gia"}, {"word": "\u5186\u3044", "hiragana": "\u307e\u308b\u3044", "meaning": "Tron"}]},
      {"character": "年", "han_viet": "Nien", "onyomi": ["\u30cd\u30f3"], "kunyomi": ["\u3068\u3057"], "meaning_vi": "Nam", "examples": [{"word": "\u53bb\u5e74", "hiragana": "\u304d\u3087\u306d\u3093", "meaning": "Nam ngoai"}, {"word": "\u4eca\u5e74", "hiragana": "\u3053\u3068\u3057", "meaning": "Nam nay"}, {"word": "\u6765\u5e74", "hiragana": "\u3089\u3044\u306e\u3093", "meaning": "Nam sau"}]},
      {"character": "半", "han_viet": "Ban", "onyomi": ["\u30cf\u30f3"], "kunyomi": ["\u306a\u304b-"], "meaning_vi": "Mot nua", "examples": [{"word": "\u534a\u5206", "hiragana": "\u306f\u3093\u3076\u3093", "meaning": "Mot nua"}, {"word": "\u534a\u5e74", "hiragana": "\u306f\u3093\u3068\u3057", "meaning": "Nua nam"}, {"word": "\u4e09\u6642\u534a", "hiragana": "\u3055\u3093\u3058\u306f\u3093", "meaning": "3 gio ruoi"}]},
      {"character": "分", "han_viet": "Phan", "onyomi": ["\u30d6\u30f3", "\u30d5\u30f3"], "kunyomi": ["\u308f-\u3051\u308b"], "meaning_vi": "Phut, chia", "examples": [{"word": "\u4e94\u5206", "hiragana": "\u3054\u3075\u3093", "meaning": "5 phut"}, {"word": "\u5206\u304b\u308b", "hiragana": "\u308f\u304b\u308b", "meaning": "Hieu"}, {"word": "\u81ea\u5206", "hiragana": "\u3058\u3076\u3093", "meaning": "Ban than"}]},
      {"character": "時", "han_viet": "Thoi", "onyomi": ["\u30b8"], "kunyomi": ["\u3068\u304d"], "meaning_vi": "Gio, thoi gian", "examples": [{"word": "\u6642\u9593", "hiragana": "\u3058\u304b\u3093", "meaning": "Thoi gian"}, {"word": "\u4e00\u6642", "hiragana": "\u3044\u3061\u3058", "meaning": "1 gio"}, {"word": "\u6642\u8a08", "hiragana": "\u3068\u3051\u3044", "meaning": "Dong ho"}, {"word": "\u6642\u3005", "hiragana": "\u3068\u304d\u3069\u304d", "meaning": "Thinh thoang"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 6,
    "topic": "Kanji made from picture 3 (human)",
    "kanji_list": [
      {"character": "人", "han_viet": "Nhan", "onyomi": ["\u30b8\u30f3", "\u30cb\u30f3"], "kunyomi": ["\u3072\u3068"], "meaning_vi": "Nguoi", "examples": [{"word": "\u65e5\u672c\u4eba", "hiragana": "\u306b\u307b\u3093\u3058\u3093", "meaning": "Nguoi Nhat"}, {"word": "\u4eba", "hiragana": "\u3072\u3068", "meaning": "Nguoi"}, {"word": "\u4e00\u4eba", "hiragana": "\u3072\u3068\u308a", "meaning": "Mot nguoi"}]},
      {"character": "女", "han_viet": "Nu", "onyomi": ["\u30b8\u30e7", "\u30cb\u30e7"], "kunyomi": ["\u304a\u3093\u306a"], "meaning_vi": "Phu nu", "examples": [{"word": "\u5973", "hiragana": "\u304a\u3093\u306a", "meaning": "Phu nu"}, {"word": "\u5973\u6027", "hiragana": "\u3058\u3087\u305b\u3044", "meaning": "Gioi nu"}, {"word": "\u5973\u306e\u5b50", "hiragana": "\u304a\u3093\u306a\u306e\u3053", "meaning": "Be gai"}]},
      {"character": "生", "han_viet": "Sinh", "onyomi": ["\u30bb\u30a4", "\u30b7\u30e7\u30a6"], "kunyomi": ["\u3044-\u304d\u308b", "\u3046-\u307e\u308c\u308b"], "meaning_vi": "Song, sinh ra", "examples": [{"word": "\u751f\u304d\u308b", "hiragana": "\u3044\u304d\u308b", "meaning": "Song"}, {"word": "\u751f\u307e\u308c\u308b", "hiragana": "\u3046\u307e\u308c\u308b", "meaning": "Duoc sinh ra"}, {"word": "\u5148\u751f", "hiragana": "\u305b\u3093\u305b\u3044", "meaning": "Giao vien"}]},
      {"character": "子", "han_viet": "Tu", "onyomi": ["\u30b7"], "kunyomi": ["\u3053"], "meaning_vi": "Con, tre em", "examples": [{"word": "\u5b50\u4f9b", "hiragana": "\u3053\u3069\u3082", "meaning": "Tre em"}, {"word": "\u96fb\u5b50", "hiragana": "\u3067\u3093\u3057", "meaning": "Dien tu"}, {"word": "\u5e3d\u5b50", "hiragana": "\u307c\u3046\u3057", "meaning": "Mu"}]},
      {"character": "学", "han_viet": "Hoc", "onyomi": ["\u30ac\u30af"], "kunyomi": ["\u307e\u306a-\u3076"], "meaning_vi": "Hoc", "examples": [{"word": "\u5b66\u751f", "hiragana": "\u304c\u304f\u305b\u3044", "meaning": "Hoc sinh"}, {"word": "\u5b66\u6821", "hiragana": "\u304c\u3063\u3053\u3046", "meaning": "Truong hoc"}, {"word": "\u5927\u5b66", "hiragana": "\u3060\u3044\u304c\u304f", "meaning": "Dai hoc"}]},
      {"character": "先", "han_viet": "Tien", "onyomi": ["\u30bb\u30f3"], "kunyomi": ["\u3055\u304d"], "meaning_vi": "Truoc", "examples": [{"word": "\u5148\u751f", "hiragana": "\u305b\u3093\u305b\u3044", "meaning": "Giao vien"}, {"word": "\u5148\u6708", "hiragana": "\u305b\u3093\u3052\u3064", "meaning": "Thang truoc"}, {"word": "\u304a\u5148\u306b", "hiragana": "\u304a\u3055\u304d\u306b", "meaning": "Truoc (xin phep)"}]},
      {"character": "白", "han_viet": "Bach", "onyomi": ["\u30cf\u30af", "\u30d3\u30e3\u30af"], "kunyomi": ["\u3057\u308d", "\u3057\u3089-"], "meaning_vi": "Trang", "examples": [{"word": "\u767d", "hiragana": "\u3057\u308d", "meaning": "Mau trang"}, {"word": "\u767d\u3044", "hiragana": "\u3057\u308d\u3044", "meaning": "Trang (tinh tu)"}, {"word": "\u9762\u767d\u3044", "hiragana": "\u304a\u3082\u3057\u308d\u3044", "meaning": "Thu vi"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 7,
    "topic": "Kanji made from picture 4 (body)",
    "kanji_list": [
      {"character": "口", "han_viet": "Khau", "onyomi": ["\u30b3\u30a6", "\u30af"], "kunyomi": ["\u304f\u3061"], "meaning_vi": "Mieng", "examples": [{"word": "\u53e3", "hiragana": "\u304f\u3061", "meaning": "Mieng"}, {"word": "\u51fa\u53e3", "hiragana": "\u3067\u3050\u3061", "meaning": "Cua ra"}, {"word": "\u5165\u53e3", "hiragana": "\u3044\u308a\u3050\u3061", "meaning": "Cua vao"}, {"word": "\u4eba\u53e3", "hiragana": "\u3058\u3093\u3053\u3046", "meaning": "Dan so"}]},
      {"character": "石", "han_viet": "Thach", "onyomi": ["\u30bb\u30ad", "\u30b7\u30e3\u30af"], "kunyomi": ["\u3044\u3057"], "meaning_vi": "Da", "examples": [{"word": "\u77f3", "hiragana": "\u3044\u3057", "meaning": "Da"}, {"word": "\u77f3\u6cb9", "hiragana": "\u305b\u304d\u3086", "meaning": "Dau mo"}, {"word": "\u5316\u77f3", "hiragana": "\u304b\u305b\u304d", "meaning": "Hoa thach"}]},
      {"character": "手", "han_viet": "Thu", "onyomi": ["\u30b7\u30e5"], "kunyomi": ["\u3066"], "meaning_vi": "Tay", "examples": [{"word": "\u624b", "hiragana": "\u3066", "meaning": "Tay"}, {"word": "\u624b\u7d19", "hiragana": "\u3066\u304c\u307f", "meaning": "Buc thu"}, {"word": "\u5207\u624b", "hiragana": "\u304d\u3063\u3066", "meaning": "Tem"}, {"word": "\u6b4c\u624b", "hiragana": "\u304b\u3057\u3085", "meaning": "Ca si"}]},
      {"character": "足", "han_viet": "Tuc", "onyomi": ["\u30bd\u30af"], "kunyomi": ["\u3042\u3057", "\u305f-\u308a\u308b"], "meaning_vi": "Chan, du", "examples": [{"word": "\u8db3", "hiragana": "\u3042\u3057", "meaning": "Chan"}, {"word": "\u8db3\u308a\u308b", "hiragana": "\u305f\u308a\u308b", "meaning": "Du"}, {"word": "\u4e00\u8db3", "hiragana": "\u3044\u3063\u305d\u304f", "meaning": "Mot doi (giay/tat)"}, {"word": "\u9060\u8db3", "hiragana": "\u3048\u3093\u305d\u304f", "meaning": "Da ngoai"}]},
      {"character": "耳", "han_viet": "Nhi", "onyomi": ["\u30b8"], "kunyomi": ["\u307f\u307f"], "meaning_vi": "Tai", "examples": [{"word": "\u8033", "hiragana": "\u307f\u307f", "meaning": "Tai"}, {"word": "\u8033\u9f3b\u79d1", "hiragana": "\u3058\u3073\u304b", "meaning": "Khoa tai mui hong"}]},
      {"character": "目", "han_viet": "Muc", "onyomi": ["\u30e2\u30af", "\u30dc\u30af"], "kunyomi": ["\u3081", "\u307e-"], "meaning_vi": "Mat", "examples": [{"word": "\u76ee", "hiragana": "\u3081", "meaning": "Mat"}, {"word": "\u76ee\u7684", "hiragana": "\u3082\u304f\u3066\u304d", "meaning": "Muc dich"}, {"word": "\u76ee\u85ac", "hiragana": "\u3081\u3050\u3059\u308a", "meaning": "Thuoc nho mat"}, {"word": "\u4e8c\u756a\u76ee", "hiragana": "\u306b\u3070\u3093\u3081", "meaning": "Thu hai (theo thu tu)"}]},
      {"character": "体", "han_viet": "The", "onyomi": ["\u30bf\u30a4"], "kunyomi": ["\u304b\u3089\u3060"], "meaning_vi": "Co the", "examples": [{"word": "\u4f53", "hiragana": "\u304b\u3089\u3060", "meaning": "Co the"}, {"word": "\u4f53\u80b2", "hiragana": "\u305f\u3044\u3044\u304f", "meaning": "The duc"}, {"word": "\u4f53\u529b", "hiragana": "\u305f\u3044\u308a\u3087\u304f", "meaning": "The luc"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 8,
    "topic": "Kanji made from signs",
    "kanji_list": [
      {"character": "上", "han_viet": "Thuong", "onyomi": ["\u30b8\u30e7\u30a6"], "kunyomi": ["\u3046\u3048", "\u3046\u308f-"], "meaning_vi": "Tren", "examples": [{"word": "\u4e0a", "hiragana": "\u3046\u3048", "meaning": "Tren"}, {"word": "\u4e0a\u624b", "hiragana": "\u3058\u3087\u3046\u305a", "meaning": "Gioi"}, {"word": "\u5e74\u4e0a", "hiragana": "\u3068\u3057\u3046\u3048", "meaning": "Lon tuoi hon"}, {"word": "\u4e0a\u7740", "hiragana": "\u3046\u308f\u304e", "meaning": "Ao khoac"}]},
      {"character": "下", "han_viet": "Ha", "onyomi": ["\u30ab", "\u30b2"], "kunyomi": ["\u3057\u305f", "\u3055-"], "meaning_vi": "Duoi", "examples": [{"word": "\u4e0b", "hiragana": "\u3057\u305f", "meaning": "Duoi"}, {"word": "\u4e0b\u624b", "hiragana": "\u3078\u305f", "meaning": "Kem"}, {"word": "\u5730\u4e0b\u9244", "hiragana": "\u3061\u304b\u3066\u3064", "meaning": "Tau dien ngam"}, {"word": "\u9774\u4e0b", "hiragana": "\u304f\u3064\u3057\u305f", "meaning": "Tat"}]},
      {"character": "中", "han_viet": "Trung", "onyomi": ["\u30c1\u30e5\u30a6"], "kunyomi": ["\u306a\u304b"], "meaning_vi": "Trong, giua", "examples": [{"word": "\u4e2d", "hiragana": "\u306a\u304b", "meaning": "Ben trong"}, {"word": "\u4e2d\u56fd", "hiragana": "\u3061\u3085\u3046\u3054\u304f", "meaning": "Trung Quoc"}, {"word": "\u4e00\u65e5\u4e2d", "hiragana": "\u3044\u3061\u306b\u3061\u3058\u3085\u3046", "meaning": "Suot ca ngay"}, {"word": "\u4e2d\u5b66\u6821", "hiragana": "\u3061\u3085\u3046\u304c\u3063\u3053\u3046", "meaning": "Truong cap 2"}]},
      {"character": "大", "han_viet": "Dai", "onyomi": ["\u30c0\u30a4", "\u30bf\u30a4"], "kunyomi": ["\u304a\u304a-", "\u304a\u304a\u304d\u3044"], "meaning_vi": "To, lon", "examples": [{"word": "\u5927\u304d\u3044", "hiragana": "\u304a\u304a\u304d\u3044", "meaning": "To lon"}, {"word": "\u5927\u5b66", "hiragana": "\u3060\u3044\u304c\u304f", "meaning": "Dai hoc"}, {"word": "\u5927\u5207", "hiragana": "\u305f\u3044\u305b\u3064", "meaning": "Quan trong"}, {"word": "\u5927\u4eba", "hiragana": "\u304a\u3068\u306a", "meaning": "Nguoi lon"}]},
      {"character": "小", "han_viet": "Tieu", "onyomi": ["\u30b7\u30e7\u30a6"], "kunyomi": ["\u3061\u3044-\u3055\u3044", "\u3053-"], "meaning_vi": "Nho", "examples": [{"word": "\u5c0f\u3055\u3044", "hiragana": "\u3061\u3044\u3055\u3044", "meaning": "Nho"}, {"word": "\u5c0f\u5b66\u6821", "hiragana": "\u3057\u3087\u3046\u304c\u3063\u3053\u3046", "meaning": "Truong tieu hoc"}, {"word": "\u5c0f\u5ddd", "hiragana": "\u304a\u304c\u308f", "meaning": "Suoi nho"}, {"word": "\u5c0f\u9ce5", "hiragana": "\u3053\u3068\u308a", "meaning": "Chim non"}]},
      {"character": "本", "han_viet": "Ban", "onyomi": ["\u30db\u30f3"], "kunyomi": ["\u3082\u3068"], "meaning_vi": "Sach, goc", "examples": [{"word": "\u672c", "hiragana": "\u307b\u3093", "meaning": "Sach"}, {"word": "\u65e5\u672c", "hiragana": "\u306b\u307b\u3093", "meaning": "Nhat Ban"}, {"word": "\u672c\u5c4b", "hiragana": "\u307b\u3093\u3084", "meaning": "Hieu sach"}, {"word": "\u5c71\u672c\u3055\u3093", "hiragana": "\u3084\u307e\u3082\u3068\u3055\u3093", "meaning": "Anh/Chi Yamamoto"}]},
      {"character": "力", "han_viet": "Luc", "onyomi": ["\u30ea\u30e7\u30af", "\u30ea\u30ad"], "kunyomi": ["\u3061\u304b\u3089"], "meaning_vi": "Suc luc", "examples": [{"word": "\u529b", "hiragana": "\u3061\u304b\u3089", "meaning": "Suc luc"}, {"word": "\u4f53\u529b", "hiragana": "\u305f\u3044\u308a\u3087\u304f", "meaning": "The luc"}, {"word": "\u5354\u529b", "hiragana": "\u304d\u3087\u3046\u308a\u3087\u304f", "meaning": "Hop tac"}, {"word": "\u80fd\u529b", "hiragana": "\u306e\u3046\u308a\u3087\u304f", "meaning": "Nang luc"}]},
      {"character": "何", "han_viet": "Ha", "onyomi": ["\u30ab"], "kunyomi": ["\u306a\u306b", "\u306a\u3093-"], "meaning_vi": "Cai gi", "examples": [{"word": "\u4f55", "hiragana": "\u306a\u306b", "meaning": "Cai gi"}, {"word": "\u4f55\u6642", "hiragana": "\u306a\u3093\u3058", "meaning": "May gio"}, {"word": "\u4f55\u4eba", "hiragana": "\u306a\u3093\u306b\u3093", "meaning": "May nguoi"}, {"word": "\u4f55\u304b", "hiragana": "\u306a\u306b\u304b", "meaning": "Cai gi do"}]},
      {"character": "出", "han_viet": "Xuat", "onyomi": ["\u30b7\u30e5\u30c4"], "kunyomi": ["\u3067-\u308b"], "meaning_vi": "Ra ngoai", "examples": [{"word": "\u51fa\u308b", "hiragana": "\u3067\u308b", "meaning": "Di ra"}, {"word": "\u51fa\u3059", "hiragana": "\u3060\u3059", "meaning": "Lay ra, nop"}, {"word": "\u51fa\u53e3", "hiragana": "\u3067\u3050\u3061", "meaning": "Cua ra"}, {"word": "\u5916\u51fa", "hiragana": "\u304c\u3044\u3057\u3085\u3064", "meaning": "Di ra ngoai"}]},
      {"character": "入", "han_viet": "Nhap", "onyomi": ["\u30cb\u30e5\u30a6"], "kunyomi": ["\u3044-\u308b", "\u306f\u3044-\u308b"], "meaning_vi": "Vao trong", "examples": [{"word": "\u5165\u308b", "hiragana": "\u306f\u3044\u308b", "meaning": "Di vao"}, {"word": "\u5165\u308c\u308b", "hiragana": "\u3044\u308c\u308b", "meaning": "Bo vao"}, {"word": "\u5165\u53e3", "hiragana": "\u3044\u308a\u3050\u3061", "meaning": "Cua vao"}, {"word": "\u5165\u5b66", "hiragana": "\u306b\u3085\u3046\u304c\u304f", "meaning": "Nhap hoc"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 9,
    "topic": "Kanji made from a combination of the meanings",
    "kanji_list": [
      {"character": "明", "han_viet": "Minh", "onyomi": ["\u30e1\u30a4"], "kunyomi": ["\u3042-\u304b\u308a", "\u3042\u304b-\u308b\u3044"], "meaning_vi": "Sang", "examples": [{"word": "\u660e\u308b\u3044", "hiragana": "\u3042\u304b\u308b\u3044", "meaning": "Sang sua"}, {"word": "\u660e\u65e5", "hiragana": "\u3042\u3057\u305f", "meaning": "Ngay mai"}, {"word": "\u8aac\u660e", "hiragana": "\u305b\u3064\u3081\u3044", "meaning": "Giai thich"}]},
      {"character": "休", "han_viet": "Huu", "onyomi": ["\u30ad\u30e5\u30a6"], "kunyomi": ["\u3084\u3059-\u3080"], "meaning_vi": "Nghi ngoi", "examples": [{"word": "\u4f11\u3080", "hiragana": "\u3084\u3059\u3080", "meaning": "Nghi"}, {"word": "\u4f11\u307f", "hiragana": "\u3084\u3059\u307f", "meaning": "Ngay nghi"}, {"word": "\u4f11\u65e5", "hiragana": "\u304d\u3085\u3046\u3058\u3064", "meaning": "Ngay nghi le"}, {"word": "\u590f\u4f11\u307f", "hiragana": "\u306a\u3064\u3084\u3059\u307f", "meaning": "Nghi he"}]},
      {"character": "好", "han_viet": "Hao", "onyomi": ["\u30b3\u30a6"], "kunyomi": ["\u3053\u306e-\u3080", "\u3059-\u304f"], "meaning_vi": "Thich", "examples": [{"word": "\u597d\u304d", "hiragana": "\u3059\u304d", "meaning": "Thich"}, {"word": "\u5927\u597d\u304d", "hiragana": "\u3060\u3044\u3059\u304d", "meaning": "Rat thich"}, {"word": "\u597d\u307f", "hiragana": "\u3053\u306e\u307f", "meaning": "So thich, gu"}]},
      {"character": "男", "han_viet": "Nam", "onyomi": ["\u30c0\u30f3", "\u30ca\u30f3"], "kunyomi": ["\u304a\u3068\u3053"], "meaning_vi": "Dan ong", "examples": [{"word": "\u7537", "hiragana": "\u304a\u3068\u3053", "meaning": "Dan ong"}, {"word": "\u7537\u306e\u5b50", "hiragana": "\u304a\u3068\u3053\u306e\u3053", "meaning": "Be trai"}, {"word": "\u7537\u6027", "hiragana": "\u3060\u3093\u305b\u3044", "meaning": "Nam gioi"}, {"word": "\u9577\u7537", "hiragana": "\u3061\u3087\u3046\u306a\u3093", "meaning": "Truong nam"}]},
      {"character": "間", "han_viet": "Gian", "onyomi": ["\u30ab\u30f3", "\u30b1\u30f3"], "kunyomi": ["\u3042\u3044\u3060", "\u307e"], "meaning_vi": "O giua, gian", "examples": [{"word": "\u6642\u9593", "hiragana": "\u3058\u304b\u3093", "meaning": "Thoi gian"}, {"word": "\u9593", "hiragana": "\u3042\u3044\u3060", "meaning": "O giua"}, {"word": "\u9593\u306b\u5408\u3046", "hiragana": "\u307e\u306b\u3042\u3046", "meaning": "Kip gio"}, {"word": "\u4ec7\u9593", "hiragana": "\u306a\u304b\u307e", "meaning": "Ban be, dong bon"}]},
      {"character": "岩", "han_viet": "Nham", "onyomi": ["\u30ac\u30f3"], "kunyomi": ["\u3044\u308f"], "meaning_vi": "Da tang", "examples": [{"word": "\u5ca9", "hiragana": "\u3044\u308f", "meaning": "Da tang"}, {"word": "\u5ca9\u5c71", "hiragana": "\u3044\u308f\u3084\u307e", "meaning": "Nui da"}]},
      {"character": "畑", "han_viet": "Dien (kho)", "onyomi": [], "kunyomi": ["\u306f\u305f", "\u306f\u305f\u3051"], "meaning_vi": "Ruong kho", "examples": [{"word": "\u7551", "hiragana": "\u306f\u305f\u3051", "meaning": "Ruong, vuon"}, {"word": "\u7530\u7551", "hiragana": "\u305f\u306f\u305f", "meaning": "Ruong dat"}]},
      {"character": "森", "han_viet": "Sam", "onyomi": ["\u30b7\u30f3"], "kunyomi": ["\u3082\u308a"], "meaning_vi": "Rung ram", "examples": [{"word": "\u68ee", "hiragana": "\u3082\u308a", "meaning": "Rung"}, {"word": "\u68ee\u6797", "hiragana": "\u3057\u3093\u308a\u3093", "meaning": "Rung ru"}, {"word": "\u9752\u68ee", "hiragana": "\u3042\u304a\u3082\u308a", "meaning": "Tinh Aomori"}]},
      {"character": "林", "han_viet": "Lam", "onyomi": ["\u30ea\u30f3"], "kunyomi": ["\u306f\u3084\u3057"], "meaning_vi": "Rung thua", "examples": [{"word": "\u6797", "hiragana": "\u306f\u3084\u3057", "meaning": "Rung thua"}, {"word": "\u5c0f\u6797\u3055\u3093", "hiragana": "\u3053\u3070\u3084\u3057\u3055\u3093", "meaning": "Anh/Chi Kobayashi"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 10,
    "topic": "Kanji carrying the meaning of Position 1",
    "kanji_list": [
      {"character": "右", "han_viet": "Huu", "onyomi": ["\u30a6"], "kunyomi": ["\u307f\u304e"], "meaning_vi": "Phai", "examples": [{"word": "\u53f3", "hiragana": "\u307f\u304e", "meaning": "Ben phai"}, {"word": "\u53f3\u624b", "hiragana": "\u307f\u304e\u3066", "meaning": "Tay phai"}, {"word": "\u5de6\u53f3", "hiragana": "\u3055\u3086\u3046", "meaning": "Trai phai"}]},
      {"character": "左", "han_viet": "Ta", "onyomi": ["\u30b5"], "kunyomi": ["\u3072\u3060\u308a"], "meaning_vi": "Trai", "examples": [{"word": "\u5de6", "hiragana": "\u3072\u3060\u308a", "meaning": "Ben trai"}, {"word": "\u5de6\u624b", "hiragana": "\u3072\u3060\u308a\u3066", "meaning": "Tay trai"}]},
      {"character": "東", "han_viet": "Dong", "onyomi": ["\u30c8\u30a6"], "kunyomi": ["\u3072\u304c\u3057"], "meaning_vi": "Phia dong", "examples": [{"word": "\u6771", "hiragana": "\u3072\u304c\u3057", "meaning": "Phia dong"}, {"word": "\u6771\u4eac", "hiragana": "\u3068\u3046\u304d\u3087\u3046", "meaning": "Tokyo"}, {"word": "\u95a2\u6771", "hiragana": "\u304b\u3093\u3068\u3046", "meaning": "Vung Kanto"}]},
      {"character": "西", "han_viet": "Tay", "onyomi": ["\u30bb\u30a4", "\u30b5\u30a4"], "kunyomi": ["\u306b\u3057"], "meaning_vi": "Phia tay", "examples": [{"word": "\u897f", "hiragana": "\u306b\u3057", "meaning": "Phia tay"}, {"word": "\u897f\u6d0b", "hiragana": "\u305b\u3044\u3088\u3046", "meaning": "Phuong tay"}, {"word": "\u95a2\u897f", "hiragana": "\u304b\u3093\u3055\u3044", "meaning": "Vung Kansai"}]},
      {"character": "北", "han_viet": "Bac", "onyomi": ["\u30db\u30af"], "kunyomi": ["\u304d\u305f"], "meaning_vi": "Phia bac", "examples": [{"word": "\u5317", "hiragana": "\u304d\u305f", "meaning": "Phia bac"}, {"word": "\u5317\u6d77\u9053", "hiragana": "\u307b\u3063\u304b\u3044\u3069\u3046", "meaning": "Hokkaido"}, {"word": "\u6771\u5317", "hiragana": "\u3068\u3046\u307b\u304f", "meaning": "Vung Tohoku"}]},
      {"character": "南", "han_viet": "Nam", "onyomi": ["\u30ca\u30f3"], "kunyomi": ["\u307f\u306a\u307f"], "meaning_vi": "Phia nam", "examples": [{"word": "\u5357", "hiragana": "\u307f\u306a\u307f", "meaning": "Phia nam"}, {"word": "\u6771\u5357\u30a2\u30b8\u30a2", "hiragana": "\u3068\u3046\u306a\u3093\u3042\u3058\u3042", "meaning": "Dong Nam A"}]},
      {"character": "外", "han_viet": "Ngoai", "onyomi": ["\u30ac\u30a4"], "kunyomi": ["\u305d\u3068"], "meaning_vi": "Ben ngoai", "examples": [{"word": "\u5916", "hiragana": "\u305d\u3068", "meaning": "Ben ngoai"}, {"word": "\u5916\u56fd", "hiragana": "\u304c\u3044\u3053\u304f", "meaning": "Nuoc ngoai"}, {"word": "\u6d77\u5916", "hiragana": "\u304b\u3044\u304c\u3044", "meaning": "Hai ngoai"}]},
      {"character": "駅", "han_viet": "Dich", "onyomi": ["\u30a8\u30ad"], "kunyomi": [], "meaning_vi": "Nha ga", "examples": [{"word": "\u99c5", "hiragana": "\u3048\u304d", "meaning": "Nha ga"}, {"word": "\u99c5\u9577", "hiragana": "\u3048\u304d\u3061\u3087\u3046", "meaning": "Truong ga"}, {"word": "\u99c5\u524d", "hiragana": "\u3048\u304d\u307e\u3048", "meaning": "Truoc nha ga"}]},
      {"character": "会", "han_viet": "Hoi", "onyomi": ["\u30ab\u30a4", "\u30a8"], "kunyomi": ["\u3042-\u3046"], "meaning_vi": "Gap go", "examples": [{"word": "\u4f1a\u3046", "hiragana": "\u3042\u3046", "meaning": "Gap"}, {"word": "\u4f1a\u793e", "hiragana": "\u304b\u3044\u3057\u3083", "meaning": "Cong ty"}, {"word": "\u4f1a\u8b70", "hiragana": "\u304b\u3044\u304e", "meaning": "Hoi nghi"}, {"word": "\u4f1a\u8a71", "hiragana": "\u304b\u3044\u308f", "meaning": "Hoi thoai"}]},
      {"character": "内", "han_viet": "Noi", "onyomi": ["\u30ca\u30a4"], "kunyomi": ["\u3046\u3061"], "meaning_vi": "Ben trong", "examples": [{"word": "\u5185", "hiragana": "\u3046\u3061", "meaning": "Ben trong"}, {"word": "\u5bb6\u5185", "hiragana": "\u304b\u306a\u3044", "meaning": "Vo toi"}, {"word": "\u56fd\u5185", "hiragana": "\u3053\u304f\u306a\u3044", "meaning": "Trong nuoc"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 11,
    "topic": "Kanji for Adjectives 1",
    "kanji_list": [
      {"character": "長", "han_viet": "Truong", "onyomi": ["\u30c1\u30e7\u30a6"], "kunyomi": ["\u306a\u304c-\u3044"], "meaning_vi": "Dai", "examples": [{"word": "\u9577\u3044", "hiragana": "\u306a\u304c\u3044", "meaning": "Dai"}, {"word": "\u793e\u9577", "hiragana": "\u3057\u3083\u3061\u3087\u3046", "meaning": "Giam doc"}, {"word": "\u6821\u9577", "hiragana": "\u3053\u3046\u3061\u3087\u3046", "meaning": "Hieu truong"}]},
      {"character": "高", "han_viet": "Cao", "onyomi": ["\u30b3\u30a6"], "kunyomi": ["\u305f\u304b-\u3044"], "meaning_vi": "Cao, dat", "examples": [{"word": "\u9ad8\u3044", "hiragana": "\u305f\u304b\u3044", "meaning": "Cao / Dat"}, {"word": "\u9ad8\u6821", "hiragana": "\u3053\u3046\u3053\u3046", "meaning": "Truong cap 3"}, {"word": "\u9ad8\u901f", "hiragana": "\u3053\u3046\u305d\u304f", "meaning": "Cao toc"}]},
      {"character": "名", "han_viet": "Danh", "onyomi": ["\u30e1\u30a4"], "kunyomi": ["\u306a"], "meaning_vi": "Ten", "examples": [{"word": "\u540d\u524d", "hiragana": "\u306a\u307e\u3048", "meaning": "Ten"}, {"word": "\u6709\u540d", "hiragana": "\u3086\u3046\u3081\u3044", "meaning": "Noi tieng"}, {"word": "\u540d\u523a", "hiragana": "\u3081\u3044\u3057", "meaning": "Danh thiep"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 12,
    "topic": "Kanji for Verbs 1",
    "kanji_list": [
      {"character": "行", "han_viet": "Hanh", "onyomi": ["\u30b3\u30a6", "\u30ae\u30e7\u30a6"], "kunyomi": ["\u3044-\u304f"], "meaning_vi": "Di", "examples": [{"word": "\u884c\u304f", "hiragana": "\u3044\u304f", "meaning": "Di"}, {"word": "\u65c5\u884c", "hiragana": "\u308a\u3087\u3053\u3046", "meaning": "Du lich"}, {"word": "\u9280\u884c", "hiragana": "\u304e\u3093\u3053\u3046", "meaning": "Ngan hang"}]},
      {"character": "来", "han_viet": "Lai", "onyomi": ["\u30e9\u30a4"], "kunyomi": ["\u304f-\u308b"], "meaning_vi": "Den", "examples": [{"word": "\u6765\u308b", "hiragana": "\u304f\u308b", "meaning": "Den"}, {"word": "\u6765\u9031", "hiragana": "\u3089\u3044\u3057\u3085\u3046", "meaning": "Tuan sau"}, {"word": "\u6765\u5e74", "hiragana": "\u3089\u3044\u306d\u3093", "meaning": "Nam sau"}, {"word": "\u5c06\u6765", "hiragana": "\u3057\u3087\u3046\u3089\u3044", "meaning": "Tuong lai"}]},
      {"character": "食", "han_viet": "Thuc", "onyomi": ["\u30b7\u30e7\u30af"], "kunyomi": ["\u305f-\u3079\u308b"], "meaning_vi": "An", "examples": [{"word": "\u98df\u3079\u308b", "hiragana": "\u305f\u3079\u308b", "meaning": "An"}, {"word": "\u98df\u3079\u7269", "hiragana": "\u305f\u3079\u3082\u306e", "meaning": "Do an"}, {"word": "\u98df\u5802", "hiragana": "\u3057\u3087\u304f\u3069\u3046", "meaning": "Nha an"}, {"word": "\u98df\u4e8b", "hiragana": "\u3057\u3087\u304f\u3058", "meaning": "Bua an"}]},
      {"character": "見", "han_viet": "Kien", "onyomi": ["\u30b1\u30f3"], "kunyomi": ["\u307f-\u308b"], "meaning_vi": "Nhin", "examples": [{"word": "\u898b\u308b", "hiragana": "\u307f\u308b", "meaning": "Nhin, xem"}, {"word": "\u898b\u305b\u308b", "hiragana": "\u307f\u305b\u308b", "meaning": "Cho xem"}, {"word": "\u898b\u5b66", "hiragana": "\u3051\u3093\u304c\u304f", "meaning": "Tham quan hoc tap"}, {"word": "\u610f\u898b", "hiragana": "\u3044\u3051\u3093", "meaning": "Y kien"}]},
      {"character": "聞", "han_viet": "Van", "onyomi": ["\u30d6\u30f3"], "kunyomi": ["\u304d-\u304f"], "meaning_vi": "Nghe", "examples": [{"word": "\u805e\u304f", "hiragana": "\u304d\u304f", "meaning": "Nghe, hoi"}, {"word": "\u805e\u3053\u3048\u308b", "hiragana": "\u304d\u3053\u3048\u308b", "meaning": "Nghe thay"}, {"word": "\u65b0\u805e", "hiragana": "\u3057\u3093\u3076\u3093", "meaning": "Bao chi"}]},
      {"character": "読", "han_viet": "Doc", "onyomi": ["\u30c9\u30af"], "kunyomi": ["\u3088-\u3080"], "meaning_vi": "Doc", "examples": [{"word": "\u8aad\u3080", "hiragana": "\u3088\u3080", "meaning": "Doc"}, {"word": "\u8aad\u66f8", "hiragana": "\u3069\u304f\u3057\u3087", "meaning": "Viec doc sach"}, {"word": "\u8aad\u307f\u65b9", "hiragana": "\u3088\u307f\u304b\u305f", "meaning": "Cach doc"}]},
      {"character": "書", "han_viet": "Thu", "onyomi": ["\u30b7\u30e7"], "kunyomi": ["\u304b-\u304f"], "meaning_vi": "Viet", "examples": [{"word": "\u66f8\u304f", "hiragana": "\u304b\u304f", "meaning": "Viet"}, {"word": "\u8f9e\u66f8", "hiragana": "\u3058\u3057\u3087", "meaning": "Tu dien"}, {"word": "\u56f3\u66f8\u9928", "hiragana": "\u3068\u3057\u3087\u304b\u3093", "meaning": "Thu vien"}]},
      {"character": "話", "han_viet": "Thoai", "onyomi": ["\u30ef"], "kunyomi": ["\u306f\u306a-\u3059"], "meaning_vi": "Noi chuyen", "examples": [{"word": "\u8a71\u3059", "hiragana": "\u306f\u306a\u3059", "meaning": "Noi chuyen"}, {"word": "\u8a71", "hiragana": "\u306f\u306a\u3057", "meaning": "Cau chuyen"}, {"word": "\u96fb\u8a71", "hiragana": "\u3067\u3093\u308f", "meaning": "Dien thoai"}, {"word": "\u4f1a\u8a71", "hiragana": "\u304b\u3044\u308f", "meaning": "Hoi thoai"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 13,
    "topic": "Kanji for Time 1",
    "kanji_list": [
      {"character": "午", "han_viet": "Ngo", "onyomi": ["\u30b4"], "kunyomi": ["\u3046\u307e"], "meaning_vi": "Trua", "examples": [{"word": "\u5348\u524d", "hiragana": "\u3054\u305c\u3093", "meaning": "Buoi sang (AM)"}, {"word": "\u5348\u5f8c", "hiragana": "\u3054\u3054", "meaning": "Buoi chieu (PM)"}, {"word": "\u6b63\u5348", "hiragana": "\u3057\u3087\u3046\u3054", "meaning": "Chinh ngo (12h trua)"}]},
      {"character": "前", "han_viet": "Tien", "onyomi": ["\u30bc\u30f3"], "kunyomi": ["\u307e\u3048"], "meaning_vi": "Truoc", "examples": [{"word": "\u524d", "hiragana": "\u307e\u3048", "meaning": "Truoc"}, {"word": "\u5348\u524d", "hiragana": "\u3054\u305c\u3093", "meaning": "Buoi sang"}, {"word": "\u540d\u524d", "hiragana": "\u306a\u307e\u3048", "meaning": "Ten"}, {"word": "\u99c5\u524d", "hiragana": "\u3048\u304d\u307e\u3048", "meaning": "Truoc nha ga"}]},
      {"character": "後", "han_viet": "Hau", "onyomi": ["\u30b4"], "kunyomi": ["\u3042\u3068", "\u3046\u3057-\u308d"], "meaning_vi": "Sau", "examples": [{"word": "\u5f8c\u308d", "hiragana": "\u3046\u3057\u308d", "meaning": "Phia sau"}, {"word": "\u5f8c\u3067", "hiragana": "\u3042\u3068\u3067", "meaning": "Lat nua"}, {"word": "\u5348\u5f8c", "hiragana": "\u3054\u3054", "meaning": "Buoi chieu"}, {"word": "\u6700\u5f8c", "hiragana": "\u3055\u3044\u3054", "meaning": "Cuoi cung"}]},
      {"character": "毎", "han_viet": "Moi", "onyomi": ["\u30de\u30a4"], "kunyomi": ["\u3054\u3068"], "meaning_vi": "Moi", "examples": [{"word": "\u6bce\u65e5", "hiragana": "\u307e\u3044\u306b\u3061", "meaning": "Hang ngay"}, {"word": "\u6bce\u6708", "hiragana": "\u307e\u3044\u3064\u304d", "meaning": "Hang thang"}, {"word": "\u6bce\u5e74", "hiragana": "\u307e\u3044\u3068\u3057", "meaning": "Hang nam"}, {"word": "\u6bce\u671d", "hiragana": "\u307e\u3044\u3042\u3055", "meaning": "Moi sang"}]}
    ]
  },
  {
    "jlpt_level": "N5",
    "lesson_id": 14,
    "topic": "Other common Kanji",
    "kanji_list": [
      {"character": "校", "han_viet": "Hieu", "onyomi": ["\u30b3\u30a6"], "kunyomi": [], "meaning_vi": "Truong hoc", "examples": [{"word": "\u5b66\u6821", "hiragana": "\u304c\u3063\u3053\u3046", "meaning": "Truong hoc"}, {"word": "\u9ad8\u6821", "hiragana": "\u3053\u3046\u3053\u3046", "meaning": "Truong cap 3"}, {"word": "\u6821\u9577", "hiragana": "\u3053\u3046\u3061\u3087\u3046", "meaning": "Hieu truong"}]},
      {"character": "語", "han_viet": "Ngu", "onyomi": ["\u30b4"], "kunyomi": ["\u304b\u305f-\u308b"], "meaning_vi": "Ngon ngu", "examples": [{"word": "\u65e5\u672c\u8a9e", "hiragana": "\u306b\u307b\u3093\u3054", "meaning": "Tieng Nhat"}, {"word": "\u82f1\u8a9e", "hiragana": "\u3048\u3044\u3054", "meaning": "Tieng Anh"}, {"word": "\u8a9e\u5b66", "hiragana": "\u3054\u304c\u304f", "meaning": "Ngon ngu hoc"}]},
      {"character": "今", "han_viet": "Kim", "onyomi": ["\u30b3\u30f3"], "kunyomi": ["\u3044\u307e"], "meaning_vi": "Bay gio", "examples": [{"word": "\u4eca", "hiragana": "\u3044\u307e", "meaning": "Bay gio"}, {"word": "\u4eca\u65e5", "hiragana": "\u304d\u3087\u3046", "meaning": "Hom nay"}, {"word": "\u4eca\u6708", "hiragana": "\u3053\u3093\u3052\u3064", "meaning": "Thang nay"}, {"word": "\u4eca\u5e74", "hiragana": "\u3053\u3068\u3057", "meaning": "Nam nay"}]},
      {"character": "電", "han_viet": "Dien", "onyomi": ["\u30c7\u30f3"], "kunyomi": [], "meaning_vi": "Dien", "examples": [{"word": "\u96fb\u6c17", "hiragana": "\u3067\u3093\u304d", "meaning": "Dien"}, {"word": "\u96fb\u8eca", "hiragana": "\u3067\u3093\u3057\u3083", "meaning": "Tau dien"}, {"word": "\u96fb\u8a71", "hiragana": "\u3067\u3093\u308f", "meaning": "Dien thoai"}]},
      {"character": "国", "han_viet": "Quoc", "onyomi": ["\u30b3\u30af"], "kunyomi": ["\u304f\u306b"], "meaning_vi": "Dat nuoc", "examples": [{"word": "\u56fd", "hiragana": "\u304f\u306b", "meaning": "Dat nuoc"}, {"word": "\u5916\u56fd", "hiragana": "\u304c\u3044\u3053\u304f", "meaning": "Nuoc ngoai"}, {"word": "\u4e2d\u56fd", "hiragana": "\u3061\u3085\u3046\u3054\u304f", "meaning": "Trung Quoc"}, {"word": "\u56fd\u969b", "hiragana": "\u3053\u304f\u3055\u3044", "meaning": "Quoc te"}]}
    ]
  }
]


class Command(BaseCommand):
    help = "Clear all kanji data and load N5 sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-clear',
            action='store_true',
            dest='no_clear',
            help='Do not clear existing kanji data before loading',
        )

    def handle(self, *args, **options):
        do_clear = not options['no_clear']

        if do_clear:
            self.stdout.write("Clearing existing kanji data...")
            UserKanjiProgress.objects.all().delete()
            KanjiVocab.objects.all().delete()
            Kanji.objects.all().delete()
            KanjiLesson.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("  OK - cleared"))

        self.stdout.write("Loading N5 data...")
        stats = _import_kanji_json(N5_DATA, replace=False)
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created:\n"
            f"  - {stats['lessons']} lessons (N5)\n"
            f"  - {stats['kanji']} kanji\n"
            f"  - {stats['vocab']} vocab examples\n"
            f"\nURL: http://127.0.0.1:8000/kanji/levels/"
        ))
