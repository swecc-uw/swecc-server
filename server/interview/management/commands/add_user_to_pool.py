import random

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q
from django.utils import timezone
from interview.algorithm import CommonAvailabilityStableMatching
from interview.models import Interview, InterviewAvailability, InterviewPool
from members.models import User

algorithm = CommonAvailabilityStableMatching()


class Command(BaseCommand):
    help = "Add a user to the interview pool"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--username",
            type=str,
            help="Username of the user to add to the interview pool",
        )

        return super().add_arguments(parser)

    def handle(self, *args, **options):
        username = options["username"]
        if not username:
            self.stdout.write(
                self.style.ERROR(
                    "Please provide a username to add to the interview pool"
                )
            )
            return

        member = User.objects.filter(username=username).first()
        if not member:
            self.stdout.write(
                self.style.ERROR(f"User with username {username} not found")
            )
            return

        if InterviewPool.objects.filter(member=member).exists():
            self.stdout.write(
                self.style.WARNING(f"User {username} is already in the interview pool")
            )
            return

        InterviewPool.objects.create(member=member)
        self.stdout.write(
            self.style.SUCCESS(f"User {username} added to the interview pool")
        )
