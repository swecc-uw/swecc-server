from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
import random
from interview.models import InterviewPool


class Command(BaseCommand):
    help = "View the interview pool (current signups)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Clearing the interview pool..."))
        try:
            n, d = InterviewPool.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f"Interview pool cleared, {n} members removed")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
