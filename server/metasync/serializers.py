from rest_framework import serializers

from .models import DiscordChannel


class DiscordChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordChannel
        fields = "__all__"
