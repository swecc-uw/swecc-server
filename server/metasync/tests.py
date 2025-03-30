from django.test import TestCase
from django.urls import reverse
from rest_framework_api_key.models import APIKey
from rest_framework.test import APITestCase
from rest_framework import status
from .models import DiscordChannel


class DiscordChannelsFuzzedTests(APITestCase):
    def setUp(self):
        api_key, key = APIKey.objects.create_key(name="swecc-bot")
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {key}")
        self.url = reverse("discord-channels-sync")

        self.initial_channels = [
            {
                "channel_id": "123456789",
                "channel_name": "general",
                "category_id": "111111111",
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
            {
                "channel_id": "987654321",
                "channel_name": "voice-chat",
                "category_id": "111111111",
                "channel_type": "VOICE",
                "guild_id": "999999999",
            },
            {
                "channel_id": "456789123",
                "channel_name": "announcements",
                "category_id": "222222222",
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
            {
                "channel_id": "789123456",
                "channel_name": "gaming",
                "category_id": "333333333",
                "channel_type": "VOICE",
                "guild_id": "999999999",
            },
            {
                "channel_id": "321654987",
                "channel_name": "help-forum",
                "category_id": "444444444",
                "channel_type": "FORUM",
                "guild_id": "999999999",
            },
        ]

        for channel_data in self.initial_channels:
            DiscordChannel.objects.create(**channel_data)

    def test_complex_sync_operation(self):
        updated_channels = [
            # keep one channel unchanged
            self.initial_channels[0],
            # update channel name and type
            {
                "channel_id": "987654321",
                "channel_name": "voice-lounge",  # changed
                "category_id": "111111111",
                "channel_type": "STAGE",  # changed
                "guild_id": "999999999",
            },
            # update channel category
            {
                "channel_id": "456789123",
                "channel_name": "announcements",
                "category_id": "111111111",  # changed
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
            # add new channels
            {
                "channel_id": "111222333",
                "channel_name": "new-text",
                "category_id": "222222222",
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
            {
                "channel_id": "444555666",
                "channel_name": "new-voice",
                "category_id": "333333333",
                "channel_type": "VOICE",
                "guild_id": "999999999",
            },
            {
                "channel_id": "777888999",
                "channel_name": "new-forum",
                "category_id": "444444444",
                "channel_type": "FORUM",
                "guild_id": "999999999",
            },
        ]
        # 'gaming' and 'help-forum' will be deleted

        response = self.client.post(self.url, updated_channels, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        changes = response.json()["changes"]
        self.assertEqual(changes["created"], 3)  # 3 new channels
        self.assertEqual(changes["updated"], 2)  # 2 modified channels
        self.assertEqual(changes["deleted"], 2)  # 2 deleted channels

        self.assertEqual(DiscordChannel.objects.count(), 6)

        voice_channel = DiscordChannel.objects.get(channel_id="987654321")
        self.assertEqual(voice_channel.channel_type, "STAGE")
        self.assertEqual(voice_channel.channel_name, "voice-lounge")

        moved_channel = DiscordChannel.objects.get(channel_id="456789123")
        self.assertEqual(moved_channel.category_id, 111111111)

        self.assertFalse(DiscordChannel.objects.filter(channel_id="789123456").exists())
        self.assertFalse(DiscordChannel.objects.filter(channel_id="321654987").exists())

        new_channels = DiscordChannel.objects.filter(
            channel_id__in=["111222333", "444555666", "777888999"]
        )
        self.assertEqual(new_channels.count(), 3)

    def test_idempotency(self):
        response1 = self.client.post(self.url, self.initial_channels, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        changes1 = response1.json()["changes"]
        self.assertEqual(changes1["created"], 0)
        self.assertEqual(changes1["updated"], 0)
        self.assertEqual(changes1["deleted"], 0)

        response2 = self.client.post(self.url, self.initial_channels, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        changes2 = response2.json()["changes"]
        self.assertEqual(changes2["created"], 0)
        self.assertEqual(changes2["updated"], 0)
        self.assertEqual(changes2["deleted"], 0)

    def test_edge_cases(self):
        """Test various edge cases in a single sync operation"""
        edge_case_channels = [
            {
                "channel_id": "111111111",
                "channel_name": "x" * 100,
                "category_id": "111111111",
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
            # channel with same category and name as another
            {
                "channel_id": "222222222",
                "channel_name": "general",  # same name as existing channel
                "category_id": "111111111",  # same category as existing channel
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
            {
                "channel_id": "333333333",
                "channel_name": "a",
                "category_id": "111111111",
                "channel_type": "TEXT",
                "guild_id": "999999999",
            },
        ]

        response = self.client.post(self.url, edge_case_channels, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            DiscordChannel.objects.filter(
                channel_id__in=["111111111", "222222222", "333333333"]
            ).count(),
            3,
        )

    def test_invalid_cases(self):
        """Test various invalid cases"""

        invalid_channels = [
            # missing channel_type
            {
                "channel_id": "111111111",
                "channel_name": "test",
                "category_id": "111111111",
                "guild_id": "999999999",
            },
            # missing both category_id and guild_id
            {
                "channel_id": "222222222",
                "channel_name": "test2",
                "channel_type": "TEXT",
            },
        ]
        response = self.client.post(self.url, invalid_channels, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_type_channels = self.initial_channels + [
            {
                "channel_id": "111111111",
                "channel_name": "test",
                "category_id": "111111111",
                "channel_type": "INVALID_TYPE",
                "guild_id": "999999999",
            }
        ]
        response = self.client.post(self.url, invalid_type_channels, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # no changes were made during invalid requests
        self.assertEqual(DiscordChannel.objects.count(), len(self.initial_channels))
