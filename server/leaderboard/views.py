import os
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics

from members.permissions import IsApiKey
from members.models import User
from .models import (
    GitHubStats,
    InternshipApplicationStats,
    LeetcodeStats,
    NewGradApplicationStats,
)
from .serializers import (
    GitHubStatsSerializer,
    InternshipApplicationStatsSerializer,
    LeetcodeStatsSerializer,
    NewGradApplicationStatsSerializer,
)
from django.db import transaction
from django.db.models import F, ExpressionWrapper, FloatField
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import logging
from rest_framework.response import Response
from rest_framework import status
from engagement.serializers import AttendanceStatsSerializer
from engagement.models import AttendanceSessionStats
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.db.models import Window
from django.db.models.functions import RowNumber

logger = logging.getLogger(__name__)
INTERNSHIP_CHANNEL_ID = int(os.getenv("INTERNSHIP_CHANNEL_ID"))
NEW_GRAD_CHANNEL_ID = int(os.getenv("NEW_GRAD_CHANNEL_ID"))


class LeetcodeLeaderboardView(generics.ListAPIView):
    serializer_class = LeetcodeStatsSerializer
    # allow any permission for now
    permission_classes = []

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
    permission_classes = []

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


class InternshipApplicationLeaderboardView(generics.ListAPIView):
    serializer_class = InternshipApplicationStatsSerializer
    permission_classes = []

    def get_queryset(self):
        order_by = self.request.query_params.get("order_by", "applied")
        time_range = self.request.query_params.get("updated_within", None)

        queryset = InternshipApplicationStats.objects.all()

        if time_range:
            try:
                hours = int(time_range)
                cutoff = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(last_updated__gte=cutoff)
            except ValueError:
                raise ValidationError("updated_within must be a valid number of hours")

        ordering_options = {
            "applied": "-applied",
            "recent": "-last_updated",
        }

        order_field = ordering_options.get(order_by)
        if not order_field:
            raise ValidationError(
                f"Invalid order_by parameter. Must be one of: {', '.join(ordering_options.keys())}"
            )

        return queryset.order_by(order_field)


class NewGradApplicationLeaderboardView(generics.ListAPIView):
    serializer_class = NewGradApplicationStatsSerializer
    permission_classes = []

    def get_queryset(self):
        order_by = self.request.query_params.get("order_by", "applied")
        time_range = self.request.query_params.get("updated_within", None)

        queryset = NewGradApplicationStats.objects.all()

        if time_range:
            try:
                hours = int(time_range)
                cutoff = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(last_updated__gte=cutoff)
            except ValueError:
                raise ValidationError("updated_within must be a valid number of hours")

        ordering_options = {
            "applied": "-applied",
            "recent": "-last_updated",
        }

        order_field = ordering_options.get(order_by)
        if not order_field:
            raise ValidationError(
                f"Invalid order_by parameter. Must be one of: {', '.join(ordering_options.keys())}"
            )

        return queryset.order_by(order_field)


class InjestReactionEventView(generics.CreateAPIView):
    permission_classes = [IsApiKey]

    def _get_user_id(self, discord_id):
        return get_object_or_404(User, discord_id=discord_id).id

    def _get_channel_config(self, channel_id):
        channel_configs = {
            INTERNSHIP_CHANNEL_ID: {
                "model": InternshipApplicationStats,
                "name": "internship",
            },
            NEW_GRAD_CHANNEL_ID: {
                "model": NewGradApplicationStats,
                "name": "new grad",
            },
        }
        return channel_configs.get(channel_id)

    def _handle_stats(self, user_id, channel_config, action="increment"):
        model = channel_config["model"]
        position_type = channel_config["name"]

        try:
            stats = model.objects.select_for_update().get(user_id=user_id)

            if action == "increment":
                stats.applied = F("applied") + 1
            elif action == "decrement" and stats.applied > 0:
                stats.applied = F("applied") - 1
            else:
                return False

            stats.save()
            stats.refresh_from_db()

            log_msg = (
                f"User {user_id} has {stats.applied} {position_type} "
                f"applications after {action}"
            )
            logger.info(log_msg)
            return True

        except model.DoesNotExist:
            if action == "increment":
                model.objects.create(user_id=user_id, applied=1)
                logger.info(f"Created new {position_type} stats for user {user_id}")
                return True
            return False

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        channel_id = request.data.get("channel_id")
        emoji = request.data.get("emoji")

        try:
            user_id = self._get_user_id(discord_id)
            channel_config = self._get_channel_config(channel_id)

            if not channel_config:
                logger.warning(
                    f"Invalid channel_id: {channel_id}, only supports "
                    f"{INTERNSHIP_CHANNEL_ID} and {NEW_GRAD_CHANNEL_ID}"
                )
                return Response(status=status.HTTP_304_NOT_MODIFIED)

            self._handle_stats(user_id, channel_config, "increment")
            return Response(status=status.HTTP_202_ACCEPTED)

        except Http404:
            logger.error(f"User not found for discord_id: {discord_id}")
            return Response(status=status.HTTP_404_NOT_FOUND)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        channel_id = request.data.get("channel_id")

        try:
            user_id = self._get_user_id(discord_id)
            channel_config = self._get_channel_config(channel_id)

            if not channel_config:
                logger.warning(
                    f"Invalid channel_id: {channel_id}, only supports "
                    f"{INTERNSHIP_CHANNEL_ID} and {NEW_GRAD_CHANNEL_ID}"
                )
                return Response(status=status.HTTP_304_NOT_MODIFIED)

            self._handle_stats(user_id, channel_config, "decrement")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            logger.error(f"User not found for discord_id: {discord_id}")
            return Response(status=status.HTTP_404_NOT_FOUND)


class AttendancePagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class AttendanceSessionLeaderboard(APIView):
    serializer_class = AttendanceStatsSerializer
    permission_classes = []
    pagination_class = AttendancePagination

    def get(self, request):
        order_by = request.query_params.get("order_by", "attendance")

        time_range = request.query_params.get("updated_within", None)

        queryset = AttendanceSessionStats.objects.all()

        if time_range:
            try:
                hours = int(time_range)
                cutoff = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(last_updated__gte=cutoff)
            except ValueError:
                raise ValidationError("updated_within must be a valid number of hours")

        ordering_options = {
            "attendance": "sessions_attended",
            "recent": "last_updated",
        }

        order_field = ordering_options.get(order_by)
        if not order_field:
            raise ValidationError(
                f"Invalid order_by parameter. Must be one of: {', '.join(ordering_options.keys())}"
            )
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(
            queryset.annotate(
                rank=Window(expression=RowNumber(), order_by=F(order_field).desc())
            ).order_by(f"-{order_field}"),
            request,
        )

        serializer = AttendanceStatsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
