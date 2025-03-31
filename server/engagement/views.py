import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import pydantic
from custom_auth.permissions import IsAdmin, IsVerified
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from email_util.send_email import send_email
from leaderboard.models import GitHubStats, LeetcodeStats
from leaderboard.serializers import GitHubStatsSerializer, LeetcodeStatsSerializer
from members.models import User
from members.permissions import IsApiKey
from members.serializers import UserSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .buffer import Message, MessageBuffer
from .models import (
    AttendanceSession,
    AttendanceSessionStats,
    CohortStats,
    DiscordMessageStats,
)
from .serializers import AttendanceSessionSerializer, MemberSerializer

logger = logging.getLogger(__name__)


def parse_date(x):
    date = datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ")

    if timezone.is_aware(date):
        return date
    return timezone.make_aware(date)


class CreateAttendanceSession(APIView):
    permission_classes = [IsAdmin | IsApiKey]

    def post(self, request):
        required_fields = ["title", "key", "expires"]
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {"error": f"{field} is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            expires = request.data["expires"]
            try:
                expires = parse_date(expires)
                expires = expires.astimezone(timezone.utc)
            except ValueError:
                return Response(
                    {"detail": "Invalid time format. Please use ISO format (with Z)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            session = AttendanceSession.objects.create(
                title=request.data["title"], key=request.data["key"], expires=expires
            )

            return Response(
                {
                    "session": {
                        "session_id": session.session_id,
                        "title": session.title,
                        "key": session.key,
                        "expires": session.expires,
                    }
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            logger.error(f"ValueError: {e}")
            return Response(
                {"error": "Invalid date or timestamp format"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetAttendanceSessions(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AttendanceSessionSerializer

    def get_queryset(self):
        return AttendanceSession.objects.all()


class GetMemberAttendanceSessions(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AttendanceSessionSerializer

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs["id"])
        # return all session that have userid in attendees
        return AttendanceSession.objects.filter(attendees=user)


class GetSessionAttendees(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = MemberSerializer

    def get_queryset(self):
        session = get_object_or_404(AttendanceSession, session_id=self.kwargs["id"])
        return session.attendees.all()


class AttendSession(generics.CreateAPIView):
    permission_classes = [IsVerified | IsAdmin | IsApiKey]

    def post(self, request):
        session_key = request.data.get("session_key")
        discord_id = request.data.get("discord_id")

        if not session_key or not discord_id:
            return Response(
                {"error": "session_key and discord_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Since we sort by expires and active sesions must have a unique key,
            # the first result is the desired active session.
            session = (
                AttendanceSession.objects.filter(key=session_key)
                .order_by("-expires")
                .first()
            )

            if not session:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if not session.is_active():
                return Response(
                    {"error": "Session has expired"}, status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(discord_id=discord_id)
                # Check if user is already in the session
                if user not in session.attendees.all():
                    session.attendees.add(user)

                    stats, created = AttendanceSessionStats.objects.get_or_create(
                        member=user
                    )
                    with transaction.atomic():
                        stats.sessions_attended += 1
                        stats.last_updated = timezone.now()

                        stats.save()

                    return Response(status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {"error": "User already in session"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except User.DoesNotExist:
                return Response(
                    {"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND
                )

        except AttendanceSession.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


class InjestMessageEventView(generics.CreateAPIView):
    permission_classes = [IsAdmin | IsApiKey]
    _message_buffer = MessageBuffer()

    def post(self, request, *args, **kwargs):
        try:
            discord_id = request.data.get("discord_id")
            channel_id = request.data.get("channel_id")

            if not isinstance(discord_id, int) or not isinstance(channel_id, int):
                return Response(
                    {"error": "invalid message format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            message = Message(discord_id=discord_id, channel_id=channel_id)
            self._message_buffer.add_message(message)

            logger.info("Message added to buffer: %s", message)

            return Response(status=status.HTTP_202_ACCEPTED)

        except pydantic.ValidationError as e:
            logger.error("Invalid message format: %s", e)
            return Response(
                {"error": "invalid message format"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Error processing message: %s", e)
            return Response(
                {"error": "internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetUserStats(APIView):
    permission_classes = [IsVerified | IsApiKey]

    def get(self, request, id):
        user = request.user if not id else get_object_or_404(User, id=id)

        return Response(
            {
                "leetcode": LeetcodeStatsSerializer(
                    LeetcodeStats.objects.get(user=user)
                ).data,
                "github": GitHubStatsSerializer(
                    GitHubStats.objects.get(user=user)
                ).data,
            }
        )


class QueryDiscordMessageStats(generics.ListAPIView):
    permission_classes = [IsAdmin]

    def _aggregate(
        self, messages: List[DiscordMessageStats]
    ) -> Dict[int, dict[str, int]]:
        """member_id -> channel_id (+ total) -> message_count"""

        result = defaultdict(lambda: defaultdict(int))
        for msg in messages:
            result[msg.member_id][str(msg.channel_id)] += msg.message_count
            result[msg.member_id]["total"] += msg.message_count
        return result

    def get(self, request):
        member_ids = request.query_params.getlist("member_id")
        channel_ids = request.query_params.getlist("channel_id")
        member_ids = [int(member_id) for member_id in member_ids]
        channel_ids = [int(channel_id) for channel_id in channel_ids]
        qs = None
        if not member_ids and not channel_ids:
            logger.info("Querying all message stats")
            qs = DiscordMessageStats.objects.all()
        elif member_ids and channel_ids:
            logger.info("Querying message stats for members and channels")
            qs = DiscordMessageStats.objects.filter(
                member_id__in=member_ids, channel_id__in=channel_ids
            )
        elif member_ids:
            logger.info("Querying message stats for members")
            qs = DiscordMessageStats.objects.filter(member_id__in=member_ids)
        elif channel_ids:
            logger.info("Querying message stats for channels %s", channel_ids)
            qs = DiscordMessageStats.objects.filter(channel_id__in=channel_ids)

        # todo: aggregate should return mapping of user_id -> channel_name -> message_count
        # will require either an API call or to save in DB. Either is fine, but for now
        # we are just returning the id.
        aggregated = self._aggregate([metric for metric in qs])

        members = User.objects.filter(id__in=aggregated.keys())
        result = [
            {
                "member": UserSerializer(members.get(id=member_id)).data,
                "stats": {
                    channel_id: count
                    for channel_id, count in stats.items()
                    if channel_id != "total"
                    and int(channel_id) in channel_ids
                    or not channel_ids
                },
            }
            for member_id, stats in aggregated.items()
        ]

        return Response(result, status=status.HTTP_200_OK)


class CohortStatsBase(APIView):
    permission_classes = [IsApiKey]

    def get_user_id_from_discord(self, discord_id):
        if not discord_id:
            return None, "Discord ID is required"

        try:
            user = User.objects.get(discord_id=discord_id)
            return user.id, None
        except User.DoesNotExist:
            return None, "User with discord ID not found"

    def update_stats(self, cohort_stats_object: CohortStats):
        pass

    def put(self, request):
        user_id, error = self.get_user_id_from_discord(request.data.get("discord_id"))

        if error:
            return JsonResponse({"error": error}, status=400)

        cohort_name = request.data.get("cohort_name")

        cohort_stats_queryset = CohortStats.objects.filter(
            member__id=user_id, cohort__is_active=True
        )

        if cohort_name:
            cohort_stats_queryset = cohort_stats_queryset.filter(
                cohort__name=cohort_name
            )
            if not cohort_stats_queryset.exists():
                return JsonResponse(
                    {"error": "Active cohort not found with the provided name"},
                    status=404,
                )

        cohort_stats_objects = list(cohort_stats_queryset)

        if not cohort_stats_objects:
            return JsonResponse(
                {"error": "No active cohort stats found for this user"}, status=404
            )

        updated_cohorts = []
        for stats_obj in cohort_stats_objects:
            self.update_stats(stats_obj)
            logger.info(
                f"{self.__class__.__name__} for {stats_obj.member.username} in cohort {stats_obj.cohort.name}"
            )
            updated_cohorts.append(stats_obj.cohort.name)

        if len(updated_cohorts) > 1:
            msg = f"User {user_id} has multiple active cohorts {updated_cohorts}. Updated all of them, but you might want to look into this."
            logger.warning(msg)
            try:
                send_email(
                    "swecc@uw.edu",
                    "sweccuw@gmail.com",
                    "Multiple active cohorts",
                    f"<p>{msg}</p>",
                )
            except Exception as e:
                logger.error(f"Failed to send email: {e}")

        return Response({"updated_cohorts": updated_cohorts}, status=status.HTTP_200_OK)


class UpdateApplicationStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object):
        cohort_stats_object.applications += 1
        cohort_stats_object.save()


class UpdateOAStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object: CohortStats):
        cohort_stats_object.onlineAssessments += 1
        cohort_stats_object.save()


class UpdateInterviewStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object: CohortStats):
        cohort_stats_object.interviews += 1
        cohort_stats_object.save()


class UpdateOffersStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object):
        cohort_stats_object.offers += 1
        cohort_stats_object.save()


class UpdateDailyChecksView(CohortStatsBase):
    def update_stats(self, cohort_stats_object):
        # 12 AM in PST
        updated_to_the_nearest_day = cohort_stats_object.last_updated.replace(
            hour=7, minute=59, second=59, microsecond=0
        )
        current_day = timezone.now().replace(
            hour=7, minute=59, second=59, microsecond=0
        )

        hour_difference = (
            updated_to_the_nearest_day - current_day
        ).total_seconds() // 3600

        if hour_difference >= 24:
            cohort_stats_object.dailyChecks += 1
            cohort_stats_object.streak = (
                cohort_stats_object.streak + 1 if hour_difference <= 48 else 1
            )
            cohort_stats_object.save()
        else:
            logging.info(
                f"Daily check for cohort {cohort_stats_object.cohort.name} occurred more than once within 24 hours. Skipping update."
            )
