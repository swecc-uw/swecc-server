from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
import random
from interview.models import InterviewPool, InterviewAvailability, Interview
from interview.algorithm import CommonAvailabilityStableMatching

algorithm = CommonAvailabilityStableMatching()


class Command(BaseCommand):
    help = "Pairs members for mock interviews based on availability"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Perform a dry run without creating pairs or sending emails",
        )

    def get_pool_members(self):
        """Get and prepare pool members, ensuring even number."""
        pool_members = list(InterviewPool.objects.all())

        if len(pool_members) % 2 != 0:
            random_idx = random.randint(0, len(pool_members) - 1)
            removed_member = pool_members.pop(random_idx)
            self.stdout.write(
                self.style.WARNING(
                    f"Removing member to ensure even pairs: {removed_member.member.username}"
                )
            )

        return pool_members

    def get_availabilities(self, pool_members):
        """Get availability slots for all members."""
        return {
            member.member.id: (
                InterviewAvailability.objects.get(
                    member=member.member
                ).interview_availability_slots
                if InterviewAvailability.objects.filter(member=member.member).exists()
                else [[False] * 48 for _ in range(7)]
            )
            for member in pool_members
        }

    def handle(self, *args, **options):
        is_dry_run = options["dry"]

        # get pool members
        pool_members = self.get_pool_members()

        if len(pool_members) < 2:
            self.stdout.write(
                self.style.ERROR("Not enough members in the pool to pair interviews")
            )
            return

        self.stdout.write(f"Found {len(pool_members)} members in the pool")

        # get availabilities
        availabilities = self.get_availabilities(pool_members)
        pool_member_ids = [m.member.id for m in pool_members]

        # set up algo
        pairing_algorithm = algorithm
        pairing_algorithm.set_availabilities(availabilities)
        matches = pairing_algorithm.pair(pool_member_ids)

        # display matches
        self.stdout.write(self.style.SUCCESS("\nProposed pairs:"))
        paired_count = 0
        for i, j in enumerate(matches):
            if i < j:  # Avoid showing duplicate pairs
                p1 = pool_members[i].member
                p2 = pool_members[j].member
                self.stdout.write(f"Pair {paired_count + 1}:")
                self.stdout.write(f"  - {p1.username} ({p1.email})")
                self.stdout.write(f"  - {p2.username} ({p2.email})")
                paired_count += 1

        # if not a dry run, create interviews and send notifications
        if not is_dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis is a live run - creating pairs and sending notifications..."
                )
            )

            # delete existing interviews for this period
            today = timezone.now()
            last_monday = today - timezone.timedelta(days=today.weekday())
            last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            next_next_monday = last_monday + timezone.timedelta(days=14)

            deleted_count = Interview.objects.filter(
                date_effective__gte=last_monday, date_effective__lte=next_next_monday
            ).delete()

            self.stdout.write(f"Deleted {deleted_count[0]} existing interviews")

            # create new interviews
            paired_interviews = []
            for i, j in enumerate(matches):
                if i < j:
                    p1 = pool_members[i].member
                    p2 = pool_members[j].member

                    interview1 = Interview.objects.create(
                        interviewer=p1,
                        interviewee=p2,
                        status="pending",
                        date_effective=timezone.now(),
                    )

                    interview2 = Interview.objects.create(
                        interviewer=p2,
                        interviewee=p1,
                        status="pending",
                        date_effective=timezone.now(),
                    )

                    paired_interviews.append(interview1)
                    paired_interviews.append(interview2)

                    # remove paired users from the pool
                    InterviewPool.objects.filter(member__in=[p1, p2]).delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully created {len(paired_interviews)} interviews"
                )
            )

            # display remaining unpaired members
            unpaired_members = InterviewPool.objects.all()
            if unpaired_members.exists():
                self.stdout.write(self.style.WARNING("\nUnpaired members:"))
                for member in unpaired_members:
                    self.stdout.write(f"  - {member.member.username}")

        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nDry run completed - no interviews were created or emails sent"
                )
            )
