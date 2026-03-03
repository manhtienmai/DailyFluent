# -*- coding: utf-8 -*-
"""
Update N2 Lesson 5 kanji with proper 形声 (hình thanh) analysis.
Format: X(ý: meaning) + Y(âm: sound) for phono-semantic characters.
Run: $env:PYTHONIOENCODING='utf-8'; python manage.py update_n2_l5_formation
"""
from django.core.management.base import BaseCommand
from kanji.models import Kanji


class Command(BaseCommand):
    help = 'Update N2 Lesson 5 kanji with proper hình thanh formation analysis'

    def handle(self, *args, **options):
        DATA = {
            # char: (formation, note)
            '庫': (
                'Hội ý: 广(ý: mái nhà) + 車(ý: xe) → nhà chứa xe, kho',
                'Dưới mái nhà 广 có nhiều xe 車 → nhà KHO chứa xe.'
            ),
            '坂': (
                'Hình thanh: 土(ý: đất) + 反(âm: ハン) → con dốc',
                'Đất 土 nghiêng → con DỐC. Âm ハン từ 反 (phản). Đường đi ngược lên là dốc.'
            ),
            '底': (
                'Hình thanh: 广(ý: nhà) + 氐(âm: テイ) → đáy, phần thấp nhất',
                'Phần thấp nhất 氐 dưới mái nhà 广 → ĐÁY. Âm テイ từ 氐.'
            ),
            '寺': (
                'Hội ý: 土(ý: đất) + 寸(ý: tấc, đo lường) → chùa',
                'Mảnh đất 土 được đo đạc 寸 để xây CHÙA. Nơi tôn nghiêm được quy hoạch cẩn thận.'
            ),
            '希': (
                'Hội ý: 㐅(ý: thưa, ít) + 巾(ý: vải) → hiếm, hi vọng',
                'Tấm vải 巾 dệt thưa 㐅 rất HIẾM. Từ nghĩa hiếm mở rộng thành hi vọng (mong điều hiếm xảy ra).'
            ),
            '仲': (
                'Hình thanh: 亻(ý: người) + 中(âm: チュウ) → trung gian, hòa giải',
                'Người 亻ở giữa 中 → TRỌNG tài, người trung gian. Âm チュウ từ 中 (trung).'
            ),
            '栄': (
                'Hội ý: ⺌(ý: ánh sáng) + 冖(ý: mái che) + 木(ý: cây) → vinh, thịnh vượng',
                'Cây 木 được che chở 冖 và tỏa sáng ⺌ → VINH quang. Cây tốt tươi là biểu tượng phồn vinh.'
            ),
            '札': (
                'Hình thanh: 木(ý: gỗ) + 乚(âm: サツ) → thẻ gỗ, tiền giấy',
                'Miếng gỗ 木 nhỏ dùng làm THẺ viết chữ → nghĩa mở rộng thành tiền giấy.'
            ),
            '板': (
                'Hình thanh: 木(ý: gỗ) + 反(âm: ハン/バン) → tấm ván, bảng',
                'Gỗ 木 được bào phẳng → tấm BẢN, tấm ván. Âm バン từ 反 (phản).'
            ),
            '包': (
                'Tượng hình: 勹(ý: bao bọc) + 巳(ý: thai nhi) → gói, bao',
                'Hình thai nhi 巳 được bao bọc 勹 → BAO bọc, gói ghém. Nghĩa gốc là mang thai.'
            ),
            '焼': (
                'Hình thanh: 火(ý: lửa) + 尭(âm: ギョウ→ショウ) → đốt, nướng',
                'Lửa 火 bốc lên → THIÊU đốt, nướng. Âm ショウ biến đổi từ 尭.'
            ),
            '章': (
                'Hội ý: 立(ý: đứng) + 早(ý: sáng sớm) → chương, bài văn hoàn chỉnh',
                'Đứng dậy 立 từ sớm 早 viết nên bài văn → CHƯƠNG sách. Mỗi chương là một đơn vị hoàn chỉnh.'
            ),
            '照': (
                'Hình thanh: 昭(âm: ショウ) + 灬(ý: lửa) → chiếu sáng',
                'Ngọn lửa 灬 tỏa sáng rõ ràng → CHIẾU sáng. Âm ショウ từ 昭 (chiêu).'
            ),
            '秒': (
                'Hình thanh: 禾(ý: lúa) + 少(âm: ショウ→ビョウ) → giây, rất nhỏ',
                'Phần nhỏ nhất 少 của cây lúa 禾 → GIÂY (đơn vị nhỏ nhất). Âm ビョウ biến đổi từ 少.'
            ),
            '皮': (
                'Tượng hình: hình bàn tay lột da thú vật',
                'Hình bàn tay đang lột DA thú vật. Chữ gốc là hình ảnh lột vỏ bên ngoài.'
            ),
            '漁': (
                'Hình thanh: 氵(ý: nước) + 魚(âm: ギョ) → đánh cá, ngư nghiệp',
                'Bắt cá 魚 dưới nước 氵→ NGƯ, đánh cá. Âm ギョ từ 魚 (ngư).'
            ),
            '貯': (
                'Hình thanh: 貝(ý: tiền/vỏ sò) + 宁(âm: チョ) → tích trữ, để dành',
                'Cất tiền 貝 vào nơi chứa → TRỮ, tích trữ. Âm チョ từ 宁 (trữ).'
            ),
            '柱': (
                'Hình thanh: 木(ý: gỗ) + 主(âm: シュ→チュウ) → cột trụ',
                'Cây gỗ 木 chính 主 chống đỡ ngôi nhà → TRỤ cột. Âm チュウ từ 主 (chủ).'
            ),
            '祭': (
                'Hội ý: ⺼(ý: thịt) + 又(ý: tay) + 示(ý: bàn thờ) → tế lễ',
                'Tay 又 dâng thịt ⺼ lên bàn thờ 示 → TẾ lễ, lễ hội. Nghi thức cúng tế truyền thống.'
            ),
            '筆': (
                'Hình thanh: ⺮(ý: tre) + 聿(âm: イツ→ヒツ) → bút',
                'Cây tre ⺮ dùng để viết 聿 → BÚT lông. Âm ヒツ từ 聿. Bút lông làm từ tre và lông thú.'
            ),
        }

        updated = 0
        for char, (formation, note) in DATA.items():
            try:
                kanji = Kanji.objects.get(char=char)
                kanji.formation = formation
                kanji.note = note
                kanji.save(update_fields=['formation', 'note'])
                updated += 1
                self.stdout.write(f"  OK: {char}")
            except Kanji.DoesNotExist:
                self.stderr.write(f"  SKIP: {char} not found")
            except Exception as e:
                self.stderr.write(f"  ERROR: {char} - {e}")

        self.stdout.write(self.style.SUCCESS(f"\nUpdated {updated}/20 kanji with hình thanh formation analysis."))
