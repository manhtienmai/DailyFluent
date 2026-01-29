from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fixes schema inconsistency: Updates FK on FsrsCardStateEn to point to correct table'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # 1. Inspect tables
            cursor.execute("SELECT to_regclass('public.vocab_vocabulary');")
            new_table = cursor.fetchone()[0]
            
            cursor.execute("SELECT to_regclass('public.vocab_englishvocabulary');")
            old_table = cursor.fetchone()[0]

            self.stdout.write(f"Vocab Table (New): {new_table}")
            self.stdout.write(f"Vocab Table (Old): {old_table}")

            if not new_table:
                self.stdout.write(self.style.ERROR("CRITICAL: 'vocab_vocabulary' table missing through logic assumes it exists!"))
                return

            # 2. Fix FK on fsrscardstateen
            # The error is: violates foreign key constraint "vocab_fsrscardstatee_vocab_id_25fde2bb_fk_vocab_eng"
            # We need to genericize the drop in case the name varies, but hardcoded is safer for this specific error.
            
            constraints_to_drop = [
                "vocab_fsrscardstatee_vocab_id_25fde2bb_fk_vocab_eng",
                "vocab_fsrscardstatee_vocab_id_25fde2bb_fk_vocab_englishvocabulary_id" 
            ]

            for constraint in constraints_to_drop:
                try:
                    cursor.execute(f"ALTER TABLE vocab_fsrscardstateen DROP CONSTRAINT IF EXISTS {constraint};")
                    self.stdout.write(f"Dropped constraint: {constraint}")
                except Exception as e:
                    self.stdout.write(f"Error dropping {constraint}: {e}")

            # 3. Add correct FK
            try:
                # Validate if constraint exists
                cursor.execute("""
                    SELECT 1 FROM pg_constraint WHERE conname = 'vocab_fsrscardstateen_vocab_id_fk_vocab_vocabulary_id'
                """)
                if not cursor.fetchone():
                    self.stdout.write("Adding correct FK constraint pointing to 'vocab_vocabulary'...")
                    cursor.execute("""
                        ALTER TABLE vocab_fsrscardstateen 
                        ADD CONSTRAINT vocab_fsrscardstateen_vocab_id_fk_vocab_vocabulary_id 
                        FOREIGN KEY (vocab_id) REFERENCES vocab_vocabulary(id) DEFERRABLE INITIALLY DEFERRED;
                    """)
                    self.stdout.write(self.style.SUCCESS("Success: FK Constraint fixed."))
                else:
                    self.stdout.write(self.style.WARNING("Correct FK constraint already exists."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to add FK: {e}"))
                self.stdout.write("Hint: Check if all vocab_id in fsrscardstateen exist in vocab_vocabulary.")
