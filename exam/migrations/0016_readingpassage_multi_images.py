from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("exam", "0015_examtemplate_audio_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReadingPassageImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=1, help_text="Thứ tự hiển thị ảnh trong passage")),
                ("image", models.ImageField(help_text="Ảnh thuộc passage (có thể upload nhiều ảnh).", upload_to="exam/reading_passages/")),
                ("caption", models.CharField(blank=True, help_text="Chú thích (optional)", max_length=255)),
                ("passage", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="exam.readingpassage")),
            ],
            options={
                "verbose_name": "Reading Passage Image",
                "verbose_name_plural": "Reading Passage Images",
                "ordering": ["passage_id", "order", "id"],
                "unique_together": {("passage", "order")},
            },
        ),
    ]


