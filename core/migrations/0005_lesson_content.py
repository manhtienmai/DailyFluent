# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_course_description_course_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='content',
            field=models.TextField(blank=True, help_text='Nội dung bài học (HTML). Hỗ trợ formatting với rich text editor.'),
        ),
    ]

