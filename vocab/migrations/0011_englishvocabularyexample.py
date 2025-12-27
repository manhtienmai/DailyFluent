from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0010_englishvocabulary_fsrscardstateen'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnglishVocabularyExample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('en', models.TextField(verbose_name='Câu ví dụ tiếng Anh')),
                ('vi', models.TextField(blank=True, verbose_name='Dịch tiếng Việt')),
                ('vocab', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examples', to='vocab.englishvocabulary')),
            ],
            options={
                'verbose_name': 'Ví dụ EN',
                'verbose_name_plural': 'Ví dụ EN',
                'ordering': ['order', 'id'],
            },
        ),
    ]

