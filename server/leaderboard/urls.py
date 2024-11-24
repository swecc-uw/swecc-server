from django.urls import path
from . import views

urlpatterns = [
    path(
        "leetcode/",
        views.LeetcodeLeaderboardView.as_view(),
        name="leetcode-leaderboard",
    ),
    path("github/", views.GitHubLeaderboardView.as_view(), name="github-leaderboard"),
]
