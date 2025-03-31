import logging

from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .settings import DJANGO_DEBUG
from .views import ManagementCommandView

logger = logging.getLogger(__name__)

urlpatterns = [
    path("auth/", include("custom_auth.urls")),
    path("questions/", include("questions.urls")),
    path("members/", include("members.urls")),
    path("interview/", include("interview.urls")),
    path("directory/", include("directory.urls")),
    path("reports/", include("report.urls")),
    path("leaderboard/", include("leaderboard.urls")),
    path("engagement/", include("engagement.urls")),
    path("admin/command/", ManagementCommandView.as_view()),
    path("engagement/", include("engagement.urls")),
    path("metasync/", include("metasync.urls")),
    path("metrics/", include("metrics.urls")),
    path("cohorts/", include("cohort.urls")),
    path("resume/", include("resume_review.urls")),
]

if DJANGO_DEBUG:
    logger.info("DEBUG is enabled, adding debug urls")
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]


@api_view(["GET"])
def health_check(request):
    logger.info("Health check")
    return Response({"status": "ok"})


urlpatterns.append(path("health/", health_check))

# from django.contrib import admin
# admin.autodiscover()

# urlpatterns.append(path('admin/', admin.site.urls))
