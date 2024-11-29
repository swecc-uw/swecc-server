from rest_framework import generics
from members.permissions import IsApiKey
from .models import GitHubStats, LeetcodeStats
from .serializers import GitHubStatsSerializer, LeetcodeStatsSerializer
from django.db.models import F, ExpressionWrapper, FloatField
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


class LeetcodeLeaderboardView(generics.ListAPIView):
    serializer_class = LeetcodeStatsSerializer
    permission_classes = [IsApiKey]

    def get_queryset(self):
        latest_stat = LeetcodeStats.objects.order_by("-last_updated").first()
        order_by = self.request.query_params.get("order_by", "total")
        time_range = self.request.query_params.get("updated_within", None)

        queryset = LeetcodeStats.objects.all()
        queryset = queryset.annotate(
            completion_rate=ExpressionWrapper(
                (F("total_solved") * 100.0)
                / (F("easy_solved") + F("medium_solved") + F("hard_solved")),
                output_field=FloatField(),
            )
        )

        if time_range:
            try:
                hours = int(time_range)
                cutoff = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(last_updated__gte=cutoff)
            except ValueError:
                raise ValidationError("updated_within must be a valid number of hours")

        ordering_options = {
            "total": "-total_solved",
            "easy": "-easy_solved",
            "medium": "-medium_solved",
            "hard": "-hard_solved",
            "recent": "-last_updated",
            "completion": "-completion_rate",
        }

        order_field = ordering_options.get(order_by)
        if not order_field:
            raise ValidationError(
                f"Invalid order_by parameter. Must be one of: {', '.join(ordering_options.keys())}"
            )

        return queryset.order_by(order_field)


class GitHubLeaderboardView(generics.ListAPIView):
    serializer_class = GitHubStatsSerializer
    permission_classes = [IsApiKey]

    def get_queryset(self):
        order_by = self.request.query_params.get("order_by", "commits")
        time_range = self.request.query_params.get("updated_within", None)

        queryset = GitHubStats.objects.all()

        if time_range:
            try:
                hours = int(time_range)
                cutoff = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(last_updated__gte=cutoff)
            except ValueError:
                raise ValidationError("updated_within must be a valid number of hours")

        ordering_options = {
            "commits": "-total_commits",
            "prs": "-total_prs",
            "followers": "-followers",
            "recent": "-last_updated",
        }

        order_field = ordering_options.get(order_by)
        if not order_field:
            raise ValidationError(
                f"Invalid order_by parameter. Must be one of: {', '.join(ordering_options.keys())}"
            )

        return queryset.order_by(order_field)
