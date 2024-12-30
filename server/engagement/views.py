import pydantic
from collections import defaultdict
from typing import Dict, List
from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
import logging
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from custom_auth.permissions import IsAdmin, IsVerified
from members.permissions import IsApiKey
from members.models import User
from .buffer import MessageBuffer, Message
from .models import AttendanceSession, DiscordMessageStats
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
        qs = None
        if not member_ids and not channel_ids:
            qs = DiscordMessageStats.objects.all()
        elif member_ids and channel_ids:
            qs = DiscordMessageStats.objects.filter(
                member_id__in=member_ids, channel_id__in=channel_ids
            )
        elif member_ids:
            qs = DiscordMessageStats.objects.filter(member_id__in=member_ids)
        elif channel_ids:
            qs = DiscordMessageStats.objects.filter(channel_id__in=channel_ids)

        # todo: aggregate should return mapping of user_id -> channel_name -> message_count
        # will require either an API call or to save in DB. Either is fine, but for now
        # we are just returning the id.
        aggregated = self._aggregate([metric for metric in qs])
        return Response(aggregated, status=status.HTTP_200_OK)
