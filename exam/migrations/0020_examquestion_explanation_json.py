from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exam", "0019_alter_readingpassage_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="examquestion",
            name="explanation_json",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="JSON giải thích chi tiết đáp án (dùng cho UI kết quả/giải thích). Gợi ý schema: meta, correct_option, content_translation, overall_analysis, options_breakdown, vocabulary_extraction.",
            ),
        ),
    ]


