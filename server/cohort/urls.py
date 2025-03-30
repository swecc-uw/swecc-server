from django.urls import path

from . import views

urlpatterns = [
    path("", views.CohortListCreateView.as_view(), name="cohort-list-create"),
    path(
        "<int:pk>/",
        views.CohortRetrieveUpdateDestroyView.as_view(),
        name="cohort-detail",
    ),
    path("stats/", views.CohortStatsView.as_view(), name="cohort-stats-list"),
    path("dashboard/", views.CohortDashboardView.as_view(), name="cohort-dashboard"),
    path(
        "remove/", views.CohortRemoveMemberView.as_view(), name="cohort-remove-member"
    ),
    path("transfer/", views.CohortTransferView.as_view(), name="cohort-transfer"),
]
