"""
Add language field to Course model, create Mimikara N2 course,
and assign sequential set_number to JP VocabularySets.
"""
from django.db import migrations, models


def create_mimikara_course_and_assign_set_numbers(apps, schema_editor):
    Course = apps.get_model('vocab', 'Course')
    VocabularySet = apps.get_model('vocab', 'VocabularySet')

    # Create Mimikara N2 course
    Course.objects.get_or_create(
        slug='mimikara-n2',
        defaults={
            'title': 'Mimikara N2',
            'description': 'Từ vựng N2 - Mimikara Oboeru',
            'language': 'jp',
            'toeic_level': None,
            'icon': '🇯🇵',
            'gradient': 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
            'is_active': True,
        },
    )

    # Assign sequential set_number to JP sets that don't have one
    jp_sets = VocabularySet.objects.filter(
        language='jp',
        toeic_level__isnull=True,
        set_number__isnull=True,
    ).order_by('chapter', 'id')

    for idx, vs in enumerate(jp_sets, start=1):
        vs.set_number = idx
        vs.save(update_fields=['set_number'])


def reverse_migration(apps, schema_editor):
    Course = apps.get_model('vocab', 'Course')
    Course.objects.filter(slug='mimikara-n2').delete()

    VocabularySet = apps.get_model('vocab', 'VocabularySet')
    VocabularySet.objects.filter(
        language='jp', toeic_level__isnull=True,
    ).update(set_number=None)


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0015_add_setitemexample'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='language',
            field=models.CharField(
                choices=[('en', 'English'), ('jp', 'Japanese')],
                default='en',
                max_length=10,
            ),
        ),
        migrations.RunPython(
            create_mimikara_course_and_assign_set_numbers,
            reverse_migration,
        ),
    ]
