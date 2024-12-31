from django.urls import path
from . import views

urlpatterns = [
    path(
        "discord/anti-entropy/",
        views.DiscordChannelsAntiEntropy.as_view(),
        name="discord-channels-sync",
    ),
    path(
        "discord/",
        views.DiscordChannelsMetadata.as_view(),
        name="discord-channels-metadata",
    ),
]
