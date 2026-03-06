"""
Management command: migrate all Kanji-related data to Azure PostgreSQL.

Usage:
    python manage.py migrate_kanji_to_azure                    # full migration
    python manage.py migrate_kanji_to_azure --dry-run          # preview only
    python manage.py migrate_kanji_to_azure --skip-progress    # skip user progress
    python manage.py migrate_kanji_to_azure --force-update     # overwrite existing
    python manage.py migrate_kanji_to_azure --batch-size 200   # custom batch size
"""

import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connections

from kanji.models import (
    KanjiLesson, Kanji, KanjiVocab,
    UserKanjiProgress, KanjiQuizQuestion,
)


AZURE_DB = "azure"


class Command(BaseCommand):
    help = "Migrate all Kanji-related data from default DB to Azure PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview migration counts without writing anything.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Batch size for bulk operations (default: 100).",
        )
        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Overwrite existing records on Azure.",
        )
        parser.add_argument(
            "--skip-progress",
            action="store_true",
            help="Skip UserKanjiProgress (user-specific data).",
        )

    # ── helpers ────────────────────────────────────────────

    def _header(self, msg):
        self.stdout.write(self.style.HTTP_INFO(f"\n{'=' * 60}"))
        self.stdout.write(self.style.HTTP_INFO(f"  {msg}"))
        self.stdout.write(self.style.HTTP_INFO(f"{'=' * 60}"))

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f"  ✓ {msg}"))

    def _skip(self, msg):
        self.stdout.write(self.style.WARNING(f"  ⏭ {msg}"))

    def _err(self, msg):
        self.stdout.write(self.style.ERROR(f"  ✗ {msg}"))

    # ── main ──────────────────────────────────────────────

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        force_update = options["force_update"]
        skip_progress = options["skip_progress"]

        # 1. Check Azure DB is configured
        from django.conf import settings
        if AZURE_DB not in settings.DATABASES:
            raise CommandError(
                "AZURE_DATABASE_URL is not set in .env. "
                "Add it and restart to enable the 'azure' database alias."
            )

        self._header("Kanji Data Migration → Azure PostgreSQL")

        if dry_run:
            self.stdout.write(self.style.WARNING("  *** DRY-RUN MODE – no data will be written ***\n"))

        # 2. Show source counts
        self._header("Source DB (local) record counts")
        counts = {
            "KanjiLesson": KanjiLesson.objects.using("default").count(),
            "Kanji": Kanji.objects.using("default").count(),
            "KanjiVocab": KanjiVocab.objects.using("default").count(),
            "KanjiQuizQuestion": KanjiQuizQuestion.objects.using("default").count(),
            "UserKanjiProgress": UserKanjiProgress.objects.using("default").count(),
        }
        for model_name, count in counts.items():
            suffix = " (will skip)" if model_name == "UserKanjiProgress" and skip_progress else ""
            self._ok(f"{model_name}: {count} records{suffix}")

        if dry_run:
            self._header("DRY-RUN complete. No changes made.")
            return

        # 3. Run migrations on Azure DB
        self._header("Running migrations on Azure DB")
        try:
            call_command("migrate", database=AZURE_DB, verbosity=0)
            self._ok("Migrations applied successfully.")
        except Exception as e:
            raise CommandError(f"Failed to run migrations on Azure: {e}")

        # 4. Migrate data
        stats = {"created": 0, "skipped": 0, "updated": 0, "errors": 0}

        # 4a. KanjiLesson
        lesson_id_map = self._migrate_kanji_lessons(batch_size, force_update, stats)

        # 4b. Kanji
        kanji_id_map = self._migrate_kanjis(lesson_id_map, batch_size, force_update, stats)

        # 4c. KanjiVocab
        self._migrate_kanji_vocabs(kanji_id_map, batch_size, force_update, stats)

        # 4d. KanjiQuizQuestion
        self._migrate_quiz_questions(kanji_id_map, batch_size, force_update, stats)

        # 4e. UserKanjiProgress
        if skip_progress:
            self._skip("UserKanjiProgress skipped (--skip-progress).")
        else:
            self._migrate_user_progress(kanji_id_map, batch_size, force_update, stats)

        # 5. Summary
        self._header("Migration Summary")
        self._ok(f"Created:  {stats['created']}")
        self._ok(f"Skipped:  {stats['skipped']}")
        self._ok(f"Updated:  {stats['updated']}")
        if stats["errors"]:
            self._err(f"Errors:   {stats['errors']}")
        else:
            self._ok(f"Errors:   0")

        # 6. Verify Azure counts
        self._header("Azure DB record counts (post-migration)")
        for model_cls in [KanjiLesson, Kanji, KanjiVocab, KanjiQuizQuestion, UserKanjiProgress]:
            count = model_cls.objects.using(AZURE_DB).count()
            self._ok(f"{model_cls.__name__}: {count}")

        self.stdout.write(self.style.SUCCESS("\n🎉 Migration complete!\n"))

    # ── Model-specific migrate methods ─────────────────────

    def _migrate_kanji_lessons(self, batch_size, force_update, stats):
        """Migrate KanjiLesson (no FK dependencies)."""
        self._header("Migrating KanjiLesson")

        id_map = {}  # old_id → new_id
        lessons = list(KanjiLesson.objects.using("default").all())

        for lesson in lessons:
            old_id = lesson.pk
            try:
                existing = KanjiLesson.objects.using(AZURE_DB).filter(
                    jlpt_level=lesson.jlpt_level,
                    lesson_number=lesson.lesson_number,
                ).first()

                if existing:
                    if force_update:
                        existing.topic = lesson.topic
                        existing.order = lesson.order
                        existing.save(using=AZURE_DB)
                        id_map[old_id] = existing.pk
                        stats["updated"] += 1
                    else:
                        id_map[old_id] = existing.pk
                        stats["skipped"] += 1
                else:
                    new = KanjiLesson(
                        jlpt_level=lesson.jlpt_level,
                        lesson_number=lesson.lesson_number,
                        topic=lesson.topic,
                        order=lesson.order,
                    )
                    new.save(using=AZURE_DB)
                    id_map[old_id] = new.pk
                    stats["created"] += 1
            except Exception as e:
                self._err(f"KanjiLesson {lesson}: {e}")
                stats["errors"] += 1

        self._ok(f"Processed {len(lessons)} lessons, mapped {len(id_map)} IDs.")
        return id_map

    def _migrate_kanjis(self, lesson_id_map, batch_size, force_update, stats):
        """Migrate Kanji (FK → KanjiLesson)."""
        self._header("Migrating Kanji")

        id_map = {}  # old_id → new_id
        kanjis = list(Kanji.objects.using("default").select_related("lesson").all())

        for kanji in kanjis:
            old_id = kanji.pk
            try:
                existing = Kanji.objects.using(AZURE_DB).filter(char=kanji.char).first()

                if existing:
                    if force_update:
                        existing.lesson_id = lesson_id_map.get(kanji.lesson_id) if kanji.lesson_id else None
                        existing.order = kanji.order
                        existing.sino_vi = kanji.sino_vi
                        existing.keyword = kanji.keyword
                        existing.onyomi = kanji.onyomi
                        existing.kunyomi = kanji.kunyomi
                        existing.meaning_vi = kanji.meaning_vi
                        existing.strokes = kanji.strokes
                        existing.note = kanji.note
                        existing.formation = kanji.formation
                        existing.save(using=AZURE_DB)
                        id_map[old_id] = existing.pk
                        stats["updated"] += 1
                    else:
                        id_map[old_id] = existing.pk
                        stats["skipped"] += 1
                else:
                    new = Kanji(
                        char=kanji.char,
                        lesson_id=lesson_id_map.get(kanji.lesson_id) if kanji.lesson_id else None,
                        order=kanji.order,
                        sino_vi=kanji.sino_vi,
                        keyword=kanji.keyword,
                        onyomi=kanji.onyomi,
                        kunyomi=kanji.kunyomi,
                        meaning_vi=kanji.meaning_vi,
                        strokes=kanji.strokes,
                        note=kanji.note,
                        formation=kanji.formation,
                    )
                    new.save(using=AZURE_DB)
                    id_map[old_id] = new.pk
                    stats["created"] += 1
            except Exception as e:
                self._err(f"Kanji {kanji.char}: {e}")
                stats["errors"] += 1

        self._ok(f"Processed {len(kanjis)} kanji, mapped {len(id_map)} IDs.")
        return id_map

    def _migrate_kanji_vocabs(self, kanji_id_map, batch_size, force_update, stats):
        """Migrate KanjiVocab (FK → Kanji)."""
        self._header("Migrating KanjiVocab")

        vocabs = list(
            KanjiVocab.objects.using("default")
            .select_related("kanji")
            .all()
        )
        processed = 0

        for vocab in vocabs:
            new_kanji_id = kanji_id_map.get(vocab.kanji_id)
            if not new_kanji_id:
                self._err(f"KanjiVocab '{vocab.word}': kanji_id {vocab.kanji_id} not in map.")
                stats["errors"] += 1
                continue

            try:
                existing = KanjiVocab.objects.using(AZURE_DB).filter(
                    kanji_id=new_kanji_id,
                    word=vocab.word,
                ).first()

                if existing:
                    if force_update:
                        existing.reading = vocab.reading
                        existing.meaning = vocab.meaning
                        existing.priority = vocab.priority
                        existing.jlpt_level = vocab.jlpt_level
                        # Note: vocabulary FK skipped (cross-app reference)
                        existing.save(using=AZURE_DB)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    new = KanjiVocab(
                        kanji_id=new_kanji_id,
                        word=vocab.word,
                        reading=vocab.reading,
                        meaning=vocab.meaning,
                        priority=vocab.priority,
                        jlpt_level=vocab.jlpt_level,
                        # vocabulary FK is left null (cross-app, will be linked later)
                    )
                    new.save(using=AZURE_DB)
                    stats["created"] += 1
                processed += 1
            except Exception as e:
                self._err(f"KanjiVocab '{vocab.word}': {e}")
                stats["errors"] += 1

        self._ok(f"Processed {processed}/{len(vocabs)} vocab entries.")

    def _migrate_quiz_questions(self, kanji_id_map, batch_size, force_update, stats):
        """Migrate KanjiQuizQuestion (FK → Kanji)."""
        self._header("Migrating KanjiQuizQuestion")

        questions = list(
            KanjiQuizQuestion.objects.using("default")
            .select_related("kanji")
            .all()
        )
        processed = 0

        for qq in questions:
            new_kanji_id = kanji_id_map.get(qq.kanji_id)
            if not new_kanji_id:
                self._err(f"QuizQuestion for kanji_id {qq.kanji_id}: not in map.")
                stats["errors"] += 1
                continue

            try:
                existing = KanjiQuizQuestion.objects.using(AZURE_DB).filter(
                    kanji_id=new_kanji_id,
                    question_type=qq.question_type,
                ).first()

                if existing:
                    if force_update:
                        existing.correct_answer = qq.correct_answer
                        existing.distractors = qq.distractors
                        existing.save(using=AZURE_DB)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    new = KanjiQuizQuestion(
                        kanji_id=new_kanji_id,
                        question_type=qq.question_type,
                        correct_answer=qq.correct_answer,
                        distractors=qq.distractors,
                    )
                    new.save(using=AZURE_DB)
                    stats["created"] += 1
                processed += 1
            except Exception as e:
                self._err(f"QuizQuestion kanji={qq.kanji.char} type={qq.question_type}: {e}")
                stats["errors"] += 1

        self._ok(f"Processed {processed}/{len(questions)} quiz questions.")

    def _migrate_user_progress(self, kanji_id_map, batch_size, force_update, stats):
        """Migrate UserKanjiProgress (FK → Kanji, FK → User)."""
        self._header("Migrating UserKanjiProgress")

        from django.contrib.auth import get_user_model
        User = get_user_model()

        progress_entries = list(
            UserKanjiProgress.objects.using("default")
            .select_related("user", "kanji")
            .all()
        )

        if not progress_entries:
            self._skip("No UserKanjiProgress records to migrate.")
            return

        # Build user email → azure user ID map
        user_emails = set(p.user.email for p in progress_entries if p.user)
        azure_users = {
            u.email: u.pk
            for u in User.objects.using(AZURE_DB).filter(email__in=user_emails)
        }

        # Create missing users on Azure (basic copy)
        local_users = {u.email: u for u in User.objects.using("default").filter(email__in=user_emails)}
        for email in user_emails:
            if email not in azure_users and email in local_users:
                lu = local_users[email]
                try:
                    new_user = User(
                        username=lu.username,
                        email=lu.email,
                        first_name=lu.first_name,
                        last_name=lu.last_name,
                        is_active=lu.is_active,
                        date_joined=lu.date_joined,
                    )
                    new_user.password = lu.password  # copy hashed password
                    new_user.save(using=AZURE_DB)
                    azure_users[email] = new_user.pk
                    self._ok(f"Created user '{email}' on Azure.")
                except Exception as e:
                    self._err(f"Failed to create user '{email}' on Azure: {e}")

        processed = 0
        for entry in progress_entries:
            new_kanji_id = kanji_id_map.get(entry.kanji_id)
            azure_user_id = azure_users.get(entry.user.email) if entry.user else None

            if not new_kanji_id or not azure_user_id:
                stats["skipped"] += 1
                continue

            try:
                existing = UserKanjiProgress.objects.using(AZURE_DB).filter(
                    user_id=azure_user_id,
                    kanji_id=new_kanji_id,
                ).first()

                if existing:
                    if force_update:
                        existing.status = entry.status
                        existing.correct_streak = entry.correct_streak
                        existing.last_practiced = entry.last_practiced
                        existing.save(using=AZURE_DB)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    new = UserKanjiProgress(
                        user_id=azure_user_id,
                        kanji_id=new_kanji_id,
                        status=entry.status,
                        correct_streak=entry.correct_streak,
                        last_practiced=entry.last_practiced,
                    )
                    new.save(using=AZURE_DB)
                    stats["created"] += 1
                processed += 1
            except Exception as e:
                self._err(f"UserKanjiProgress user={entry.user.email} kanji={entry.kanji.char}: {e}")
                stats["errors"] += 1

        self._ok(f"Processed {processed}/{len(progress_entries)} progress entries.")
