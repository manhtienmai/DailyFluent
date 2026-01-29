
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from vocab.models import Course

def create_courses():
    courses_data = [
        {
            'title': 'TOEIC 600 Essential',
            'slug': 'toeic-600-essential',
            'toeic_level': 600,
            'description': 'Từ vựng cơ bản dành cho người mới bắt đầu.',
            'icon': '🌱',
            'gradient': 'linear-gradient(135deg, #4caf50, #2e7d32)',
            'order': 1
        },
        {
            'title': 'TOEIC 730 Intermediate',
            'slug': 'toeic-730-intermediate',
            'toeic_level': 730,
            'description': 'Từ vựng trung cấp dành cho môi trường công sở.',
            'icon': '📘',
            'gradient': 'linear-gradient(135deg, #2196f3, #1565c0)',
            'order': 2
        },
        {
            'title': 'TOEIC 860 Advanced',
            'slug': 'toeic-860-advanced',
            'toeic_level': 860,
            'description': 'Từ vựng nâng cao để đạt điểm xuất sắc.',
            'icon': '🔮',
            'gradient': 'linear-gradient(135deg, #9c27b0, #6a1b9a)',
            'order': 3
        },
        {
            'title': 'TOEIC 990 Master',
            'slug': 'toeic-990-master',
            'toeic_level': 990,
            'description': 'Từ vựng chuyên sâu chinh phục điểm tuyệt đối.',
            'icon': '👑',
            'gradient': 'linear-gradient(135deg, #ff9800, #e65100)',
            'order': 4
        }
    ]

    print("Checking and creating default courses...")
    
    for data in courses_data:
        course, created = Course.objects.update_or_create(
            slug=data['slug'],
            defaults={
                'title': data['title'],
                'toeic_level': data['toeic_level'],
                'description': data['description'],
                'icon': data['icon'],
                'gradient': data['gradient'],
                'is_active': True,
                # 'order': data['order'] # Assuming order field might not exist or handled by ID/level
            }
        )
        status = "Created" if created else "Updated"
        print(f"[{status}] {course.title} (Level {course.toeic_level})")

    print("Done!")

if __name__ == "__main__":
    create_courses()
