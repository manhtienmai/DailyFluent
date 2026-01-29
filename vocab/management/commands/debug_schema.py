from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Diffs the actual DB schema against expected models'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # 1. List all tables
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'vocab_%';")
            tables = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f"Vocab Tables: {tables}")
            
            # 2. Check row counts
            for table in ['vocab_vocabulary', 'vocab_englishvocabulary']:
                if table in tables:
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"Table '{table}' row count: {count}")
                else:
                    self.stdout.write(f"Table '{table}' DOES NOT EXIST")

            # 3. Check constraints on fsrscardstateen
            if 'vocab_fsrscardstateen' in tables:
                cursor.execute("""
                    SELECT conname, pg_get_constraintdef(c.oid)
                    FROM pg_constraint c
                    JOIN pg_namespace n ON n.oid = c.connamespace
                    WHERE n.nspname = 'public' 
                    AND conrelid = 'vocab_fsrscardstateen'::regclass;
                """)
                constraints = cursor.fetchall()
                self.stdout.write("\nConstraints on vocab_fsrscardstateen:")
                for name, definition in constraints:
                    self.stdout.write(f"- {name}: {definition}")
