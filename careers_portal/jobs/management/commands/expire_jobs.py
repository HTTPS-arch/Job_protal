
from django.core.management.base import BaseCommand

from jobs.models import Job


class Command(BaseCommand):
    help = 'Mark overdue jobs as expired.'

    def handle(self, *args, **options):
        count = Job.objects.expire_due()

        self.stdout.write(
            self.style.SUCCESS(
                f'{count} overdue job(s) marked as expired.'
            )
        )
