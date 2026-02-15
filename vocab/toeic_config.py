"""
TOEIC Level configuration constants.
"""

TOEIC_LEVELS = {
    600: {
        'label': 'TOEIC 600',
        'description': 'Từ vựng kinh doanh cơ bản',
        'total_sets': 40,
        'color': '#10B981',       # Emerald/green
        'gradient': 'linear-gradient(135deg, #10B981, #059669)',
        'bg_gradient': 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
        'icon': '🌱',
        'unlock_requirement': None,
        'unlock_text': '',
    },
    730: {
        'label': 'TOEIC 730',
        'description': 'Từ vựng kinh doanh trung cấp',
        'total_sets': 30,
        'color': '#3B82F6',       # Blue
        'gradient': 'linear-gradient(135deg, #3B82F6, #2563EB)',
        'bg_gradient': 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
        'icon': '📘',
        'unlock_requirement': None,
        'unlock_text': '',
    },
    860: {
        'label': 'TOEIC 860',
        'description': 'Từ vựng kinh doanh nâng cao',
        'total_sets': 20,
        'color': '#8B5CF6',       # Purple
        'gradient': 'linear-gradient(135deg, #8B5CF6, #7C3AED)',
        'bg_gradient': 'linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)',
        'icon': '🔮',
        'unlock_requirement': None,
        'unlock_text': '',
    },
    990: {
        'label': 'TOEIC 990',
        'description': 'Từ vựng trình độ chuyên gia',
        'total_sets': 10,
        'color': '#F59E0B',       # Amber/gold
        'gradient': 'linear-gradient(135deg, #F59E0B, #D97706)',
        'bg_gradient': 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
        'icon': '👑',
        'unlock_requirement': None,
        'unlock_text': '',
    },
}

TOEIC_LEVEL_ORDER = [600, 730, 860, 990]
