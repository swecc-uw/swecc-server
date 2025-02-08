from django.urls import path
from . import views

urlpatterns = [
    path("", views.CohortListCreateView.as_view(), name="cohort-list-create"),
    path(
        "<int:pk>/",
        views.CohortRetrieveUpdateDestroyView.as_view(),
        name="cohort-detail",
    ),
    path(
        "oa/<int:amt>",
        view=views.UpdateOAStatsView.as_view(),
        name="cohort-update-oa-stats",
    ),
    path(
        "apply/<int:amt>",
        view=views.UpdateApplicationStatsView.as_view(),
        name="cohort-update-application-stats",
    ),
    path(
        "interview/<int:amt>",
        view=views.UpdateInterviewStatsView.as_view(),
        name="cohort-update-interview-stats",
    ),
    path(
        "offer/<int:amt>",
        view=views.UpdateOffersStatsView.as_view(),
        name="cohort-update-offer-stats",
    ),
    path(
        "dailycheck",
        view=views.UpdateDailyChecksView.as_view(),
        name="cohort-update-daily-check",
    ),
]
