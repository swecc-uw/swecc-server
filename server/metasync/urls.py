from django.urls import path
from . import views

urlpatterns = [
    path(
        "discord/anti-entropy/",
        views.DiscordChannelsAntiEntropy.as_view(),
        name="discord-channels-sync",
    ),
]
