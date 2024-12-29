from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .views import ManagementCommandView

urlpatterns = [
    path('auth/', include('custom_auth.urls')),
    path('questions/', include("questions.urls")),
    path('members/', include("members.urls")),
    path('interview/', include("interview.urls")),
    path('directory/', include('directory.urls')),
    path('reports/', include('report.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('engagement/', include('engagement.urls')),
    path('admin/command/', ManagementCommandView.as_view()),
]


import logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    logger.info("Health check")
    return Response({'status': 'ok'})

urlpatterns.append(path('health/', health_check))

# from django.contrib import admin
# admin.autodiscover()

# urlpatterns.append(path('admin/', admin.site.urls))