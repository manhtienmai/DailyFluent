"""
Management command to fix Kanji data:
- Supplement missing Vietnamese diacritics in sino_vi and meaning_vi
- Fix 畑 sino_vi
- Add kunyomi for kanji that have common kunyomi readings
"""
import sys
from django.core.management.base import BaseCommand
from kanji.models import Kanji


# Mapping: kanji char -> corrected (sino_vi, meaning_vi)
# Based on standard Hán Việt readings
KANJI_FIXES = {
    # ===== N5 Bài 2: Kanji made from picture 2 (nature) =====
    '川': {'sino_vi': 'Xuyên', 'meaning_vi': 'Sông'},
    '天': {'sino_vi': 'Thiên', 'meaning_vi': 'Trời'},
    '気': {'sino_vi': 'Khí', 'meaning_vi': 'Khí, tinh thần'},

    # ===== N5 Bài 3: Kanji for human relationships 1 =====
    '母': {'sino_vi': 'Mẫu', 'meaning_vi': 'Mẹ'},
    '私': {'sino_vi': 'Tư', 'meaning_vi': 'Tôi'},
    '兄': {'meaning_vi': 'Anh trai'},
    '姉': {'sino_vi': 'Tỷ', 'meaning_vi': 'Chị gái'},
    '弟': {'sino_vi': 'Đệ', 'meaning_vi': 'Em trai'},
    '妹': {'sino_vi': 'Muội', 'meaning_vi': 'Em gái'},

    # ===== N5 Bài 4: Numbers =====
    '三': {'meaning_vi': 'Ba'},
    '四': {'sino_vi': 'Tứ', 'meaning_vi': 'Bốn'},
    '五': {'sino_vi': 'Ngũ', 'meaning_vi': 'Năm'},
    '六': {'sino_vi': 'Lục', 'meaning_vi': 'Sáu'},
    '七': {'sino_vi': 'Thất', 'meaning_vi': 'Bảy'},
    '九': {'sino_vi': 'Cửu', 'meaning_vi': 'Chín'},

    # ===== N5 Bài 5: Numbers 2 =====
    '百': {'sino_vi': 'Bách', 'meaning_vi': 'Trăm'},
    '千': {'sino_vi': 'Thiên', 'meaning_vi': 'Nghìn'},
    '万': {'sino_vi': 'Vạn', 'meaning_vi': 'Vạn (mười nghìn)'},
    '円': {'sino_vi': 'Viên', 'meaning_vi': 'Yên, tròn'},
    '年': {'sino_vi': 'Niên', 'meaning_vi': 'Năm'},
    '半': {'sino_vi': 'Bán', 'meaning_vi': 'Một nửa'},
    '分': {'sino_vi': 'Phân', 'meaning_vi': 'Phút, chia'},
    '時': {'sino_vi': 'Thời', 'meaning_vi': 'Giờ, thời gian'},

    # ===== N5 Bài 6: Kanji made from picture 3 (human) =====
    '学': {'sino_vi': 'Học', 'meaning_vi': 'Học'},
    '先': {'sino_vi': 'Tiên', 'meaning_vi': 'Trước'},

    # ===== N5 Bài 7: Kanji made from picture 4 (body) =====
    '体': {'sino_vi': 'Thể', 'meaning_vi': 'Cơ thể'},

    # ===== N5 Bài 8: Kanji made from signs =====
    '上': {'sino_vi': 'Thượng', 'meaning_vi': 'Trên'},
    '下': {'sino_vi': 'Hạ', 'meaning_vi': 'Dưới'},
    '中': {'meaning_vi': 'Trong, giữa'},
    '本': {'sino_vi': 'Bản', 'meaning_vi': 'Sách, gốc'},
    '何': {'sino_vi': 'Hà', 'meaning_vi': 'Cái gì'},
    '出': {'sino_vi': 'Xuất', 'meaning_vi': 'Ra ngoài'},

    # ===== N5 Bài 9: Kanji made from a combination of the meanings =====
    '明': {'meaning_vi': 'Sáng'},
    '休': {'sino_vi': 'Hưu', 'meaning_vi': 'Nghỉ ngơi'},
    '好': {'sino_vi': 'Hảo', 'meaning_vi': 'Thích'},
    '男': {'meaning_vi': 'Đàn ông'},
    '間': {'meaning_vi': 'Ở giữa, gian'},
    '畑': {'sino_vi': 'Điền (quốc tự)', 'meaning_vi': 'Ruộng khô'},

    # ===== N5 Bài 10: Kanji carrying the meaning of Position 1 =====
    '右': {'sino_vi': 'Hữu', 'meaning_vi': 'Phải'},
    '左': {'sino_vi': 'Tả', 'meaning_vi': 'Trái'},
    '東': {'sino_vi': 'Đông', 'meaning_vi': 'Phía đông'},
    '西': {'sino_vi': 'Tây', 'meaning_vi': 'Phía tây'},
    '北': {'sino_vi': 'Bắc', 'meaning_vi': 'Phía bắc'},
    '南': {'meaning_vi': 'Phía nam'},
    '外': {'sino_vi': 'Ngoại', 'meaning_vi': 'Bên ngoài'},
    '駅': {'sino_vi': 'Dịch', 'meaning_vi': 'Nhà ga'},
    '会': {'sino_vi': 'Hội', 'meaning_vi': 'Gặp gỡ'},
    '内': {'sino_vi': 'Nội', 'meaning_vi': 'Bên trong'},

    # ===== N5 Bài 11: Kanji for Adjectives 1 =====
    '名': {'meaning_vi': 'Tên'},

    # ===== N5 Bài 12: Kanji for Verbs 1 =====
    '来': {'sino_vi': 'Lai', 'meaning_vi': 'Đến'},
    '聞': {'sino_vi': 'Văn', 'meaning_vi': 'Nghe'},
    '読': {'sino_vi': 'Đọc', 'meaning_vi': 'Đọc'},
    '書': {'sino_vi': 'Thư', 'meaning_vi': 'Viết'},
    '話': {'meaning_vi': 'Nói chuyện'},

    # ===== N5 Bài 13: Kanji for Time 1 =====
    '午': {'sino_vi': 'Ngọ', 'meaning_vi': 'Trưa'},
    '前': {'sino_vi': 'Tiền', 'meaning_vi': 'Trước'},
    '後': {'sino_vi': 'Hậu', 'meaning_vi': 'Sau'},
    '毎': {'sino_vi': 'Mỗi', 'meaning_vi': 'Mỗi'},

    # ===== N5 Bài 14: Other common Kanji =====
    '校': {'sino_vi': 'Hiệu', 'meaning_vi': 'Trường học'},
    '語': {'sino_vi': 'Ngữ', 'meaning_vi': 'Ngôn ngữ'},
    '今': {'meaning_vi': 'Bây giờ'},
    '電': {'sino_vi': 'Điện', 'meaning_vi': 'Điện'},
    '国': {'sino_vi': 'Quốc', 'meaning_vi': 'Đất nước'},

    # ===== N4 =====
    '買': {'sino_vi': 'Mãi', 'meaning_vi': 'Mua'},  # already correct sino_vi

    # ===== Additional N5 with ASCII sino_vi from audit =====
    '山': {'sino_vi': 'Sơn', 'meaning_vi': 'Núi'},
    '火': {'sino_vi': 'Hỏa', 'meaning_vi': 'Lửa'},
    '水': {'sino_vi': 'Thủy', 'meaning_vi': 'Nước'},
    '木': {'sino_vi': 'Mộc', 'meaning_vi': 'Cây, gỗ'},
    '金': {'sino_vi': 'Kim', 'meaning_vi': 'Vàng, kim loại, tiền'},
    '土': {'sino_vi': 'Thổ', 'meaning_vi': 'Đất'},
    '日': {'sino_vi': 'Nhật', 'meaning_vi': 'Ngày, mặt trời'},
    '月': {'sino_vi': 'Nguyệt', 'meaning_vi': 'Tháng, mặt trăng'},
    '人': {'sino_vi': 'Nhân', 'meaning_vi': 'Người'},
    '口': {'sino_vi': 'Khẩu', 'meaning_vi': 'Miệng'},
    '目': {'sino_vi': 'Mục', 'meaning_vi': 'Mắt'},
    '耳': {'sino_vi': 'Nhĩ', 'meaning_vi': 'Tai'},
    '手': {'sino_vi': 'Thủ', 'meaning_vi': 'Tay'},
    '足': {'sino_vi': 'Túc', 'meaning_vi': 'Chân'},
    '力': {'sino_vi': 'Lực', 'meaning_vi': 'Sức mạnh'},
    '父': {'sino_vi': 'Phụ', 'meaning_vi': 'Cha'},
    '友': {'sino_vi': 'Hữu', 'meaning_vi': 'Bạn'},
    '女': {'sino_vi': 'Nữ', 'meaning_vi': 'Nữ, phụ nữ'},
    '子': {'sino_vi': 'Tử', 'meaning_vi': 'Con'},
    '一': {'sino_vi': 'Nhất', 'meaning_vi': 'Một'},
    '二': {'sino_vi': 'Nhị', 'meaning_vi': 'Hai'},
    '八': {'sino_vi': 'Bát', 'meaning_vi': 'Tám'},
    '十': {'sino_vi': 'Thập', 'meaning_vi': 'Mười'},
    '大': {'sino_vi': 'Đại', 'meaning_vi': 'Lớn'},
    '小': {'sino_vi': 'Tiểu', 'meaning_vi': 'Nhỏ'},
    '高': {'sino_vi': 'Cao', 'meaning_vi': 'Cao'},
    '安': {'sino_vi': 'An', 'meaning_vi': 'Yên, rẻ'},
    '白': {'sino_vi': 'Bạch', 'meaning_vi': 'Trắng'},
    '長': {'sino_vi': 'Trường', 'meaning_vi': 'Dài'},
    '多': {'sino_vi': 'Đa', 'meaning_vi': 'Nhiều'},
    '少': {'sino_vi': 'Thiểu', 'meaning_vi': 'Ít'},
    '新': {'sino_vi': 'Tân', 'meaning_vi': 'Mới'},
    '古': {'sino_vi': 'Cổ', 'meaning_vi': 'Cũ'},
    '入': {'sino_vi': 'Nhập', 'meaning_vi': 'Vào'},
    '食': {'sino_vi': 'Thực', 'meaning_vi': 'Ăn'},
    '飲': {'sino_vi': 'Ẩm', 'meaning_vi': 'Uống'},
    '見': {'sino_vi': 'Kiến', 'meaning_vi': 'Nhìn'},
    '行': {'sino_vi': 'Hành', 'meaning_vi': 'Đi'},
    '立': {'sino_vi': 'Lập', 'meaning_vi': 'Đứng'},
    '車': {'sino_vi': 'Xa', 'meaning_vi': 'Xe'},
    '門': {'sino_vi': 'Môn', 'meaning_vi': 'Cổng'},
    '雨': {'sino_vi': 'Vũ', 'meaning_vi': 'Mưa'},
    '花': {'meaning_vi': 'Hoa'},
    '週': {'meaning_vi': 'Tuần'},
    '曜': {'sino_vi': 'Diệu', 'meaning_vi': 'Thứ (ngày trong tuần)'},
    '晩': {'sino_vi': 'Vãn', 'meaning_vi': 'Tối'},

    # N4 kanji with missing diacritics
    '茶': {'sino_vi': 'Trà', 'meaning_vi': 'Trà'},
    '字': {'sino_vi': 'Tự', 'meaning_vi': 'Chữ'},
    '部': {'sino_vi': 'Bộ', 'meaning_vi': 'Bộ phận'},
    '院': {'sino_vi': 'Viện', 'meaning_vi': 'Học viện'},
    '宅': {'sino_vi': 'Trạch', 'meaning_vi': 'Nhà'},
    '客': {'sino_vi': 'Khách', 'meaning_vi': 'Khách'},
    '英': {'meaning_vi': 'Anh, tài giỏi'},
    '度': {'sino_vi': 'Độ', 'meaning_vi': 'Độ, lần'},
    '便': {'sino_vi': 'Tiện', 'meaning_vi': 'Tiện lợi, thư'},
    '利': {'sino_vi': 'Lợi', 'meaning_vi': 'Lợi ích'},
    '不': {'sino_vi': 'Bất', 'meaning_vi': 'Không'},
    '地': {'sino_vi': 'Địa', 'meaning_vi': 'Đất'},
    '館': {'sino_vi': 'Quán', 'meaning_vi': 'Tòa nhà'},
    '番': {'sino_vi': 'Phiên', 'meaning_vi': 'Số'},
    '号': {'sino_vi': 'Hiệu', 'meaning_vi': 'Số hiệu'},
    '京': {'meaning_vi': 'Kinh đô'},
    '質': {'sino_vi': 'Chất', 'meaning_vi': 'Chất lượng, hỏi'},
    '題': {'sino_vi': 'Đề', 'meaning_vi': 'Đề tài'},
    '理': {'sino_vi': 'Lý', 'meaning_vi': 'Lý do'},
    '科': {'meaning_vi': 'Khoa'},
    '医': {'meaning_vi': 'Y học'},

    # N2 kanji needing meaning_vi fix
    '菜': {'meaning_vi': 'Rau'},  # already ASCII but correct
    '周': {'meaning_vi': 'Xung quanh, chu vi'},  # already correct
    '庫': {'sino_vi': 'Khố', 'meaning_vi': 'Kho'},
    '皮': {'sino_vi': 'Bì', 'meaning_vi': 'Da'},
}


