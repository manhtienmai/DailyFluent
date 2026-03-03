"""
Management command: load Kanji N2 – Bài 1 & 2.

Usage:
    python manage.py load_kanji_n2
"""
from django.core.management.base import BaseCommand

from kanji.admin import _import_kanji_json

N2_DATA = [
  {
    "jlpt_level": "N2",
    "lesson_id": 1,
    "topic": "Địa lý & Xã hội",
    "kanji_list": [
      {
        "character": "区",
        "han_viet": "Khu",
        "onyomi": ["ク"],
        "kunyomi": [],
        "meaning_vi": "Khu vực, quận",
        "formation": "Hội ý: 匚(hộp) + 品(đồ vật) → phân chia khu vực",
        "examples": [
          {"word": "地区", "hiragana": "ちく", "meaning": "Địa khu, khu vực"},
          {"word": "区別", "hiragana": "くべつ", "meaning": "Phân biệt"},
          {"word": "区域", "hiragana": "くいき", "meaning": "Khu vực"},
          {"word": "区間", "hiragana": "くかん", "meaning": "Khu gian, đoạn"},
          {"word": "区民", "hiragana": "くみん", "meaning": "Cư dân quận"}
        ]
      },
      {
        "character": "県",
        "han_viet": "Huyện",
        "onyomi": ["ケン"],
        "kunyomi": [],
        "meaning_vi": "Huyện, tỉnh",
        "formation": "Hội ý: 目(mắt) + 系(hệ) → quản lý vùng đất",
        "examples": [
          {"word": "県庁", "hiragana": "けんちょう", "meaning": "Tỉnh sảnh, ủy ban tỉnh"},
          {"word": "県民", "hiragana": "けんみん", "meaning": "Cư dân tỉnh"},
          {"word": "県立", "hiragana": "けんりつ", "meaning": "Thuộc tỉnh lập"},
          {"word": "県内", "hiragana": "けんない", "meaning": "Trong tỉnh"},
          {"word": "県知事", "hiragana": "けんちじ", "meaning": "Thống đốc tỉnh"}
        ]
      },
      {
        "character": "村",
        "han_viet": "Thôn",
        "onyomi": ["ソン"],
        "kunyomi": ["むら"],
        "meaning_vi": "Thôn, làng",
        "formation": "Hình thanh: 木(ý: cây) + 寸(âm: ソン) → làng quê có cây cối",
        "examples": [
          {"word": "村長", "hiragana": "そんちょう", "meaning": "Trưởng thôn"},
          {"word": "村民", "hiragana": "そんみん", "meaning": "Dân làng"},
          {"word": "村落", "hiragana": "そんらく", "meaning": "Thôn xóm"},
          {"word": "農村", "hiragana": "のうそん", "meaning": "Nông thôn"},
          {"word": "村", "hiragana": "むら", "meaning": "Làng"}
        ]
      },
      {
        "character": "低",
        "han_viet": "Đê",
        "onyomi": ["テイ"],
        "kunyomi": ["ひくい", "ひくめる", "ひくまる"],
        "meaning_vi": "Thấp",
        "formation": "Hình thanh: 亻(ý: người) + 氐(âm: テイ) → người cúi thấp",
        "examples": [
          {"word": "低下", "hiragana": "ていか", "meaning": "Giảm xuống, suy giảm"},
          {"word": "最低", "hiragana": "さいてい", "meaning": "Tối thiểu, tệ nhất"},
          {"word": "低温", "hiragana": "ていおん", "meaning": "Nhiệt độ thấp"},
          {"word": "低い", "hiragana": "ひくい", "meaning": "Thấp"},
          {"word": "低下する", "hiragana": "ていかする", "meaning": "Sụt giảm"}
        ]
      },
      {
        "character": "門",
        "han_viet": "Môn",
        "onyomi": ["モン"],
        "kunyomi": ["かど"],
        "meaning_vi": "Cổng, cửa, môn",
        "formation": "Tượng hình: Hình ảnh hai cánh cửa mở ra",
        "examples": [
          {"word": "専門", "hiragana": "せんもん", "meaning": "Chuyên môn"},
          {"word": "入門", "hiragana": "にゅうもん", "meaning": "Nhập môn"},
          {"word": "部門", "hiragana": "ぶもん", "meaning": "Bộ môn, bộ phận"},
          {"word": "門", "hiragana": "もん", "meaning": "Cổng"},
          {"word": "校門", "hiragana": "こうもん", "meaning": "Cổng trường"}
        ]
      },
      {
        "character": "森",
        "han_viet": "Sâm",
        "onyomi": ["シン"],
        "kunyomi": ["もり"],
        "meaning_vi": "Rừng rậm",
        "formation": "Hội ý: 木+木+木 (ba cây) → rừng rậm, um tùm",
        "examples": [
          {"word": "森林", "hiragana": "しんりん", "meaning": "Rừng rậm, sâm lâm"},
          {"word": "森", "hiragana": "もり", "meaning": "Rừng"},
          {"word": "森林浴", "hiragana": "しんりんよく", "meaning": "Tắm rừng"},
          {"word": "森林保護", "hiragana": "しんりんほご", "meaning": "Bảo vệ rừng"},
          {"word": "青森", "hiragana": "あおもり", "meaning": "Aomori (tỉnh)"}
        ]
      },
      {
        "character": "林",
        "han_viet": "Lâm",
        "onyomi": ["リン"],
        "kunyomi": ["はやし"],
        "meaning_vi": "Rừng thưa",
        "formation": "Hội ý: 木+木 (hai cây) → rừng thưa",
        "examples": [
          {"word": "森林", "hiragana": "しんりん", "meaning": "Sâm lâm, rừng rậm"},
          {"word": "林業", "hiragana": "りんぎょう", "meaning": "Lâm nghiệp"},
          {"word": "山林", "hiragana": "さんりん", "meaning": "Sơn lâm"},
          {"word": "林", "hiragana": "はやし", "meaning": "Lùm cây, rừng thưa"},
          {"word": "農林", "hiragana": "のうりん", "meaning": "Nông lâm"}
        ]
      },
      {
        "character": "短",
        "han_viet": "Đoản",
        "onyomi": ["タン"],
        "kunyomi": ["みじかい"],
        "meaning_vi": "Ngắn",
        "formation": "Hình thanh: 矢(ý: mũi tên, ngắn) + 豆(âm: トウ→タン) → ngắn",
        "examples": [
          {"word": "短期", "hiragana": "たんき", "meaning": "Ngắn hạn"},
          {"word": "短所", "hiragana": "たんしょ", "meaning": "Nhược điểm, sở đoản"},
          {"word": "短縮", "hiragana": "たんしゅく", "meaning": "Rút ngắn"},
          {"word": "短い", "hiragana": "みじかい", "meaning": "Ngắn"},
          {"word": "短大", "hiragana": "たんだい", "meaning": "Cao đẳng"}
        ]
      },
      {
        "character": "軽",
        "han_viet": "Khinh",
        "onyomi": ["ケイ"],
        "kunyomi": ["かるい", "かろやか"],
        "meaning_vi": "Nhẹ, khinh",
        "formation": "Hình thanh: 車(ý: xe) + 巠(âm: ケイ) → xe nhẹ",
        "examples": [
          {"word": "軽い", "hiragana": "かるい", "meaning": "Nhẹ"},
          {"word": "軽食", "hiragana": "けいしょく", "meaning": "Bữa ăn nhẹ"},
          {"word": "軽減", "hiragana": "けいげん", "meaning": "Giảm nhẹ"},
          {"word": "手軽", "hiragana": "てがる", "meaning": "Đơn giản, tiện lợi"},
          {"word": "軽率", "hiragana": "けいそつ", "meaning": "Khinh suất"}
        ]
      },
      {
        "character": "池",
        "han_viet": "Trì",
        "onyomi": ["チ"],
        "kunyomi": ["いけ"],
        "meaning_vi": "Ao, hồ",
        "formation": "Hình thanh: 氵(ý: nước) + 也(âm: チ) → ao nước",
        "examples": [
          {"word": "池", "hiragana": "いけ", "meaning": "Cái ao"},
          {"word": "電池", "hiragana": "でんち", "meaning": "Pin"},
          {"word": "池袋", "hiragana": "いけぶくろ", "meaning": "Ikebukuro"},
          {"word": "貯水池", "hiragana": "ちょすいち", "meaning": "Hồ chứa nước"}
        ]
      },
      {
        "character": "弱",
        "han_viet": "Nhược",
        "onyomi": ["ジャク"],
        "kunyomi": ["よわい", "よわる", "よわまる", "よわめる"],
        "meaning_vi": "Yếu",
        "formation": "Hội ý: 弓+弓 (hai cung) + 彡(lông) → cung yếu, mỏng manh",
        "examples": [
          {"word": "弱点", "hiragana": "じゃくてん", "meaning": "Nhược điểm"},
          {"word": "弱い", "hiragana": "よわい", "meaning": "Yếu"},
          {"word": "弱者", "hiragana": "じゃくしゃ", "meaning": "Người yếu thế"},
          {"word": "強弱", "hiragana": "きょうじゃく", "meaning": "Mạnh yếu"}
        ]
      },
      {
        "character": "菜",
        "han_viet": "Thái",
        "onyomi": ["サイ"],
        "kunyomi": ["な"],
        "meaning_vi": "Rau",
        "formation": "Hình thanh: 艹(ý: cỏ) + 采(âm: サイ) → rau cỏ",
        "examples": [
          {"word": "野菜", "hiragana": "やさい", "meaning": "Rau quả"},
          {"word": "菜食", "hiragana": "さいしょく", "meaning": "Ăn chay"},
          {"word": "前菜", "hiragana": "ぜんさい", "meaning": "Món khai vị"},
          {"word": "山菜", "hiragana": "さんさい", "meaning": "Rau rừng"}
        ]
      },
      {
        "character": "協",
        "han_viet": "Hiệp",
        "onyomi": ["キョウ"],
        "kunyomi": [],
        "meaning_vi": "Hợp tác, hiệp",
        "formation": "Hội ý: 十(mười) + 力+力+力 (ba sức) → nhiều người hợp sức",
        "examples": [
          {"word": "協力", "hiragana": "きょうりょく", "meaning": "Hiệp lực, hợp tác"},
          {"word": "協会", "hiragana": "きょうかい", "meaning": "Hiệp hội"},
          {"word": "協定", "hiragana": "きょうてい", "meaning": "Hiệp định"},
          {"word": "協議", "hiragana": "きょうぎ", "meaning": "Bàn bạc"},
          {"word": "協調", "hiragana": "きょうちょう", "meaning": "Phối hợp"}
        ]
      },
      {
        "character": "改",
        "han_viet": "Cải",
        "onyomi": ["カイ"],
        "kunyomi": ["あらためる", "あらたまる"],
        "meaning_vi": "Sửa đổi, cải cách",
        "formation": "Hội ý: 己(bản thân) + 攵(đánh) → tự đánh mình để sửa đổi",
        "examples": [
          {"word": "改善", "hiragana": "かいぜん", "meaning": "Cải thiện"},
          {"word": "改革", "hiragana": "かいかく", "meaning": "Cải cách"},
          {"word": "改正", "hiragana": "かいせい", "meaning": "Sửa đổi"},
          {"word": "改札", "hiragana": "かいさつ", "meaning": "Cửa soát vé"},
          {"word": "改める", "hiragana": "あらためる", "meaning": "Sửa đổi"}
        ]
      },
      {
        "character": "府",
        "han_viet": "Phủ",
        "onyomi": ["フ"],
        "kunyomi": [],
        "meaning_vi": "Phủ, chính phủ",
        "formation": "Hình thanh: 广(ý: mái nhà) + 付(âm: フ) → cơ quan lớn dưới mái nhà",
        "examples": [
          {"word": "政府", "hiragana": "せいふ", "meaning": "Chính phủ"},
          {"word": "府県", "hiragana": "ふけん", "meaning": "Phủ huyện"},
          {"word": "大阪府", "hiragana": "おおさかふ", "meaning": "Phủ Osaka"},
          {"word": "京都府", "hiragana": "きょうとふ", "meaning": "Phủ Kyoto"}
        ]
      },
      {
        "character": "委",
        "han_viet": "Ủy",
        "onyomi": ["イ"],
        "kunyomi": ["ゆだねる"],
        "meaning_vi": "Ủy thác, giao phó",
        "formation": "Hội ý: 禾(lúa) + 女(phụ nữ) → giao việc cho người khác",
        "examples": [
          {"word": "委員", "hiragana": "いいん", "meaning": "Ủy viên"},
          {"word": "委員会", "hiragana": "いいんかい", "meaning": "Ủy ban"},
          {"word": "委託", "hiragana": "いたく", "meaning": "Ủy thác"},
          {"word": "委任", "hiragana": "いにん", "meaning": "Ủy nhiệm"},
          {"word": "委ねる", "hiragana": "ゆだねる", "meaning": "Giao phó"}
        ]
      },
      {
        "character": "軍",
        "han_viet": "Quân",
        "onyomi": ["グン"],
        "kunyomi": ["いくさ"],
        "meaning_vi": "Quân đội",
        "formation": "Hội ý: 冖(mũ che) + 車(xe) → xe quân đội được che phủ",
        "examples": [
          {"word": "軍隊", "hiragana": "ぐんたい", "meaning": "Quân đội"},
          {"word": "軍事", "hiragana": "ぐんじ", "meaning": "Quân sự"},
          {"word": "軍人", "hiragana": "ぐんじん", "meaning": "Quân nhân"},
          {"word": "海軍", "hiragana": "かいぐん", "meaning": "Hải quân"},
          {"word": "空軍", "hiragana": "くうぐん", "meaning": "Không quân"}
        ]
      },
      {
        "character": "各",
        "han_viet": "Các",
        "onyomi": ["カク"],
        "kunyomi": ["おの", "おのおの"],
        "meaning_vi": "Mỗi, các",
        "formation": "Hội ý: 夂(bước đi) + 口(miệng) → mỗi người đi một hướng",
        "examples": [
          {"word": "各地", "hiragana": "かくち", "meaning": "Các nơi"},
          {"word": "各国", "hiragana": "かっこく", "meaning": "Các nước"},
          {"word": "各自", "hiragana": "かくじ", "meaning": "Mỗi người"},
          {"word": "各種", "hiragana": "かくしゅ", "meaning": "Các loại"},
          {"word": "各駅停車", "hiragana": "かくえきていしゃ", "meaning": "Tàu dừng mỗi ga"}
        ]
      },
      {
        "character": "島",
        "han_viet": "Đảo",
        "onyomi": ["トウ"],
        "kunyomi": ["しま"],
        "meaning_vi": "Đảo",
        "formation": "Hội ý: 鳥(chim) + 山(núi) → núi giữa biển có chim đậu → đảo",
        "examples": [
          {"word": "半島", "hiragana": "はんとう", "meaning": "Bán đảo"},
          {"word": "島国", "hiragana": "しまぐに", "meaning": "Đảo quốc"},
          {"word": "列島", "hiragana": "れっとう", "meaning": "Quần đảo"},
          {"word": "島", "hiragana": "しま", "meaning": "Đảo"},
          {"word": "無人島", "hiragana": "むじんとう", "meaning": "Đảo hoang"}
        ]
      },
      {
        "character": "副",
        "han_viet": "Phó",
        "onyomi": ["フク"],
        "kunyomi": [],
        "meaning_vi": "Phó, phụ",
        "formation": "Hình thanh: 畐(âm: フク) + 刂(ý: dao) → chia phần phụ",
        "examples": [
          {"word": "副社長", "hiragana": "ふくしゃちょう", "meaning": "Phó giám đốc"},
          {"word": "副作用", "hiragana": "ふくさよう", "meaning": "Tác dụng phụ"},
          {"word": "副業", "hiragana": "ふくぎょう", "meaning": "Nghề phụ"},
          {"word": "副会長", "hiragana": "ふくかいちょう", "meaning": "Phó hội trưởng"},
          {"word": "副詞", "hiragana": "ふくし", "meaning": "Phó từ (trạng từ)"}
        ]
      }
    ]
  },
  {
    "jlpt_level": "N2",
    "lesson_id": 2,
    "topic": "Toán học & Đo lường",
    "kanji_list": [
      {
        "character": "算",
        "han_viet": "Toán",
        "onyomi": ["サン"],
        "kunyomi": [],
        "meaning_vi": "Tính toán",
        "formation": "Hội ý: 竹(tre) + 目(mắt) + 廾(hai tay) → dùng que tre và mắt để tính",
        "examples": [
          {"word": "計算", "hiragana": "けいさん", "meaning": "Tính toán"},
          {"word": "予算", "hiragana": "よさん", "meaning": "Ngân sách, dự toán"},
          {"word": "算数", "hiragana": "さんすう", "meaning": "Toán học (tiểu học)"},
          {"word": "暗算", "hiragana": "あんざん", "meaning": "Tính nhẩm"},
          {"word": "決算", "hiragana": "けっさん", "meaning": "Quyết toán"}
        ]
      },
      {
        "character": "線",
        "han_viet": "Tuyến",
        "onyomi": ["セン"],
        "kunyomi": ["すじ"],
        "meaning_vi": "Dây, tuyến, đường",
        "formation": "Hình thanh: 糸(ý: sợi chỉ) + 泉(âm: セン) → sợi dây, đường tuyến",
        "examples": [
          {"word": "新幹線", "hiragana": "しんかんせん", "meaning": "Tàu cao tốc Shinkansen"},
          {"word": "路線", "hiragana": "ろせん", "meaning": "Lộ tuyến, tuyến đường"},
          {"word": "電線", "hiragana": "でんせん", "meaning": "Dây điện"},
          {"word": "無線", "hiragana": "むせん", "meaning": "Vô tuyến"},
          {"word": "前線", "hiragana": "ぜんせん", "meaning": "Tiền tuyến"}
        ]
      },
      {
        "character": "農",
        "han_viet": "Nông",
        "onyomi": ["ノウ"],
        "kunyomi": [],
        "meaning_vi": "Nông nghiệp",
        "formation": "Hội ý: 曲(uốn cong) + 辰(bàn tay cầm vỏ sò) → uốn mình làm ruộng",
        "examples": [
          {"word": "農業", "hiragana": "のうぎょう", "meaning": "Nông nghiệp"},
          {"word": "農村", "hiragana": "のうそん", "meaning": "Nông thôn"},
          {"word": "農民", "hiragana": "のうみん", "meaning": "Nông dân"},
          {"word": "農家", "hiragana": "のうか", "meaning": "Nhà nông"},
          {"word": "農薬", "hiragana": "のうやく", "meaning": "Thuốc trừ sâu"}
        ]
      },
      {
        "character": "州",
        "han_viet": "Châu",
        "onyomi": ["シュウ"],
        "kunyomi": ["す"],
        "meaning_vi": "Tỉnh, bang, châu lục",
        "formation": "Tượng hình: Hình ảnh dải đất giữa dòng sông → vùng đất",
        "examples": [
          {"word": "九州", "hiragana": "きゅうしゅう", "meaning": "Kyushu"},
          {"word": "本州", "hiragana": "ほんしゅう", "meaning": "Honshu"},
          {"word": "欧州", "hiragana": "おうしゅう", "meaning": "Châu Âu"},
          {"word": "州立", "hiragana": "しゅうりつ", "meaning": "Thuộc bang lập"}
        ]
      },
      {
        "character": "象",
        "han_viet": "Tượng",
        "onyomi": ["ショウ", "ゾウ"],
        "kunyomi": [],
        "meaning_vi": "Hiện tượng, con voi, hình tượng",
        "formation": "Tượng hình: Hình ảnh con voi với vòi dài",
        "examples": [
          {"word": "現象", "hiragana": "げんしょう", "meaning": "Hiện tượng"},
          {"word": "印象", "hiragana": "いんしょう", "meaning": "Ấn tượng"},
          {"word": "対象", "hiragana": "たいしょう", "meaning": "Đối tượng"},
          {"word": "象徴", "hiragana": "しょうちょう", "meaning": "Biểu tượng"},
          {"word": "気象", "hiragana": "きしょう", "meaning": "Khí tượng"}
        ]
      },
      {
        "character": "賞",
        "han_viet": "Thưởng",
        "onyomi": ["ショウ"],
        "kunyomi": [],
        "meaning_vi": "Giải thưởng, thưởng",
        "formation": "Hình thanh: 尚(âm: ショウ) + 貝(ý: tiền) → cho tiền thưởng",
        "examples": [
          {"word": "賞品", "hiragana": "しょうひん", "meaning": "Phần thưởng"},
          {"word": "受賞", "hiragana": "じゅしょう", "meaning": "Nhận giải"},
          {"word": "鑑賞", "hiragana": "かんしょう", "meaning": "Thưởng thức"},
          {"word": "賞金", "hiragana": "しょうきん", "meaning": "Tiền thưởng"},
          {"word": "賞味期限", "hiragana": "しょうみきげん", "meaning": "Hạn sử dụng"}
        ]
      },
      {
        "character": "辺",
        "han_viet": "Biên",
        "onyomi": ["ヘン"],
        "kunyomi": ["べ", "あたり"],
        "meaning_vi": "Biên, vùng lân cận",
        "formation": "Hình thanh: 辶(ý: đi) + 刀(âm) → đi đến biên giới",
        "examples": [
          {"word": "辺り", "hiragana": "あたり", "meaning": "Vùng lân cận"},
          {"word": "周辺", "hiragana": "しゅうへん", "meaning": "Xung quanh"},
          {"word": "海辺", "hiragana": "うみべ", "meaning": "Bờ biển"},
          {"word": "辺境", "hiragana": "へんきょう", "meaning": "Biên cương"}
        ]
      },
      {
        "character": "課",
        "han_viet": "Khóa",
        "onyomi": ["カ"],
        "kunyomi": [],
        "meaning_vi": "Khóa học, bài học, phòng ban",
        "formation": "Hình thanh: 言(ý: lời nói) + 果(âm: カ) → bài học bằng lời",
        "examples": [
          {"word": "課長", "hiragana": "かちょう", "meaning": "Trưởng phòng"},
          {"word": "課題", "hiragana": "かだい", "meaning": "Đề tài, vấn đề"},
          {"word": "日課", "hiragana": "にっか", "meaning": "Việc hàng ngày"},
          {"word": "課程", "hiragana": "かてい", "meaning": "Chương trình học"}
        ]
      },
      {
        "character": "極",
        "han_viet": "Cực",
        "onyomi": ["キョク", "ゴク"],
        "kunyomi": ["きわめる", "きわまる", "きわみ"],
        "meaning_vi": "Cực, cùng cực",
        "formation": "Hình thanh: 木(ý: gỗ) + 亟(âm: キョク) → cái cột chống đến tận cùng",
        "examples": [
          {"word": "積極的", "hiragana": "せっきょくてき", "meaning": "Tích cực"},
          {"word": "北極", "hiragana": "ほっきょく", "meaning": "Bắc cực"},
          {"word": "極端", "hiragana": "きょくたん", "meaning": "Cực đoan"},
          {"word": "極めて", "hiragana": "きわめて", "meaning": "Cực kỳ"},
          {"word": "南極", "hiragana": "なんきょく", "meaning": "Nam cực"}
        ]
      },
      {
        "character": "量",
        "han_viet": "Lượng",
        "onyomi": ["リョウ"],
        "kunyomi": ["はかる"],
        "meaning_vi": "Lượng, đo lường",
        "formation": "Hội ý: 旦(mặt trời mọc) + 里(làng) → đo đạc ruộng đất lúc sáng",
        "examples": [
          {"word": "量", "hiragana": "りょう", "meaning": "Lượng"},
          {"word": "大量", "hiragana": "たいりょう", "meaning": "Đại lượng, số lượng lớn"},
          {"word": "重量", "hiragana": "じゅうりょう", "meaning": "Trọng lượng"},
          {"word": "測量", "hiragana": "そくりょう", "meaning": "Đo đạc"},
          {"word": "容量", "hiragana": "ようりょう", "meaning": "Dung lượng"}
        ]
      },
      {
        "character": "型",
        "han_viet": "Hình",
        "onyomi": ["ケイ"],
        "kunyomi": ["かた"],
        "meaning_vi": "Khuôn, mẫu, kiểu",
        "formation": "Hình thanh: 刑(âm: ケイ) + 土(ý: đất) → khuôn đúc bằng đất",
        "examples": [
          {"word": "大型", "hiragana": "おおがた", "meaning": "Cỡ lớn"},
          {"word": "小型", "hiragana": "こがた", "meaning": "Cỡ nhỏ"},
          {"word": "血液型", "hiragana": "けつえきがた", "meaning": "Nhóm máu"},
          {"word": "模型", "hiragana": "もけい", "meaning": "Mô hình"},
          {"word": "新型", "hiragana": "しんがた", "meaning": "Kiểu mới"}
        ]
      },
      {
        "character": "谷",
        "han_viet": "Cốc",
        "onyomi": ["コク"],
        "kunyomi": ["たに"],
        "meaning_vi": "Thung lũng",
        "formation": "Hội ý: 八(chia ra) + 口(miệng) → miệng núi mở ra → thung lũng",
        "examples": [
          {"word": "谷", "hiragana": "たに", "meaning": "Thung lũng"},
          {"word": "渓谷", "hiragana": "けいこく", "meaning": "Hẻm núi"},
          {"word": "谷間", "hiragana": "たにま", "meaning": "Khe núi"},
          {"word": "長谷川", "hiragana": "はせがわ", "meaning": "Hasegawa (họ)"}
        ]
      },
      {
        "character": "史",
        "han_viet": "Sử",
        "onyomi": ["シ"],
        "kunyomi": [],
        "meaning_vi": "Lịch sử",
        "formation": "Hội ý: 中(giữa) + 又(tay phải) → tay ghi chép → lịch sử",
        "examples": [
          {"word": "歴史", "hiragana": "れきし", "meaning": "Lịch sử"},
          {"word": "史上", "hiragana": "しじょう", "meaning": "Trong lịch sử"},
          {"word": "史料", "hiragana": "しりょう", "meaning": "Sử liệu"},
          {"word": "日本史", "hiragana": "にほんし", "meaning": "Lịch sử Nhật Bản"}
        ]
      },
      {
        "character": "階",
        "han_viet": "Giai",
        "onyomi": ["カイ"],
        "kunyomi": [],
        "meaning_vi": "Tầng, bậc, giai cấp",
        "formation": "Hình thanh: 阝(ý: đồi) + 皆(âm: カイ) → bậc thang trên đồi",
        "examples": [
          {"word": "階段", "hiragana": "かいだん", "meaning": "Cầu thang"},
          {"word": "二階", "hiragana": "にかい", "meaning": "Tầng hai"},
          {"word": "階級", "hiragana": "かいきゅう", "meaning": "Giai cấp"},
          {"word": "段階", "hiragana": "だんかい", "meaning": "Giai đoạn"}
        ]
      },
      {
        "character": "管",
        "han_viet": "Quản",
        "onyomi": ["カン"],
        "kunyomi": ["くだ"],
        "meaning_vi": "Ống, quản lý",
        "formation": "Hình thanh: 竹(ý: tre) + 官(âm: カン) → ống tre → quản lý",
        "examples": [
          {"word": "管理", "hiragana": "かんり", "meaning": "Quản lý"},
          {"word": "管", "hiragana": "くだ", "meaning": "Ống"},
          {"word": "管轄", "hiragana": "かんかつ", "meaning": "Quản hạt"},
          {"word": "管制", "hiragana": "かんせい", "meaning": "Quản chế"},
          {"word": "血管", "hiragana": "けっかん", "meaning": "Mạch máu"}
        ]
      },
      {
        "character": "兵",
        "han_viet": "Binh",
        "onyomi": ["ヘイ", "ヒョウ"],
        "kunyomi": [],
        "meaning_vi": "Binh lính, binh lực",
        "formation": "Hội ý: 斤(rìu) + 廾(hai tay) → hai tay cầm rìu → binh lính",
        "examples": [
          {"word": "兵士", "hiragana": "へいし", "meaning": "Binh sĩ"},
          {"word": "兵器", "hiragana": "へいき", "meaning": "Binh khí, vũ khí"},
          {"word": "兵力", "hiragana": "へいりょく", "meaning": "Binh lực"},
          {"word": "兵庫", "hiragana": "ひょうご", "meaning": "Hyogo (tỉnh)"}
        ]
      },
      {
        "character": "細",
        "han_viet": "Tế",
        "onyomi": ["サイ"],
        "kunyomi": ["ほそい", "ほそる", "こまか", "こまかい"],
        "meaning_vi": "Nhỏ, chi tiết, tinh tế",
        "formation": "Hình thanh: 糸(ý: sợi chỉ) + 田(âm: サイ) → sợi chỉ nhỏ → tinh tế",
        "examples": [
          {"word": "細かい", "hiragana": "こまかい", "meaning": "Chi tiết, nhỏ"},
          {"word": "細い", "hiragana": "ほそい", "meaning": "Mảnh, gầy"},
          {"word": "詳細", "hiragana": "しょうさい", "meaning": "Chi tiết"},
          {"word": "細胞", "hiragana": "さいぼう", "meaning": "Tế bào"},
          {"word": "細心", "hiragana": "さいしん", "meaning": "Tỉ mỉ, cẩn thận"}
        ]
      },
      {
        "character": "丸",
        "han_viet": "Hoàn",
        "onyomi": ["ガン"],
        "kunyomi": ["まる", "まるい", "まるめる"],
        "meaning_vi": "Tròn, viên",
        "formation": "Chỉ sự: Hình tròn 九 với dấu chấm → hình tròn",
        "examples": [
          {"word": "丸い", "hiragana": "まるい", "meaning": "Tròn"},
          {"word": "丸", "hiragana": "まる", "meaning": "Hình tròn"},
          {"word": "丸める", "hiragana": "まるめる", "meaning": "Cuộn tròn"},
          {"word": "日の丸", "hiragana": "ひのまる", "meaning": "Quốc kỳ Nhật"}
        ]
      },
      {
        "character": "録",
        "han_viet": "Lục",
        "onyomi": ["ロク"],
        "kunyomi": [],
        "meaning_vi": "Ghi chép, kí lục",
        "formation": "Hình thanh: 金(ý: kim loại) + 录(âm: ロク) → khắc ghi trên kim loại",
        "examples": [
          {"word": "記録", "hiragana": "きろく", "meaning": "Kí lục, ghi chép"},
          {"word": "録音", "hiragana": "ろくおん", "meaning": "Thu âm"},
          {"word": "登録", "hiragana": "とうろく", "meaning": "Đăng ký"},
          {"word": "録画", "hiragana": "ろくが", "meaning": "Thu hình"},
          {"word": "目録", "hiragana": "もくろく", "meaning": "Mục lục"}
        ]
      },
      {
        "character": "省",
        "han_viet": "Tỉnh",
        "onyomi": ["ショウ", "セイ"],
        "kunyomi": ["はぶく", "かえりみる"],
        "meaning_vi": "Bộ (chính phủ), tiết kiệm, tự xét",
        "formation": "Hội ý: 少(ít) + 目(mắt) → ít nhìn lại → tự xét, tiết kiệm",
        "examples": [
          {"word": "省エネ", "hiragana": "しょうエネ", "meaning": "Tiết kiệm năng lượng"},
          {"word": "省略", "hiragana": "しょうりゃく", "meaning": "Lược bỏ"},
          {"word": "反省", "hiragana": "はんせい", "meaning": "Phản tỉnh"},
          {"word": "文部省", "hiragana": "もんぶしょう", "meaning": "Bộ Giáo dục"},
          {"word": "省く", "hiragana": "はぶく", "meaning": "Lược bỏ, tiết kiệm"}
        ]
      }
    ]
  },
  {
    "jlpt_level": "N2",
    "lesson_id": 3,
    "topic": "Giao thông & Tự nhiên",
    "kanji_list": [
      {
        "character": "橋",
        "han_viet": "Kiều",
        "onyomi": ["キョウ"],
        "kunyomi": ["はし"],
        "meaning_vi": "Cây cầu",
        "formation": "Hình thanh: 木 (mộc – cây gỗ, chỉ chất liệu gỗ) + 喬 (kiều – cao vút, cho âm キョウ). Ngày xưa cầu làm bằng gỗ bắc cao qua sông. 喬 vừa cho âm đọc vừa gợi ý cầu vươn cao.",
        "examples": [
          {"word": "橋", "hiragana": "はし", "meaning": "Cây cầu"},
          {"word": "歩道橋", "hiragana": "ほどうきょう", "meaning": "Cầu vượt bộ hành"},
          {"word": "鉄橋", "hiragana": "てっきょう", "meaning": "Cầu sắt"},
          {"word": "石橋", "hiragana": "いしばし", "meaning": "Cầu đá"}
        ]
      },
      {
        "character": "岸",
        "han_viet": "Ngạn",
        "onyomi": ["ガン"],
        "kunyomi": ["きし"],
        "meaning_vi": "Bờ, hải ngạn",
        "formation": "Hội ý: 山 (sơn – núi đá) + 厂 (vách đá) + 干 (can – cột chống). Hình ảnh vách đá dựng đứng bên bờ sông, nơi mặt đất nhô cao thành bờ.",
        "examples": [
          {"word": "海岸", "hiragana": "かいがん", "meaning": "Bờ biển"},
          {"word": "岸", "hiragana": "きし", "meaning": "Bờ sông"},
          {"word": "対岸", "hiragana": "たいがん", "meaning": "Bờ đối diện"},
          {"word": "沿岸", "hiragana": "えんがん", "meaning": "Dọc bờ biển"}
        ]
      },
      {
        "character": "周",
        "han_viet": "Chu",
        "onyomi": ["シュウ"],
        "kunyomi": ["まわり"],
        "meaning_vi": "Xung quanh, chu vi",
        "formation": "Hội ý: 冂 (vây quanh) + 土 (thổ – đất) + 口 (khẩu – miệng). Hình ảnh một vùng đất được bao quanh kín, ý chỉ sự trọn vẹn một vòng.",
        "examples": [
          {"word": "周り", "hiragana": "まわり", "meaning": "Xung quanh"},
          {"word": "周囲", "hiragana": "しゅうい", "meaning": "Chu vi, bao quanh"},
          {"word": "一周", "hiragana": "いっしゅう", "meaning": "Một vòng"},
          {"word": "周辺", "hiragana": "しゅうへん", "meaning": "Vùng phụ cận"}
        ]
      },
      {
        "character": "材",
        "han_viet": "Tài",
        "onyomi": ["ザイ"],
        "kunyomi": [],
        "meaning_vi": "Tài liệu, chất liệu, nhân tài",
        "formation": "Hình thanh: 木 (mộc – gỗ, chỉ vật liệu) + 才 (tài – tài năng, cho âm ザイ). Gỗ là nguyên liệu cơ bản nhất; mở rộng nghĩa thành tài liệu, nhân tài.",
        "examples": [
          {"word": "材料", "hiragana": "ざいりょう", "meaning": "Nguyên liệu"},
          {"word": "人材", "hiragana": "じんざい", "meaning": "Nhân tài"},
          {"word": "素材", "hiragana": "そざい", "meaning": "Chất liệu"},
          {"word": "教材", "hiragana": "きょうざい", "meaning": "Giáo tài, giáo cụ"},
          {"word": "木材", "hiragana": "もくざい", "meaning": "Gỗ, mộc tài"}
        ]
      },
      {
        "character": "戸",
        "han_viet": "Hộ",
        "onyomi": ["コ"],
        "kunyomi": ["と"],
        "meaning_vi": "Cửa, hộ gia đình",
        "formation": "Tượng hình: Hình ảnh một cánh cửa xoay (門 là hai cánh, 戸 chỉ một cánh). Nghĩa gốc là cánh cửa, mở rộng thành hộ gia đình (nhà có cửa).",
        "examples": [
          {"word": "戸", "hiragana": "と", "meaning": "Cánh cửa"},
          {"word": "戸籍", "hiragana": "こせき", "meaning": "Hộ tịch"},
          {"word": "下戸", "hiragana": "げこ", "meaning": "Người không uống được rượu"},
          {"word": "雨戸", "hiragana": "あまど", "meaning": "Cửa chống mưa bão"},
          {"word": "戸口", "hiragana": "とぐち", "meaning": "Cửa ra vào"}
        ]
      },
      {
        "character": "央",
        "han_viet": "Ương",
        "onyomi": ["オウ"],
        "kunyomi": [],
        "meaning_vi": "Trung tâm, giữa",
        "formation": "Hội ý: 大 (đại – người dang tay) + | (que xuyên giữa). Hình ảnh người đứng giữa bị que xuyên qua chính giữa → nghĩa: trung tâm, giữa.",
        "examples": [
          {"word": "中央", "hiragana": "ちゅうおう", "meaning": "Trung ương"},
          {"word": "中央線", "hiragana": "ちゅうおうせん", "meaning": "Tuyến Chuo"},
          {"word": "中央区", "hiragana": "ちゅうおうく", "meaning": "Quận Chuo"}
        ]
      },
      {
        "character": "竹",
        "han_viet": "Trúc",
        "onyomi": ["チク"],
        "kunyomi": ["たけ"],
        "meaning_vi": "Tre, trúc",
        "formation": "Tượng hình: Hình ảnh hai nhánh tre với lá rủ xuống. Chữ ⺮ (bộ trúc) xuất hiện trong nhiều kanji liên quan đến đồ tre (筆, 箱, 算, 管).",
        "examples": [
          {"word": "竹", "hiragana": "たけ", "meaning": "Tre, trúc"},
          {"word": "竹林", "hiragana": "ちくりん", "meaning": "Rừng tre"},
          {"word": "竹の子", "hiragana": "たけのこ", "meaning": "Măng"},
          {"word": "爆竹", "hiragana": "ばくちく", "meaning": "Pháo nổ"}
        ]
      },
      {
        "character": "競",
        "han_viet": "Cạnh",
        "onyomi": ["キョウ", "ケイ"],
        "kunyomi": ["せる", "きそう", "くらべる"],
        "meaning_vi": "Cạnh tranh, thi đấu",
        "formation": "Hội ý: 立 (lập – đứng) + 兄 (huynh – anh) × 2 = hai người đứng tranh nhau. Hình ảnh hai anh em đứng song song, cùng cạnh tranh → nghĩa: ganh đua.",
        "examples": [
          {"word": "競争", "hiragana": "きょうそう", "meaning": "Cạnh tranh"},
          {"word": "競馬", "hiragana": "けいば", "meaning": "Đua ngựa"},
          {"word": "競技", "hiragana": "きょうぎ", "meaning": "Thi đấu"},
          {"word": "競り合い", "hiragana": "せりあい", "meaning": "Tranh đua"}
        ]
      },
      {
        "character": "根",
        "han_viet": "Căn",
        "onyomi": ["コン"],
        "kunyomi": ["ね"],
        "meaning_vi": "Gốc, rễ, căn bản",
        "formation": "Hình thanh: 木 (mộc – cây, chỉ ý nghĩa rễ cây) + 艮 (cấn – cứng rắn, bền bỉ, cho âm コン). Rễ cây bám sâu, cứng rắn → gốc rễ, nền tảng.",
        "examples": [
          {"word": "根", "hiragana": "ね", "meaning": "Rễ, gốc"},
          {"word": "根本", "hiragana": "こんぽん", "meaning": "Căn bản, gốc rễ"},
          {"word": "根拠", "hiragana": "こんきょ", "meaning": "Căn cứ"},
          {"word": "根性", "hiragana": "こんじょう", "meaning": "Nghị lực"},
          {"word": "屋根", "hiragana": "やね", "meaning": "Mái nhà"}
        ]
      },
      {
        "character": "歴",
        "han_viet": "Lịch",
        "onyomi": ["レキ"],
        "kunyomi": [],
        "meaning_vi": "Lịch sử, kinh lịch",
        "formation": "Hình thanh: 厂 (vách đá) + 禾禾 (lúa chồng lên) + 止 (chỉ – dừng, cho âm). Hình ảnh các tầng lúa (mùa vụ) chồng lên nhau qua năm tháng → sự trải qua, lịch sử.",
        "examples": [
          {"word": "歴史", "hiragana": "れきし", "meaning": "Lịch sử"},
          {"word": "経歴", "hiragana": "けいれき", "meaning": "Kinh lịch, hồ sơ"},
          {"word": "学歴", "hiragana": "がくれき", "meaning": "Học lịch, học vấn"},
          {"word": "履歴書", "hiragana": "りれきしょ", "meaning": "Lý lịch, CV"}
        ]
      },
      {
        "character": "航",
        "han_viet": "Hàng",
        "onyomi": ["コウ"],
        "kunyomi": [],
        "meaning_vi": "Hàng hải, hàng không",
        "formation": "Hình thanh: 舟 (chu – thuyền, chỉ phương tiện đi lại) + 亢 (kháng – cổ ngẩng cao, cho âm コウ). Thuyền lướt trên mặt nước → đi xa, hàng hải; mở rộng sang hàng không.",
        "examples": [
          {"word": "航空", "hiragana": "こうくう", "meaning": "Hàng không"},
          {"word": "航海", "hiragana": "こうかい", "meaning": "Hàng hải"},
          {"word": "航路", "hiragana": "こうろ", "meaning": "Tuyến đường biển/không"},
          {"word": "運航", "hiragana": "うんこう", "meaning": "Vận hành chuyến bay/tàu"}
        ]
      },
      {
        "character": "鉄",
        "han_viet": "Thiết",
        "onyomi": ["テツ"],
        "kunyomi": [],
        "meaning_vi": "Sắt, gang thép",
        "formation": "Hình thanh: 金 (kim – kim loại, chỉ chất liệu) + 失 (thất – mất, cho âm テツ). Kim loại phổ biến nhất, hay bị gỉ (mất đi vẻ sáng) → sắt.",
        "examples": [
          {"word": "地下鉄", "hiragana": "ちかてつ", "meaning": "Tàu điện ngầm"},
          {"word": "鉄道", "hiragana": "てつどう", "meaning": "Đường sắt"},
          {"word": "鉄板", "hiragana": "てっぱん", "meaning": "Tấm sắt, chắc chắn"},
          {"word": "鋼鉄", "hiragana": "こうてつ", "meaning": "Gang thép"}
        ]
      },
      {
        "character": "児",
        "han_viet": "Nhi",
        "onyomi": ["ジ", "ニ"],
        "kunyomi": ["こ"],
        "meaning_vi": "Trẻ em, nhi đồng",
        "formation": "Hội ý: 旧(đầu) + 儿 (nhân – chân người). Hình ảnh đứa trẻ có đầu to (thóp chưa khép) trên đôi chân nhỏ → trẻ sơ sinh.",
        "examples": [
          {"word": "幼児", "hiragana": "ようじ", "meaning": "Trẻ nhỏ"},
          {"word": "児童", "hiragana": "じどう", "meaning": "Nhi đồng"},
          {"word": "小児科", "hiragana": "しょうにか", "meaning": "Khoa nhi"},
          {"word": "育児", "hiragana": "いくじ", "meaning": "Nuôi con nhỏ"}
        ]
      },
      {
        "character": "印",
        "han_viet": "Ấn",
        "onyomi": ["イン"],
        "kunyomi": ["しるし"],
        "meaning_vi": "Dấu, in ấn",
        "formation": "Hội ý: 爫 (tay ấn xuống) + 卩 (quỳ gối). Hình ảnh bàn tay ấn xuống con dấu lên vật → đóng dấu, in ấn. Mở rộng: dấu hiệu, ấn tượng.",
        "examples": [
          {"word": "印象", "hiragana": "いんしょう", "meaning": "Ấn tượng"},
          {"word": "印刷", "hiragana": "いんさつ", "meaning": "In ấn"},
          {"word": "印鑑", "hiragana": "いんかん", "meaning": "Con dấu"},
          {"word": "目印", "hiragana": "めじるし", "meaning": "Dấu hiệu nhận biết"}
        ]
      },
      {
        "character": "油",
        "han_viet": "Du",
        "onyomi": ["ユ"],
        "kunyomi": ["あぶら"],
        "meaning_vi": "Dầu, mỡ",
        "formation": "Hình thanh: 氵(thủy – nước, chỉ chất lỏng) + 由 (do – từ đâu đó ra, cho âm ユ). Chất lỏng nhờn chảy ra từ đất hoặc thực vật → dầu.",
        "examples": [
          {"word": "油", "hiragana": "あぶら", "meaning": "Dầu, mỡ"},
          {"word": "石油", "hiragana": "せきゆ", "meaning": "Dầu mỏ"},
          {"word": "油断", "hiragana": "ゆだん", "meaning": "Chủ quan, lơ là"},
          {"word": "醤油", "hiragana": "しょうゆ", "meaning": "Nước tương"},
          {"word": "油絵", "hiragana": "あぶらえ", "meaning": "Tranh sơn dầu"}
        ]
      },
      {
        "character": "輪",
        "han_viet": "Luân",
        "onyomi": ["リン"],
        "kunyomi": ["わ"],
        "meaning_vi": "Bánh xe, vòng tròn",
        "formation": "Hình thanh: 車 (xa – xe, chỉ phương tiện) + 侖 (luân – sắp xếp theo thứ tự, cho âm リン). Bánh xe quay tròn theo vòng → bánh xe, luân hồi (xoay vòng).",
        "examples": [
          {"word": "車輪", "hiragana": "しゃりん", "meaning": "Bánh xe"},
          {"word": "五輪", "hiragana": "ごりん", "meaning": "Olympic (5 vòng)"},
          {"word": "指輪", "hiragana": "ゆびわ", "meaning": "Nhẫn"},
          {"word": "輪郭", "hiragana": "りんかく", "meaning": "Đường viền, luân quách"},
          {"word": "一輪車", "hiragana": "いちりんしゃ", "meaning": "Xe một bánh"}
        ]
      },
      {
        "character": "植",
        "han_viet": "Thực",
        "onyomi": ["ショク"],
        "kunyomi": ["うえる", "うわる"],
        "meaning_vi": "Trồng cây, thực vật",
        "formation": "Hình thanh: 木 (mộc – cây, chỉ cây cối) + 直 (trực – thẳng, cho âm ショク). Cây được trồng thẳng đứng xuống đất → trồng trọt, thực vật.",
        "examples": [
          {"word": "植物", "hiragana": "しょくぶつ", "meaning": "Thực vật"},
          {"word": "植える", "hiragana": "うえる", "meaning": "Trồng"},
          {"word": "植民地", "hiragana": "しょくみんち", "meaning": "Thuộc địa"},
          {"word": "移植", "hiragana": "いしょく", "meaning": "Ghép, cấy (cơ quan)"},
          {"word": "植林", "hiragana": "しょくりん", "meaning": "Trồng rừng"}
        ]
      },
      {
        "character": "清",
        "han_viet": "Thanh",
        "onyomi": ["セイ", "シン"],
        "kunyomi": ["きよい", "きよまる", "きよめる"],
        "meaning_vi": "Trong sạch, thanh bạch",
        "formation": "Hình thanh: 氵(thủy – nước, chỉ sự trong trẻo) + 青 (thanh – xanh, cho âm セイ). Nước xanh trong → trong sạch, thuần khiết. Liên hệ HV: Thanh = trong, sạch.",
        "examples": [
          {"word": "清潔", "hiragana": "せいけつ", "meaning": "Sạch sẽ"},
          {"word": "清い", "hiragana": "きよい", "meaning": "Trong sạch"},
          {"word": "清掃", "hiragana": "せいそう", "meaning": "Dọn dẹp"},
          {"word": "清算", "hiragana": "せいさん", "meaning": "Thanh toán"},
          {"word": "清める", "hiragana": "きよめる", "meaning": "Tẩy rửa, thanh tẩy"}
        ]
      },
      {
        "character": "倍",
        "han_viet": "Bội",
        "onyomi": ["バイ"],
        "kunyomi": [],
        "meaning_vi": "Gấp đôi, bội số",
        "formation": "Hình thanh: 亻(nhân – người, chỉ hành vi) + 咅 (bồi – phát âm, cho âm バイ). Người nhân đôi sức lực → gấp bội. Liên hệ: bội thu = thu hoạch gấp nhiều lần.",
        "examples": [
          {"word": "二倍", "hiragana": "にばい", "meaning": "Gấp đôi"},
          {"word": "倍率", "hiragana": "ばいりつ", "meaning": "Tỷ lệ, bội suất"},
          {"word": "倍増", "hiragana": "ばいぞう", "meaning": "Tăng gấp đôi"},
          {"word": "何倍", "hiragana": "なんばい", "meaning": "Gấp mấy lần"}
        ]
      },
      {
        "character": "億",
        "han_viet": "Ức",
        "onyomi": ["オク"],
        "kunyomi": [],
        "meaning_vi": "Trăm triệu (100.000.000)",
        "formation": "Hình thanh: 亻(nhân – người, chỉ khái niệm trừu tượng) + 意 (ý – ý nghĩ, cho âm オク). Số lượng lớn đến mức chỉ có thể tưởng tượng trong ý nghĩ → con số khổng lồ: 100 triệu.",
        "examples": [
          {"word": "一億", "hiragana": "いちおく", "meaning": "Một trăm triệu"},
          {"word": "億万", "hiragana": "おくまん", "meaning": "Hàng tỷ"},
          {"word": "数億", "hiragana": "すうおく", "meaning": "Vài trăm triệu"},
          {"word": "億万長者", "hiragana": "おくまんちょうじゃ", "meaning": "Tỷ phú"}
        ]
      }
    ]
  },
  {
    "jlpt_level": "N2",
    "lesson_id": 4,
    "topic": "Đời sống & Tự nhiên II",
    "kanji_list": [
      {
        "character": "芸",
        "han_viet": "Vân",
        "onyomi": ["ゲイ"],
        "kunyomi": ["わざ"],
        "meaning_vi": "Nghệ thuật, kỹ năng",
        "formation": "🔊 Hình thanh: 艹 (thảo – cỏ) + 云 (vân – mây, cho âm ゲイ gần ウン). Gốc: cây thảo mộc có hương thơm xua côn trùng; người trồng thảo mộc cần kỹ năng → nghệ thuật. Nhóm 云: 芸(vân=nghệ), 雲(vân=mây).",
        "examples": [
          {"word": "芸術", "hiragana": "げいじゅつ", "meaning": "Nghệ thuật"},
          {"word": "芸能", "hiragana": "げいのう", "meaning": "Nghệ năng, giải trí"},
          {"word": "芸人", "hiragana": "げいにん", "meaning": "Nghệ nhân, diễn viên hài"},
          {"word": "芸能人", "hiragana": "げいのうじん", "meaning": "Nghệ sĩ"},
          {"word": "文芸", "hiragana": "ぶんげい", "meaning": "Văn nghệ"}
        ]
      },
      {
        "character": "停",
        "han_viet": "Đình",
        "onyomi": ["テイ"],
        "kunyomi": [],
        "meaning_vi": "Dừng lại, đình chỉ",
        "formation": "🔊 Hình thanh: 亻(nhân – người) + 亭 (đình – cái đình, cho âm テイ). Người dừng chân ở đình nghỉ mát → dừng lại. Nhóm âm 亭→テイ: 停(đình chỉ), 亭(đình).",
        "examples": [
          {"word": "停止", "hiragana": "ていし", "meaning": "Đình chỉ, dừng lại"},
          {"word": "停車", "hiragana": "ていしゃ", "meaning": "Dừng xe"},
          {"word": "停電", "hiragana": "ていでん", "meaning": "Mất điện"},
          {"word": "バス停", "hiragana": "バスてい", "meaning": "Trạm xe buýt"}
        ]
      },
      {
        "character": "陸",
        "han_viet": "Lục",
        "onyomi": ["リク"],
        "kunyomi": [],
        "meaning_vi": "Đất liền, lục địa",
        "formation": "🔊 Hình thanh: 阝(phụ – gò đất, chỉ địa hình) + 坴 (lục – đất chồng lên, cho âm リク). Gò đất nhô cao khỏi mặt nước → đất liền, lục địa.",
        "examples": [
          {"word": "大陸", "hiragana": "たいりく", "meaning": "Đại lục, lục địa"},
          {"word": "陸上", "hiragana": "りくじょう", "meaning": "Trên bộ"},
          {"word": "着陸", "hiragana": "ちゃくりく", "meaning": "Hạ cánh"},
          {"word": "陸軍", "hiragana": "りくぐん", "meaning": "Lục quân"}
        ]
      },
      {
        "character": "玉",
        "han_viet": "Ngọc",
        "onyomi": ["ギョク"],
        "kunyomi": ["たま"],
        "meaning_vi": "Ngọc, viên tròn, đá quý",
        "formation": "📖 Tượng hình: Ba viên ngọc 王 xâu trên sợi dây, thêm dấu chấm phân biệt với 王(vua). Ngọc = đá quý tròn bóng. Bộ 玉/⺩ xuất hiện trong nhiều chữ liên quan đến đá quý: 珠(châu), 理(lý), 現(hiện), 環(hoàn).",
        "examples": [
          {"word": "玉", "hiragana": "たま", "meaning": "Viên tròn, ngọc"},
          {"word": "宝玉", "hiragana": "ほうぎょく", "meaning": "Ngọc quý"},
          {"word": "玉ねぎ", "hiragana": "たまねぎ", "meaning": "Hành tây"},
          {"word": "目玉", "hiragana": "めだま", "meaning": "Tròng mắt, điểm nhấn"}
        ]
      },
      {
        "character": "波",
        "han_viet": "Ba",
        "onyomi": ["ハ"],
        "kunyomi": ["なみ"],
        "meaning_vi": "Sóng",
        "formation": "🔊 Hình thanh: 氵(thủy – nước) + 皮 (bì – da, lớp ngoài, cho âm ハ). Lớp nước bên ngoài cuộn lên → sóng. Nhóm âm 皮→ハ/ヒ: 波(ba=sóng), 破(phá=phá vỡ), 被(bị=chịu đựng).",
        "examples": [
          {"word": "波", "hiragana": "なみ", "meaning": "Sóng"},
          {"word": "電波", "hiragana": "でんぱ", "meaning": "Sóng điện từ"},
          {"word": "津波", "hiragana": "つなみ", "meaning": "Sóng thần"},
          {"word": "波長", "hiragana": "はちょう", "meaning": "Bước sóng"}
        ]
      },
      {
        "character": "帯",
        "han_viet": "Đới",
        "onyomi": ["タイ"],
        "kunyomi": ["おび", "おびる"],
        "meaning_vi": "Đai, dải, vùng",
        "formation": "📖 Hội ý: Phần trên (世+冖 = thế gian + mũ che) + 巾 (cân – vải). Dải vải quấn quanh thân → đai lưng. Mở rộng: vùng đất quấn quanh Trái Đất như dải vải → nhiệt đới, ôn đới, hàn đới.",
        "examples": [
          {"word": "地帯", "hiragana": "ちたい", "meaning": "Vùng, khu vực"},
          {"word": "熱帯", "hiragana": "ねったい", "meaning": "Nhiệt đới"},
          {"word": "帯", "hiragana": "おび", "meaning": "Đai lưng (kimono)"},
          {"word": "携帯", "hiragana": "けいたい", "meaning": "Mang theo, điện thoại"}
        ]
      },
      {
        "character": "羽",
        "han_viet": "Vũ",
        "onyomi": ["ウ"],
        "kunyomi": ["は", "はね", "わ"],
        "meaning_vi": "Lông vũ, cánh",
        "formation": "📖 Tượng hình: Hai cánh chim xòe đối xứng, mỗi nửa là một chiếc lông. Bộ 羽 xuất hiện trong: 翼(dực=cánh), 習(tập=học, chim tập bay), 翌(dực=ngày mai). Mẹo: hình chữ trông như hai cánh chim đang vỗ.",
        "examples": [
          {"word": "羽", "hiragana": "はね", "meaning": "Lông, cánh"},
          {"word": "羽田", "hiragana": "はねだ", "meaning": "Haneda (sân bay)"},
          {"word": "一羽", "hiragana": "いちわ", "meaning": "Một con (chim, thỏ)"},
          {"word": "羽毛", "hiragana": "うもう", "meaning": "Lông tơ"}
        ]
      },
      {
        "character": "固",
        "han_viet": "Cố",
        "onyomi": ["コ"],
        "kunyomi": ["かためる", "かたまる", "かたい"],
        "meaning_vi": "Cứng, chắc, ngoan cố",
        "formation": "🔊 Hình thanh: 囗 (vi – bao quanh, đóng kín) + 古 (cổ – cũ lâu, cho âm コ). Vật bị bao bọc kín lâu ngày → cứng chắc, bền vững. Nhóm âm 古→コ: 固(cố=cứng), 故(cố=nên), 枯(khô héo), 個(cá thể).",
        "examples": [
          {"word": "固い", "hiragana": "かたい", "meaning": "Cứng, chắc"},
          {"word": "固定", "hiragana": "こてい", "meaning": "Cố định"},
          {"word": "頑固", "hiragana": "がんこ", "meaning": "Ngoan cố"},
          {"word": "固める", "hiragana": "かためる", "meaning": "Làm cứng lại"}
        ]
      },
      {
        "character": "囲",
        "han_viet": "Vi",
        "onyomi": ["イ"],
        "kunyomi": ["かこむ", "かこう"],
        "meaning_vi": "Bao vây, chu vi",
        "formation": "🔊 Hình thanh: 囗 (vi – viền bao) + 韋 (vi – da thuộc, cho âm イ). Dùng da bao bọc xung quanh → bao vây. Nhóm âm 韋→イ: 囲(vi=bao vây), 違(vi=khác biệt), 偉(vĩ=vĩ đại).",
        "examples": [
          {"word": "周囲", "hiragana": "しゅうい", "meaning": "Chu vi, xung quanh"},
          {"word": "囲む", "hiragana": "かこむ", "meaning": "Bao vây"},
          {"word": "範囲", "hiragana": "はんい", "meaning": "Phạm vi"},
          {"word": "雰囲気", "hiragana": "ふんいき", "meaning": "Bầu không khí"}
        ]
      },
      {
        "character": "卒",
        "han_viet": "Tốt",
        "onyomi": ["ソツ"],
        "kunyomi": [],
        "meaning_vi": "Binh tốt, tốt nghiệp, kết thúc",
        "formation": "📖 Hội ý + Mẹo nhớ: 亠 (đầu) + 人人 (hai người) + 十 (thập = chữ thập). Hình ảnh lính mặc áo có dấu thập → binh tốt (lính trơn). Lính hoàn thành nghĩa vụ → tốt nghiệp, kết thúc.",
        "examples": [
          {"word": "卒業", "hiragana": "そつぎょう", "meaning": "Tốt nghiệp"},
          {"word": "兵卒", "hiragana": "へいそつ", "meaning": "Binh tốt, lính"},
          {"word": "卒論", "hiragana": "そつろん", "meaning": "Luận văn tốt nghiệp"},
          {"word": "卒中", "hiragana": "そっちゅう", "meaning": "Đột quỵ"}
        ]
      },
      {
        "character": "順",
        "han_viet": "Thuận",
        "onyomi": ["ジュン"],
        "kunyomi": [],
        "meaning_vi": "Thuận theo, thứ tự",
        "formation": "📖 Hội ý: 川 (xuyên – dòng sông chảy xuôi) + 頁 (hiệt – cái đầu). Mẹo: Nước sông chảy xuôi 川, người cúi đầu 頁 theo dòng → thuận theo tự nhiên, đi theo thứ tự.",
        "examples": [
          {"word": "順番", "hiragana": "じゅんばん", "meaning": "Thứ tự"},
          {"word": "順調", "hiragana": "じゅんちょう", "meaning": "Thuận lợi, suôn sẻ"},
          {"word": "順序", "hiragana": "じゅんじょ", "meaning": "Trình tự"},
          {"word": "手順", "hiragana": "てじゅん", "meaning": "Quy trình, các bước"}
        ]
      },
      {
        "character": "岩",
        "han_viet": "Nham",
        "onyomi": ["ガン"],
        "kunyomi": ["いわ"],
        "meaning_vi": "Đá tảng, nham thạch",
        "formation": "📖 Hội ý: 山 (sơn – núi) + 石 (thạch – đá). Đơn giản: đá trên núi → tảng đá lớn, nham thạch. Mẹo: núi 山 đặt trên đá 石 = tảng đá khổng lồ trong núi.",
        "examples": [
          {"word": "岩", "hiragana": "いわ", "meaning": "Tảng đá"},
          {"word": "岩石", "hiragana": "がんせき", "meaning": "Nham thạch"},
          {"word": "溶岩", "hiragana": "ようがん", "meaning": "Dung nham"},
          {"word": "火成岩", "hiragana": "かせいがん", "meaning": "Đá magma"}
        ]
      },
      {
        "character": "練",
        "han_viet": "Luyện",
        "onyomi": ["レン"],
        "kunyomi": ["ねる"],
        "meaning_vi": "Rèn luyện, luyện tập",
        "formation": "🔊 Hình thanh: 糸 (mịch – sợi tơ, chỉ quá trình tinh chế) + 柬 (giản – chọn lọc, cho âm レン). Tơ phải đun nấu, kéo sợi nhiều lần mới mượt mà → rèn luyện, tập đi tập lại.",
        "examples": [
          {"word": "練習", "hiragana": "れんしゅう", "meaning": "Luyện tập"},
          {"word": "訓練", "hiragana": "くんれん", "meaning": "Huấn luyện"},
          {"word": "練る", "hiragana": "ねる", "meaning": "Nhào, trau chuốt"},
          {"word": "熟練", "hiragana": "じゅくれん", "meaning": "Thành thạo, thuần thục"}
        ]
      },
      {
        "character": "令",
        "han_viet": "Lệnh",
        "onyomi": ["レイ"],
        "kunyomi": [],
        "meaning_vi": "Lệnh, ra lệnh",
        "formation": "📖 Hội ý + Bộ cho âm: 亼 (mũ quan, mệnh lệnh từ trên xuống) + 卩 (người quỳ gối). Mẹo: Quan đội mũ 亼 ra lệnh, bên dưới quỳ 卩 tuân theo. ⚡ 令 cho âm レイ trong rất nhiều chữ: 冷(lãnh=lạnh), 零(linh=số 0), 齢(linh=tuổi), 鈴(linh=chuông), 領(lãnh=lãnh đạo).",
        "examples": [
          {"word": "命令", "hiragana": "めいれい", "meaning": "Mệnh lệnh"},
          {"word": "令和", "hiragana": "れいわ", "meaning": "Lệnh Hòa (niên hiệu)"},
          {"word": "法令", "hiragana": "ほうれい", "meaning": "Pháp lệnh"},
          {"word": "指令", "hiragana": "しれい", "meaning": "Chỉ lệnh"}
        ]
      },
      {
        "character": "角",
        "han_viet": "Giác",
        "onyomi": ["カク"],
        "kunyomi": ["かど", "つの"],
        "meaning_vi": "Sừng, góc",
        "formation": "📖 Tượng hình: Phần trên là sừng nhọn 🐂, phần dưới là đầu con vật. Sừng thú nhọn → góc nhọn → góc (hình học). Mẹo: Giác = góc. Bộ 角 xuất hiện trong: 解(giải=tháo sừng→giải quyết), 触(xúc=chạm sừng→tiếp xúc).",
        "examples": [
          {"word": "角度", "hiragana": "かくど", "meaning": "Góc độ"},
          {"word": "三角", "hiragana": "さんかく", "meaning": "Tam giác"},
          {"word": "角", "hiragana": "つの", "meaning": "Sừng"},
          {"word": "角", "hiragana": "かど", "meaning": "Góc (đường phố)"},
          {"word": "四角", "hiragana": "しかく", "meaning": "Tứ giác, hình vuông"}
        ]
      },
      {
        "character": "貨",
        "han_viet": "Hóa",
        "onyomi": ["カ"],
        "kunyomi": [],
        "meaning_vi": "Hàng hóa",
        "formation": "🔊 Hình thanh: 化 (hóa – biến đổi, cho âm カ) + 貝 (bối – vỏ sò = tiền xưa). Vật có giá trị dùng trao đổi (biến đổi) → hàng hóa. Nhóm âm 化→カ: 貨(hóa=hàng), 花(hoa=hoa), 靴(hóa=giày).",
        "examples": [
          {"word": "貨物", "hiragana": "かもつ", "meaning": "Hàng hóa"},
          {"word": "通貨", "hiragana": "つうか", "meaning": "Tiền tệ"},
          {"word": "雑貨", "hiragana": "ざっか", "meaning": "Tạp hóa"},
          {"word": "百貨店", "hiragana": "ひゃっかてん", "meaning": "Bách hóa, trung tâm TM"}
        ]
      },
      {
        "character": "血",
        "han_viet": "Huyết",
        "onyomi": ["ケツ"],
        "kunyomi": ["ち"],
        "meaning_vi": "Máu",
        "formation": "📖 Chỉ sự: 皿 (mãnh – cái bát) + giọt chất lỏng bên trong. Hình ảnh bát đựng máu dùng trong nghi lễ tế thần thời xưa → máu, huyết. Mẹo: cái bát 皿 có giọt đỏ bên trong = máu.",
        "examples": [
          {"word": "血液", "hiragana": "けつえき", "meaning": "Huyết dịch, máu"},
          {"word": "血圧", "hiragana": "けつあつ", "meaning": "Huyết áp"},
          {"word": "出血", "hiragana": "しゅっけつ", "meaning": "Xuất huyết"},
          {"word": "血", "hiragana": "ち", "meaning": "Máu"},
          {"word": "血液型", "hiragana": "けつえきがた", "meaning": "Nhóm máu"}
        ]
      },
      {
        "character": "温",
        "han_viet": "Ôn",
        "onyomi": ["オン"],
        "kunyomi": ["あたたかい", "あたたか", "あたたまる", "あたためる", "ぬるい"],
        "meaning_vi": "Ấm, ôn hòa",
        "formation": "🔊 Hình thanh: 氵(thủy – nước) + 昷 (ôn – ấm, cho âm オン; gồm 日=mặt trời + 皿=bát). Mẹo: nước 氵 được mặt trời 日 hâm trong bát 皿 → ấm áp. Nhóm 昷→オン: 温(ôn=ấm), 穏(ổn=yên ổn).",
        "examples": [
          {"word": "温度", "hiragana": "おんど", "meaning": "Nhiệt độ"},
          {"word": "温泉", "hiragana": "おんせん", "meaning": "Suối nước nóng"},
          {"word": "気温", "hiragana": "きおん", "meaning": "Khí ôn, nhiệt độ"},
          {"word": "温かい", "hiragana": "あたたかい", "meaning": "Ấm áp"},
          {"word": "温暖", "hiragana": "おんだん", "meaning": "Ấm áp"}
        ]
      },
      {
        "character": "季",
        "han_viet": "Quý",
        "onyomi": ["キ"],
        "kunyomi": [],
        "meaning_vi": "Mùa",
        "formation": "📖 Hội ý: 禾 (hòa – lúa) + 子 (tử – con, hạt giống). Mẹo: Mỗi mùa, cây lúa 禾 sinh ra hạt con 子 → chu kỳ mùa vụ. Quý = khoảng thời gian 3 tháng = 1 mùa.",
        "examples": [
          {"word": "季節", "hiragana": "きせつ", "meaning": "Mùa, tiết"},
          {"word": "四季", "hiragana": "しき", "meaning": "Bốn mùa"},
          {"word": "雨季", "hiragana": "うき", "meaning": "Mùa mưa"},
          {"word": "季語", "hiragana": "きご", "meaning": "Từ chỉ mùa (thơ haiku)"}
        ]
      },
      {
        "character": "星",
        "han_viet": "Tinh",
        "onyomi": ["セイ"],
        "kunyomi": ["ほし"],
        "meaning_vi": "Ngôi sao, hành tinh",
        "formation": "🔊 Hình thanh: 日 (nhật – mặt trời, vật phát sáng) + 生 (sinh – sinh ra, cho âm セイ). Vật phát sáng sinh ra trên bầu trời đêm → ngôi sao. Nhóm âm 生→セイ: 星(tinh=sao), 性(tính=tính cách), 姓(tính=họ), 牲(sinh=hy sinh).",
        "examples": [
          {"word": "星", "hiragana": "ほし", "meaning": "Ngôi sao"},
          {"word": "惑星", "hiragana": "わくせい", "meaning": "Hành tinh"},
          {"word": "星座", "hiragana": "せいざ", "meaning": "Chòm sao"},
          {"word": "火星", "hiragana": "かせい", "meaning": "Sao Hỏa"},
          {"word": "流れ星", "hiragana": "ながれぼし", "meaning": "Sao băng"}
        ]
      }
    ]
  }
]


class Command(BaseCommand):
    help = "Load Kanji N2 - Bai 1~4"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-clear',
            action='store_true',
            dest='no_clear',
            help='Do not clear existing lessons before loading',
        )

    def handle(self, *args, **options):
        self.stdout.write("Loading N2 data (Bai 1~4)...")
        stats = _import_kanji_json(N2_DATA, replace=not options['no_clear'])
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created:\n"
            f"  - {stats['lessons']} lessons\n"
            f"  - {stats['kanji']} kanji\n"
            f"  - {stats['vocab']} new vocab\n"
            f"  - {stats.get('vocab_linked', 0)} vocab linked to Vocabulary\n"
        ))
