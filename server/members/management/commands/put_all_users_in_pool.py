import random

from django.core.management.base import BaseCommand
from interview.models import InterviewAvailability, InterviewPool
from members.models import User


class Command(BaseCommand):
    help = "Puts all users in the pool with random availability"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="dont actually update anything, just print what would be done",
        )

    def generate_random_availability(self):
        return [[random.choice([True, False]) for _ in range(48)] for _ in range(7)]

    def handle(self, *args, **options):
        is_dry_run = options["dry"]

        users = User.objects.all()

        # add all users to the pool
        for user in users:
            if not InterviewPool.objects.filter(member=user).exists():
                InterviewPool.objects.create(member=user)
                self.stdout.write(f"Added {user.username} to the pool")

        # random availability for all users without availability
        for user in users:
            if not InterviewAvailability.objects.filter(member=user).exists():
                InterviewAvailability.objects.create(
                    member=user,
                    interview_availability_slots=self.generate_random_availability(),
                )
                self.stdout.write(f"Added random availability for {user.username}")

        if is_dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run complete"))
        else:
            self.stdout.write(self.style.SUCCESS("All users added to pool"))
