
import os, django
import sys
from django.conf import settings

# Setup Django
sys.path.append('E:\\DailyFluent')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from vocab.models import Course, VocabularySet, UserSetProgress
from vocab import toeic_utils # CORRECTED IMPORT
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(username='mtmanh').first() or User.objects.first()
print(f"User: {user}")

print("--- Simulating CourseListView Logic ---")

courses = Course.objects.filter(is_active=True).order_by('toeic_level')
print(f"Courses Queryset count: {courses.count()}")

courses_data = []
for course in courses:
    level = course.toeic_level
    print(f"Processing Course: {course.title} (Level: {level})")
    
    if not level:
        print("  - Skipped: No level")
        continue

    try:
        completion = toeic_utils.get_level_completion_percent(user, level)
        print(f"  - Completion: {completion}")
        
        learned_count = toeic_utils.get_level_words_learned_count(user, level)
        print(f"  - Learned: {learned_count}")
        
        total_sets = VocabularySet.objects.filter(toeic_level=level, status='published').count()
        print(f"  - Total Sets: {total_sets}")
        
        completed_sets = UserSetProgress.objects.filter(
            user=user, 
            vocabulary_set__toeic_level=level, 
            status=UserSetProgress.ProgressStatus.COMPLETED
        ).count()
        print(f"  - Completed Sets: {completed_sets}")
        
        item_data = {
            'object': course,
            'slug': course.slug, 
            'completion': completion,
            # ...
        }
        courses_data.append(item_data)
        print("  - Added to list")
        
    except Exception as e:
        print(f"  - ERROR: {e}")
        import traceback
        traceback.print_exc()

print(f"Final courses_data length: {len(courses_data)}")
