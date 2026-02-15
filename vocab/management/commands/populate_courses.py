from django.core.management.base import BaseCommand
from vocab.models import Course

class Command(BaseCommand):
    help = 'Populate initial Course data for TOEIC levels'

    def handle(self, *args, **options):
        # Define default courses
        courses_data = [
            {
                'title': 'TOEIC 600 Cơ bản',
                'slug': 'toeic-600-essential',
                'description': 'Từ vựng cơ bản dành cho người mới bắt đầu.',
                'toeic_level': 600,
                'icon': '🌱',
                'gradient': 'linear-gradient(135deg, #4ade80 0%, #16a34a 100%)'
            },
            {
                'title': 'TOEIC 730 Trung cấp',
                'slug': 'toeic-730-intermediate',
                'description': 'Từ vựng trung cấp dành cho môi trường công sở.',
                'toeic_level': 730,
                'icon': '📘',
                'gradient': 'linear-gradient(135deg, #60a5fa 0%, #2563eb 100%)'
            },
            {
                'title': 'TOEIC 860 Nâng cao',
                'slug': 'toeic-860-advanced',
                'description': 'Từ vựng nâng cao để đạt điểm xuất sắc.',
                'toeic_level': 860,
                'icon': '🔮',
                'gradient': 'linear-gradient(135deg, #c084fc 0%, #7c3aed 100%)'
            },
            {
                'title': 'TOEIC 990 Chuyên gia',
                'slug': 'toeic-990-master',
                'description': 'Từ vựng chuyên sâu chinh phục điểm tuyệt đối.',
                'toeic_level': 990,
                'icon': '👑',
                'gradient': 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)'
            }
        ]

        self.stdout.write("Creating/Updating courses...")
        for data in courses_data:
            course, created = Course.objects.update_or_create(
                toeic_level=data['toeic_level'],
                defaults=data
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"- {status}: {course.title} ({course.slug})")

        self.stdout.write(self.style.SUCCESS("Done!"))
