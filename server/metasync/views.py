from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from custom_auth.permissions import IsAdmin
from members.permissions import IsApiKey
from .models import DiscordChannel
from .serializers import DiscordChannelSerializer
import logging

logger = logging.getLogger(__name__)


class DiscordChannelsAntiEntropy(APIView):
    """
    synchronize discord channel data with the database.
    ensures database state exactly matches the provided
    snapshot after execution
    """

    permission_classes = [IsAdmin | IsApiKey]

    def _validate_channel_data(self, channel_data: dict) -> bool:
        logger.info("Validating channel data %s", channel_data)
        required_fields = {
            "channel_id",
            "channel_name",
            "category_id",
            "channel_type",
            "guild_id",
        }

        if not all(field in channel_data for field in required_fields):
            logger.error("Missing required fields in channel data")
            return False

        if not any(
            v == channel_data["channel_type"] for v, _ in DiscordChannel.CHANNEL_TYPES
        ):
            logger.error(
                "Invalid channel type %s, must be one of %s",
                channel_data["channel_type"],
                [v for v, _ in DiscordChannel.CHANNEL_TYPES],
            )
            return False

        for field in ["channel_id", "guild_id"]:
            try:

                if isinstance(channel_data.get(field), str):
                    int(channel_data[field])
                elif not isinstance(channel_data.get(field), int):
                    logger.error(f"Invalid {field} format")
                    return False
            except (ValueError, TypeError):
                logger.error(f"Invalid {field} format")
                return False

        if channel_data.get("category_id") is not None:
            try:
                if isinstance(channel_data["category_id"], str):
                    int(channel_data["category_id"])
                elif not isinstance(channel_data["category_id"], int):
                    logger.error("Invalid category_id format")
                    return False
            except (ValueError, TypeError):
                logger.error("Invalid category_id format")
                return False

        return True

    def _prepare_channel_data(self, channel_data: dict) -> dict:
        prepared_data = {
            "channel_name": channel_data["channel_name"],
            "channel_type": channel_data["channel_type"],
            "guild_id": int(channel_data["guild_id"]),
        }

        category_id = channel_data.get("category_id")
        if category_id is not None and category_id != "":
            prepared_data["category_id"] = int(category_id)
        else:
            prepared_data["category_id"] = None

        return prepared_data

    @transaction.atomic
    def post(self, request: Request) -> Response:
        try:
            channels_updated = request.data
            if not isinstance(channels_updated, list):
                return Response(
                    {"error": "Invalid data format. Expected a list of channels."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for channel in channels_updated:
                if not self._validate_channel_data(channel):
                    return Response(
                        {
                            "error": "Invalid channel data format or missing required fields"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            channel_ids = [int(channel["channel_id"]) for channel in channels_updated]
            if len(channel_ids) != len(set(channel_ids)):
                return Response(
                    {"error": "Duplicate channel IDs found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            desired_state = {
                int(channel["channel_id"]): self._prepare_channel_data(channel)
                for channel in channels_updated
            }

            current_channels = DiscordChannel.objects.all()
            current_state = {
                channel.channel_id: {
                    "channel_name": channel.channel_name,
                    "category_id": channel.category_id,
                    "channel_type": channel.channel_type,
                    "guild_id": channel.guild_id,
                    "instance": channel,
                }
                for channel in current_channels
            }

            current_ids = set(current_state.keys())
            desired_ids = set(desired_state.keys())

            to_delete = current_ids - desired_ids
            to_create = desired_ids - current_ids
            to_check = current_ids & desired_ids

            channels_to_update = []
            channels_to_create = []

            for channel_id in to_create:
                channel_data = desired_state[channel_id]
                channels_to_create.append(
                    DiscordChannel(channel_id=channel_id, **channel_data)
                )

            for channel_id in to_check:
                current = current_state[channel_id]
                desired = desired_state[channel_id]

                if any(current[k] != desired[k] for k in desired.keys()):
                    channel = current["instance"]
                    for key, value in desired.items():
                        setattr(channel, key, value)
                    channels_to_update.append(channel)

            deleted_count = 0
            if to_delete:
                deleted_count, _ = DiscordChannel.objects.filter(
                    channel_id__in=to_delete
                ).delete()

            if channels_to_create:
                DiscordChannel.objects.bulk_create(channels_to_create)

            if channels_to_update:
                DiscordChannel.objects.bulk_update(
                    channels_to_update,
                    ["channel_name", "category_id", "channel_type", "guild_id"],
                )

            return Response(
                {
                    "status": "success",
                    "changes": {
                        "deleted": deleted_count,
                        "created": len(channels_to_create),
                        "updated": len(channels_to_update),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except KeyError as e:
            return Response(
                {"error": f"Missing required field: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as e:
            return Response(
                {"error": f"Invalid ID format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("An unexpected error occurred", exc_info=e)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class DiscordChannelsMetadata(APIView):
    permission_classes = [IsAdmin]

    def get(self, request: Request) -> Response:
        channel_id = request.query_params.get("channel_id", None)
        category_id = request.query_params.get("category_id", None)
        channel_type = request.query_params.get("type", None)
        guild_id = request.query_params.get("guild_id", None)

        channels = DiscordChannel.objects.all()

        if channel_type:
            channels = DiscordChannel.objects.filter(channel_type=channel_type)
        if channel_id:
            channels = DiscordChannel.objects.filter(channel_id=channel_id)
        if category_id:
            channels = DiscordChannel.objects.filter(category_id=category_id)
        if guild_id:
            channels = DiscordChannel.objects.filter(guild_id=guild_id)

        serializer = DiscordChannelSerializer(channels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)