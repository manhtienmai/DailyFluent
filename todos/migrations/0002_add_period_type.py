# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='todoitem',
            name='period_type',
            field=models.CharField(
                choices=[
                    ('day', 'Ngày'),
                    ('week', 'Tuần'),
                    ('month', 'Tháng'),
                    ('year', 'Năm'),
                ],
                default='day',
                help_text='Loại mục tiêu theo thời gian',
                max_length=10
            ),
        ),
    ]

