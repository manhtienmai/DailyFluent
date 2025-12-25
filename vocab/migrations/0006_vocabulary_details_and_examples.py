from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("vocab", "0005_userstudysettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="vocabulary",
            name="en_meaning",
            field=models.CharField(
                blank=True,
                help_text="Optional English meaning (if available)",
                max_length=255,
                verbose_name="Meaning (English)",
            ),
        ),
        migrations.AddField(
            model_name="vocabulary",
            name="notes",
            field=models.TextField(
                blank=True,
                help_text="Ghi chú thêm (mẹo nhớ, phân biệt nghĩa, ngữ cảnh sử dụng...)",
                verbose_name="Ghi chú / giải thích",
            ),
        ),
        migrations.CreateModel(
            name="VocabularyExample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=0)),
                ("jp", models.TextField(verbose_name="Ví dụ tiếng Nhật")),
                ("vi", models.TextField(blank=True, verbose_name="Dịch tiếng Việt")),
                (
                    "vocab",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="examples",
                        to="vocab.vocabulary",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ví dụ",
                "verbose_name_plural": "Ví dụ",
                "ordering": ["order", "id"],
            },
        ),
    ]

