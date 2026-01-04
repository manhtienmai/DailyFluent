from django.core.management.base import BaseCommand
from exam.models import ExamTemplate, TOEICPart


class Command(BaseCommand):
    help = "Update ExamTemplate title from READING_ETS2026_TEST1 to a better name"

    def add_arguments(self, parser):
        parser.add_argument(
            '--old-title',
            type=str,
            default='READING_ETS2026_TEST1',
            help='Old template title to find'
        )
        parser.add_argument(
            '--new-title',
            type=str,
            default=None,
            help='New template title (if not provided, will auto-detect based on questions)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating'
        )

    def handle(self, *args, **options):
        old_title = options['old_title']
        new_title = options['new_title']
        dry_run = options['dry_run']

        # Find the template
        template = ExamTemplate.objects.filter(title=old_title).first()

        if not template:
            self.stdout.write(self.style.ERROR(f"Template '{old_title}' not found!"))
            return

        self.stdout.write(f"Found template:")
        self.stdout.write(f"  ID: {template.id}")
        self.stdout.write(f"  Title: {template.title}")
        self.stdout.write(f"  Slug: {template.slug}")
        self.stdout.write(f"  Category: {template.category}")
        self.stdout.write(f"  Is full TOEIC: {template.is_full_toeic}")
        self.stdout.write(f"  Total questions: {template.total_questions}")

        # Check if it has both listening and reading
        listening_questions = template.questions.filter(toeic_part__in=['L1', 'L2', 'L3', 'L4']).count()
        reading_questions = template.questions.filter(toeic_part__in=['R5', 'R6', 'R7']).count()

        self.stdout.write(f"\nQuestions breakdown:")
        self.stdout.write(f"  Listening: {listening_questions}")
        self.stdout.write(f"  Reading: {reading_questions}")

        # Determine new name if not provided
        if not new_title:
            if listening_questions > 0 and reading_questions > 0:
                # Remove "READING_" prefix since it has both
                new_title = old_title.replace("READING_", "").replace("LISTENING_", "")
                if not new_title.startswith("ETS"):
                    new_title = f"ETS{new_title}" if new_title.startswith("2026") else new_title
            elif listening_questions > 0:
                new_title = old_title.replace("READING_", "LISTENING_")
            else:
                new_title = old_title  # Keep as is if only reading

        if new_title == template.title:
            self.stdout.write(self.style.SUCCESS(f"\nNo change needed. Title is already: {template.title}"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\n[DRY RUN] Would update:"))
            self.stdout.write(f"  Old title: {template.title}")
            self.stdout.write(f"  New title: {new_title}")
            self.stdout.write(f"  Old slug: {template.slug}")
            # Show what new slug would be
            from utils.slug import to_romaji_slug
            new_slug = to_romaji_slug(new_title)
            self.stdout.write(f"  New slug (estimated): {new_slug}")
        else:
            old_title_value = template.title
            old_slug_value = template.slug

            template.title = new_title
            # Slug will be auto-generated on save if needed
            template.save()

            self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully updated:"))
            self.stdout.write(f"  Old title: {old_title_value}")
            self.stdout.write(f"  New title: {template.title}")
            self.stdout.write(f"  Old slug: {old_slug_value}")
            self.stdout.write(f"  New slug: {template.slug}")

