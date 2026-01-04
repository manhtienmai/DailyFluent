# Generated manually for enhanced vocabulary fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0014_englishvocabulary_audio_uk_and_more'),
    ]

    operations = [
        # Add fields to EnglishVocabulary
        migrations.AddField(
            model_name='englishvocabulary',
            name='pos',
            field=models.CharField(
                blank=True,
                help_text='Từ loại (noun, verb, adjective, adverb, etc.)',
                max_length=50,
                verbose_name='Part of Speech',
            ),
        ),
        migrations.AddField(
            model_name='englishvocabulary',
            name='pos_candidates',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Danh sách các từ loại có thể (JSON array)',
                verbose_name='POS Candidates',
            ),
        ),
        migrations.AddField(
            model_name='englishvocabulary',
            name='audio_pack_uuid',
            field=models.CharField(
                blank=True,
                help_text='UUID của audio pack để tải về sau',
                max_length=100,
                verbose_name='Audio Pack UUID',
            ),
        ),
        # Add fields to EnglishVocabularyExample
        migrations.AddField(
            model_name='englishvocabularyexample',
            name='sentence_marked',
            field=models.TextField(
                blank=True,
                help_text='Câu ví dụ với từ vựng được đánh dấu (ví dụ: ⟦word⟧)',
                verbose_name='Câu ví dụ có đánh dấu',
            ),
        ),
        migrations.AddField(
            model_name='englishvocabularyexample',
            name='sentence_en',
            field=models.TextField(
                blank=True,
                help_text='Câu ví dụ tiếng Anh không có đánh dấu',
                verbose_name='Câu ví dụ tiếng Anh (plain)',
            ),
        ),
        migrations.AddField(
            model_name='englishvocabularyexample',
            name='context',
            field=models.CharField(
                blank=True,
                help_text='Ngữ cảnh sử dụng (ví dụ: system update, order processing)',
                max_length=200,
                verbose_name='Context',
            ),
        ),
        migrations.AddField(
            model_name='englishvocabularyexample',
            name='word_count',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Số từ trong câu ví dụ',
                null=True,
                verbose_name='Word Count',
            ),
        ),
    ]

