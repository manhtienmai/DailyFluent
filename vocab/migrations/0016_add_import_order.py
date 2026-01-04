# Generated manually for import order field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0015_add_enhanced_vocab_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='englishvocabulary',
            name='import_order',
            field=models.PositiveIntegerField(
                blank=True,
                db_index=True,
                help_text='Thứ tự import từ JSON (để giữ nguyên thứ tự ban đầu)',
                null=True,
                verbose_name='Import Order',
            ),
        ),
    ]

