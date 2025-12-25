from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GrammarPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('level', models.CharField(choices=[('N1', 'N1'), ('N2', 'N2'), ('N3', 'N3'), ('N4', 'N4'), ('N5', 'N5')], default='N5', max_length=2)),
                ('summary', models.TextField(blank=True, help_text='Mô tả ngắn / ý chính')),
                ('details', models.TextField(blank=True, help_text='Giải thích chi tiết (plain text hoặc Markdown)')),
                ('examples', models.TextField(blank=True, help_text='Ví dụ, mỗi dòng một câu')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['level', 'title'],
                'verbose_name': 'Ngữ pháp',
                'verbose_name_plural': 'Ngữ pháp',
            },
        ),
    ]

