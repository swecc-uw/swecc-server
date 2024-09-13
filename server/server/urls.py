from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .settings import DEBUG

urlpatterns = [
    path('auth/', include('custom_auth.urls')),
    path('questions/', include("questions.urls")),
    path('members/', include("members.urls")),
    path('interview/', include("interview.urls")),
    path('directory/', include('directory.urls')),
]

if DEBUG:
    import logging
    logger = logging.getLogger(__name__)

    @api_view(['GET'])
    def health_check(request):
        logger.info("Health check")
        return Response({'status': 'ok'})

    urlpatterns.append(path('health/', health_check))
