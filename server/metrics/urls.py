from django.urls import path
from . import views

urlpatterns = [
    path(
        "all/",
        views.MetricViewAllRecent.as_view(),
        name="metrics-view-all-recent",
    ),
]