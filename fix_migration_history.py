import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.utils import timezone

with connection.cursor() as cursor:
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
        ['vocab', '0001_initial', timezone.now()]
    )
    print("Inserted vocab.0001_initial into django_migrations")
