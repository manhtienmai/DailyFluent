# shop/management/commands/seed_frames.py
"""
Seed sample avatar frames for the shop.
Run with: python manage.py seed_frames
"""

from django.core.management.base import BaseCommand
from shop.models import AvatarFrame


class Command(BaseCommand):
    help = 'Seed sample avatar frames for the shop'

    def handle(self, *args, **options):
        frames_data = [
            # COMMON (100-200 coins)
            {
                'name': 'Ocean Blue',
                'slug': 'ocean-blue',
                'description': 'Khung xanh dương đơn giản, thanh lịch',
                'price': 100,
                'rarity': 'COMMON',
                'css_gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'display_order': 1,
            },
            {
                'name': 'Forest Green',
                'slug': 'forest-green',
                'description': 'Khung xanh lá tự nhiên',
                'price': 100,
                'rarity': 'COMMON',
                'css_gradient': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                'display_order': 2,
            },
            {
                'name': 'Sunset Orange',
                'slug': 'sunset-orange',
                'description': 'Khung cam ấm áp như hoàng hôn',
                'price': 150,
                'rarity': 'COMMON',
                'css_gradient': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                'display_order': 3,
            },
            {
                'name': 'Midnight Purple',
                'slug': 'midnight-purple',
                'description': 'Khung tím huyền bí',
                'price': 150,
                'rarity': 'COMMON',
                'css_gradient': 'linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%)',
                'display_order': 4,
            },
            
            # RARE (300-500 coins)
            {
                'name': 'Electric Neon',
                'slug': 'electric-neon',
                'description': 'Khung neon rực rỡ với hiệu ứng phát sáng',
                'price': 300,
                'rarity': 'RARE',
                'css_gradient': 'linear-gradient(135deg, #00f260 0%, #0575e6 100%)',
                'css_animation': 'glow',
                'display_order': 10,
            },
            {
                'name': 'Cherry Blossom',
                'slug': 'cherry-blossom',
                'description': 'Khung hồng sakura lãng mạn',
                'price': 350,
                'rarity': 'RARE',
                'css_gradient': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
                'css_animation': 'pulse',
                'display_order': 11,
            },
            {
                'name': 'Cyber Blue',
                'slug': 'cyber-blue',
                'description': 'Khung xanh cyber phong cách tương lai',
                'price': 400,
                'rarity': 'RARE',
                'css_gradient': 'linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)',
                'css_animation': 'pulse',
                'display_order': 12,
            },
            {
                'name': 'Fire Storm',
                'slug': 'fire-storm',
                'description': 'Khung lửa rực cháy',
                'price': 450,
                'rarity': 'RARE',
                'css_gradient': 'linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%)',
                'css_animation': 'glow',
                'display_order': 13,
            },
            
            # EPIC (800-1200 coins)
            {
                'name': 'Aurora Borealis',
                'slug': 'aurora-borealis',
                'description': 'Khung cực quang huyền ảo',
                'price': 800,
                'rarity': 'EPIC',
                'css_gradient': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 50%, #667eea 100%)',
                'css_animation': 'rainbow',
                'border_width': 4,
                'display_order': 20,
            },
            {
                'name': 'Galaxy Swirl',
                'slug': 'galaxy-swirl',
                'description': 'Khung thiên hà xoáy với nhiều sắc màu',
                'price': 1000,
                'rarity': 'EPIC',
                'css_gradient': 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
                'css_animation': 'spin',
                'border_width': 4,
                'display_order': 21,
            },
            {
                'name': 'Crystal Ice',
                'slug': 'crystal-ice',
                'description': 'Khung băng pha lê lấp lánh',
                'price': 1100,
                'rarity': 'EPIC',
                'css_gradient': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
                'css_animation': 'glow',
                'border_width': 4,
                'display_order': 22,
            },
            
            # LEGENDARY (2000-5000 coins)
            {
                'name': 'Rainbow Prism',
                'slug': 'rainbow-prism',
                'description': 'Khung cầu vồng huyền thoại với hiệu ứng đổi màu liên tục',
                'price': 2500,
                'rarity': 'LEGENDARY',
                'css_gradient': 'linear-gradient(135deg, #f5af19 0%, #f12711 25%, #8e44ad 50%, #3498db 75%, #2ecc71 100%)',
                'css_animation': 'rainbow',
                'border_width': 5,
                'display_order': 30,
            },
            {
                'name': 'Golden Crown',
                'slug': 'golden-crown',
                'description': 'Khung vàng hoàng gia dành cho những người xuất sắc',
                'price': 3000,
                'rarity': 'LEGENDARY',
                'css_gradient': 'linear-gradient(135deg, #f7971e 0%, #ffd200 50%, #f7971e 100%)',
                'css_animation': 'glow',
                'border_width': 5,
                'display_order': 31,
            },
            {
                'name': 'Diamond Radiance',
                'slug': 'diamond-radiance',
                'description': 'Khung kim cương siêu hiếm với ánh sáng rực rỡ',
                'price': 5000,
                'rarity': 'LEGENDARY',
                'css_gradient': 'linear-gradient(135deg, #fff 0%, #e0e0e0 25%, #c0c0c0 50%, #e0e0e0 75%, #fff 100%)',
                'css_animation': 'rainbow',
                'border_width': 6,
                'display_order': 32,
            },
            
            # LEGENDARY with pre-rendered images
            {
                'name': 'Nebula Galaxy',
                'slug': 'nebula-galaxy',
                'description': 'Khung thiên hà sâu thẳm với bụi sao lấp lánh',
                'price': 4999,
                'rarity': 'LEGENDARY',
                'css_gradient': 'linear-gradient(135deg, #7C3AED 0%, #EC4899 50%, #06B6D4 100%)',
                'css_animation': 'glow',
                'border_width': 5,
                'display_order': 33,
            },
            {
                'name': 'Royal Gold',
                'slug': 'royal-gold',
                'description': 'Khung vàng hoàng gia với sư tử và kim cương',
                'price': 5999,
                'rarity': 'LEGENDARY',
                'css_gradient': 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%)',
                'css_animation': 'glow',
                'border_width': 5,
                'display_order': 34,
            },
            {
                'name': 'Frozen Aurora',
                'slug': 'frozen-aurora',
                'description': 'Khung băng giá với cực quang và rune ma thuật',
                'price': 4499,
                'rarity': 'LEGENDARY',
                'css_gradient': 'linear-gradient(135deg, #00FFFF 0%, #87CEEB 50%, #E0FFFF 100%)',
                'css_animation': 'glow',
                'border_width': 5,
                'display_order': 35,
            },
        ]

        created_count = 0
        for data in frames_data:
            frame, created = AvatarFrame.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {frame.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Exists: {frame.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal created: {created_count} frames'))
