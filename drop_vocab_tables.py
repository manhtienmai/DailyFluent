import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def drop_tables():
    tables_to_drop = [
        'vocab_setitem', # If exists from failed attempt
        'vocab_vocabularyset',
        'vocab_worddefinition',
        'vocab_vocabulary', # New table name same as old, but old has different schema? Old was vocab_vocabulary too.
        'vocab_englishvocabulary', 
        'vocab_englishvocabularyexample', 
        'vocab_fixedphrase', 
        'vocab_fixedphraseexample', 
        'vocab_fsrscardstate', 
        'vocab_fsrscardstateen',
        'vocab_userstudysettings', # Keeping UserStudySettings -> DROPPING IT NOW to fix migration 0001
        'vocab_vocabularyexample',
    ]
    
    with connection.cursor() as cursor:
        # Disable foreign key checks for sqlite/mysql/postgres to make dropping easier if order matters
        # For SQLite: PRAGMA foreign_keys = OFF;
        try:
             cursor.execute("PRAGMA foreign_keys = OFF;") 
        except:
             pass 

        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped {table} CASCADE")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        # Clear migration history for vocab AND exam (to re-sync)
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'vocab';")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'exam';")
            print("Cleared migration history for 'vocab' and 'exam'")
        except Exception as e:
            print(f"Error clearing migrations: {e}")

if __name__ == "__main__":
    drop_tables()
