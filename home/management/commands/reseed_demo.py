from django.core.management.base import BaseCommand

from home.demo_data import reseed_starter_activities


class Command(BaseCommand):
    help = (
        "Move the 6 starter activities back to upcoming dates (tomorrow and the "
        "next few days) so the feed looks alive for a demo. Posts made by users "
        "are never touched."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-joins', action='store_true',
            help='Also remove everyone who joined the starter activities (fresh 0 going).',
        )

    def handle(self, *args, clear_joins=False, **options):
        updated, created, joins_removed = reseed_starter_activities(clear_joins=clear_joins)
        self.stdout.write(self.style.SUCCESS(
            f'Starter activities ready: {updated} moved to upcoming dates, {created} recreated.'
        ))
        if clear_joins:
            self.stdout.write(f'Removed {joins_removed} join(s) from starter activities.')
