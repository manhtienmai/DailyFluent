# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vocab', '0004_vocabulary_kanji_chars'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStudySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('new_cards_per_day', models.PositiveIntegerField(default=20, help_text='Số từ mới tối đa mỗi ngày')),
                ('reviews_per_day', models.PositiveIntegerField(default=200, help_text='Số lượt ôn tập tối đa mỗi ngày')),
                ('new_cards_today', models.PositiveIntegerField(default=0)),
                ('reviews_today', models.PositiveIntegerField(default=0)),
                ('last_study_date', models.DateField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='study_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cài đặt học tập',
                'verbose_name_plural': 'Cài đặt học tập',
            },
        ),
    ]

