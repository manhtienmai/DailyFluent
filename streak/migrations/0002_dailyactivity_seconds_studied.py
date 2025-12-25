from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("streak", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dailyactivity",
            name="seconds_studied",
            field=models.PositiveIntegerField(default=0),
        ),
    ]

