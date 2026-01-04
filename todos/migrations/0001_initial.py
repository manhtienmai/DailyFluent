# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TodoItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Tiêu đề mục tiêu', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Mô tả chi tiết (tùy chọn)')),
                ('completed', models.BooleanField(default=False, help_text='Đã hoàn thành chưa')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Thời gian cập nhật')),
                ('due_date', models.DateField(blank=True, help_text='Hạn chót (tùy chọn)', null=True)),
                ('priority', models.CharField(choices=[('low', 'Thấp'), ('medium', 'Trung bình'), ('high', 'Cao')], default='medium', help_text='Mức độ ưu tiên', max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='todo_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mục tiêu',
                'verbose_name_plural': 'Mục tiêu',
                'ordering': ['-created_at'],
            },
        ),
    ]