class Command(BaseCommand):
    help = 'Fix missing Vietnamese diacritics in Kanji sino_vi and meaning_vi fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating',
        )

    def handle(self, *args, **options):
        sys.stdout.reconfigure(encoding='utf-8')
        dry_run = options['dry_run']
        updated_count = 0
        not_found = []

        for char, fixes in KANJI_FIXES.items():
            try:
                kanji = Kanji.objects.get(char=char)
            except Kanji.DoesNotExist:
                not_found.append(char)
                continue

            changes = []
            update_fields = []

            for field, new_value in fixes.items():
                old_value = getattr(kanji, field)
                # Only update if the current value is ASCII-only or empty
                if old_value and not old_value.isascii():
                    # Already has diacritics, skip
                    continue
                if old_value != new_value:
                    changes.append(f'  {field}: "{old_value}" -> "{new_value}"')
                    setattr(kanji, field, new_value)
                    update_fields.append(field)

            if update_fields:
                self.stdout.write(f'{char}:')
                for c in changes:
                    self.stdout.write(c)
                if not dry_run:
                    kanji.save(update_fields=update_fields)
                updated_count += 1

        action = 'Would update' if dry_run else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'\n{action} {updated_count} kanji entries.')
        )
        if not_found:
            self.stdout.write(
                self.style.WARNING(f'Not found in DB: {", ".join(not_found)}')
            )
