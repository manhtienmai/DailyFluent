from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exam", "0016_readingpassage_multi_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="readingpassage",
            name="content_json",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]


