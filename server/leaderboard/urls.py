from django.urls import path
from . import views

urlpatterns = [
    path(
        "leetcode/",
        views.LeetcodeLeaderboardView.as_view(),
        name="leetcode-leaderboard",
    ),
]
