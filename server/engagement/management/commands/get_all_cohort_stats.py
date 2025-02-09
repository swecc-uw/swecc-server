from django.core.management.base import BaseCommand
from engagement.models import CohortStats
from engagement.serializers import CohortStatsSerializer


class Command(BaseCommand):
    help = "List all `CohortStats` objects"

    def handle(self, *args, **options):

        cohort_stats = CohortStats.objects.all()
        for cohort_stat in cohort_stats:
            self.stdout.write(
                self.style.SUCCESS(f"{CohortStatsSerializer(cohort_stat).data}")
            )
