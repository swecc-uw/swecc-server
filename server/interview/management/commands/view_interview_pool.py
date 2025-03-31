from django.core.management.base import BaseCommand
from interview.algorithm import CommonAvailabilityStableMatching
from interview.models import InterviewPool

algorithm = CommonAvailabilityStableMatching()


class Command(BaseCommand):
    help = "View the interview pool (current signups)"

    def handle(self, *args, **options):
        print("Viewing the interview pool...")
        for pool_member in list(InterviewPool.objects.all()):
            self.stdout.write(
                self.style.SUCCESS(f"Member: {pool_member.member.username}")
            )
