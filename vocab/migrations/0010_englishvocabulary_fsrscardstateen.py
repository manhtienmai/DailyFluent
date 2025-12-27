from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0008_fixedphrase_models'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EnglishVocabulary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('en_word', models.CharField(max_length=200, verbose_name='Từ vựng tiếng Anh')),
                ('phonetic', models.CharField(blank=True, max_length=200, verbose_name='Phiên âm')),
                ('vi_meaning', models.CharField(max_length=255, verbose_name='Nghĩa tiếng Việt')),
                ('en_definition', models.TextField(blank=True, verbose_name='Định nghĩa tiếng Anh')),
                ('example_en', models.TextField(blank=True, verbose_name='Câu ví dụ tiếng Anh')),
                ('example_vi', models.TextField(blank=True, verbose_name='Nghĩa câu ví dụ (VI)')),
                ('notes', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('lesson', models.CharField(blank=True, max_length=100, verbose_name='Lesson')),
                ('course', models.CharField(blank=True, max_length=100, verbose_name='Course')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Từ vựng tiếng Anh',
                'verbose_name_plural': 'Từ vựng tiếng Anh',
                'ordering': ['en_word'],
            },
        ),
        migrations.CreateModel(
            name='FsrsCardStateEn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_json', models.JSONField()),
                ('due', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_reviewed', models.DateTimeField(blank=True, null=True)),
                ('total_reviews', models.PositiveIntegerField(default=0)),
                ('successful_reviews', models.PositiveIntegerField(default=0)),
                ('last_rating', models.CharField(blank=True, max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fsrs_cards_en', to=settings.AUTH_USER_MODEL)),
                ('vocab', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fsrs_states_en', to='vocab.englishvocabulary')),
            ],
            options={
                'verbose_name': 'FSRS EN',
                'verbose_name_plural': 'FSRS EN',
            },
        ),
        migrations.AlterUniqueTogether(
            name='fsrscardstateen',
            unique_together={('user', 'vocab')},
        ),
    ]

