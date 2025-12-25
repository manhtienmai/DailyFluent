from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("vocab", "0007_vocabulary_is_verified"),
    ]

    operations = [
        migrations.CreateModel(
            name="FixedPhrase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jp_text", models.CharField(max_length=200, verbose_name="Cụm từ (JP)")),
                ("jp_kana", models.CharField(blank=True, max_length=200, verbose_name="Hiragana/Kana")),
                ("vi_meaning", models.CharField(blank=True, max_length=255, verbose_name="Nghĩa tiếng Việt")),
                ("en_meaning", models.CharField(blank=True, max_length=255, verbose_name="Meaning (English)")),
                ("notes", models.TextField(blank=True, verbose_name="Ghi chú / giải thích")),
                ("is_active", models.BooleanField(default=True)),
                (
                    "is_verified",
                    models.BooleanField(
                        default=False,
                        help_text="Tick khi bạn đã rà soát & sửa đúng dữ liệu cụm từ trong admin.",
                        verbose_name="Đã kiểm tra",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Cụm từ cố định",
                "verbose_name_plural": "Cụm từ cố định",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="FixedPhraseExample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=0)),
                ("jp", models.TextField(verbose_name="Ví dụ tiếng Nhật")),
                ("vi", models.TextField(blank=True, verbose_name="Dịch tiếng Việt")),
                (
                    "phrase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="examples",
                        to="vocab.fixedphrase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ví dụ cụm từ",
                "verbose_name_plural": "Ví dụ cụm từ",
                "ordering": ["order", "id"],
            },
        ),
    ]

