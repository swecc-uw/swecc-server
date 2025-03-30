import random

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from interview.algorithm import CommonAvailabilityStableMatching
from interview.models import Interview, InterviewAvailability, InterviewPool

algorithm = CommonAvailabilityStableMatching()


class Command(BaseCommand):
    help = "View the interview pool (current signups)"

    def handle(self, *args, **options):
        print("Viewing the interview pool...")
        for pool_member in list(InterviewPool.objects.all()):
            self.stdout.write(
                self.style.SUCCESS(f"Member: {pool_member.member.username}")
            )
