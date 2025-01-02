from django.urls import path
from . import views

urlpatterns = [
    path(
        "leetcode/",
        views.LeetcodeLeaderboardView.as_view(),
        name="leetcode-leaderboard",
    ),
    path("github/", views.GitHubLeaderboardView.as_view(), name="github-leaderboard"),
    path(
        "internship/",
        views.InternshipApplicationLeaderboardView.as_view(),
        name="internship-leaderboard",
    ),
    path(
        "newgrad/",
        views.NewGradApplicationLeaderboardView.as_view(),
        name="newgrad-leaderboard",
    ),
    path(
        "events/process/",
        views.InjestReactionEventView.as_view(),
        name="process-events",
    ),
    path(
        "attendance/",
        views.AttendanceSessionLeaderboard.as_view(),
        name="attendance-leaderboard",
    ),
]
