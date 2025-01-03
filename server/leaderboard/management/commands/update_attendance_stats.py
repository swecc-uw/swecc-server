from django.core.management.base import BaseCommand
from members.models import User
from collections import defaultdict
from engagement.models import AttendanceSessionStats


class Command(BaseCommand):
    help = "Updates derived data for attendance stats"

    def handle(self, *args, **options):

        session_counts = defaultdict(int)

        for user in User.objects.all().values("id", "attendance_sessions"):
            session_counts[user["id"]] += 1 if user["attendance_sessions"] else 0

        for user_id, attended_sessions in session_counts.items():
            user_stats, _ = AttendanceSessionStats.objects.get_or_create(
                member_id=user_id
            )
            user_stats.sessions_attended = attended_sessions

            user_stats.save()

            self.stdout.write(self.style.SUCCESS(str(user_stats)))
