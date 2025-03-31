from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.GetChronosHealth.as_view(), name="chronos-health"),
    path(
        "containers/",
        views.GetAllContainerStatus.as_view(),
        name="container-status",
    ),
    path(
        "containers/<container_name>/",
        views.GetContainerMetadata.as_view(),
        name="container-metadata",
    ),
    path(
        "live/",
        views.GetRunningContainer.as_view(),
        name="container-running",
    ),
    path(
        "usage/<container_name>/",
        views.GetContainerRecentUsage.as_view(),
        name="container-usage-recent",
    ),
    path(
        "usage/<container_name>/all/",
        views.GetContainerUsageHistory.as_view(),
        name="container-usage-history",
    ),
    path(
        "all/",
        views.MetricViewAllRecent.as_view(),
        name="metrics-view-all-recent",
    ),
    path(
        "task/disable/", views.DisableMetricTask.as_view(), name="disable-metrics-poll"
    ),
    path("task/enable/", views.EnableMetricTask.as_view(), name="enable-metrics-poll"),
    path(
        "task/<job_id>/",
        views.GetMetricTaskStatus.as_view(),
        name="metrics-poll-status",
    ),
    path(
        "collect-stat/",
        views.GetMetricCollectionStatus.as_view(),
        name="metrics-collection-status",
    ),
    path(
        "collect/",
        views.EnableMetricCollection.as_view(),
        name="enable-metrics-collection",
    ),
    path(
        "dis-collect/",
        views.DisableMetricCollection.as_view(),
        name="disable-metrics-collection",
    ),
]
