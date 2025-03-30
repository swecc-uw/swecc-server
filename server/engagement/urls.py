from django.urls import path

from . import views

urlpatterns = [
    path(
        "message/",
        views.InjestMessageEventView.as_view(),
        name="injest-message-event",
    ),
    path(
        "message/query/",
        views.QueryDiscordMessageStats.as_view(),
        name="query-discord-message-stats",
    ),
    path(
        "attendance/session",
        views.CreateAttendanceSession.as_view(),
        name="create-attendance-session",
    ),
    path(
        "attendance/",
        views.GetAttendanceSessions.as_view(),
        name="get-attendance-sessions",
    ),
    path(
        "attendance/member/<int:id>/",
        views.GetMemberAttendanceSessions.as_view(),
        name="get-member-attendance-sessions",
    ),
    path(
        "attendance/session/<int:id>/",
        views.GetSessionAttendees.as_view(),
        name="get-session-attendees",
    ),
    path("attendance/attend", views.AttendSession.as_view(), name="attend-session"),
    path(
        "cohort/oa",
        view=views.UpdateOAStatsView.as_view(),
        name="cohort-update-oa-stats",
    ),
    path(
        "cohort/apply",
        view=views.UpdateApplicationStatsView.as_view(),
        name="cohort-update-application-stats",
    ),
    path(
        "cohort/interview",
        view=views.UpdateInterviewStatsView.as_view(),
        name="cohort-update-interview-stats",
    ),
    path(
        "cohort/offer",
        view=views.UpdateOffersStatsView.as_view(),
        name="cohort-update-offer-stats",
    ),
    path(
        "cohort/dailycheck",
        view=views.UpdateDailyChecksView.as_view(),
        name="cohort-update-daily-check",
    ),
    path(
        "user/<int:id>/",
        views.GetUserStats.as_view(),
        name="get-user-stats",
    ),
]
