from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from django.http import Http404
from django.db import transaction
from django.db.models import F
from engagement.models import DiscordMessageStats
from members.models import User
from members.permissions import IsApiKey

import logging

logger = logging.getLogger(__name__)


class InjestMessageEventView(generics.CreateAPIView):
    permission_classes = [IsApiKey]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        channel_id = request.data.get("channel_id")
        try:
            user = get_object_or_404(User, discord_id=discord_id)

            (
                stats,
                created,
            ) = DiscordMessageStats.objects.select_for_update().get_or_create(
                member_id=user.id, channel_id=channel_id, defaults={"message_count": 1}
            )

            if not created:
                stats.message_count = F("message_count") + 1
                stats.save()
                stats.refresh_from_db()

            logger.info(
                "member %s has %d messages in channel %s",
                user.id,
                stats.message_count,
                channel_id,
            )

            return Response(status=status.HTTP_202_ACCEPTED)

        except Http404:
            logger.error("member not found for discord_id: %s", discord_id)
            return Response(
                {"error": "member not found"}, status=status.HTTP_404_NOT_FOUND
            )
