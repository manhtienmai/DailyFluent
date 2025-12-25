from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vocab", "0006_vocabulary_details_and_examples"),
    ]

    operations = [
        migrations.AddField(
            model_name="vocabulary",
            name="is_verified",
            field=models.BooleanField(
                default=False,
                help_text="Tick khi bạn đã rà soát & sửa đúng dữ liệu từ này trong admin.",
                verbose_name="Đã kiểm tra",
            ),
        ),
    ]

