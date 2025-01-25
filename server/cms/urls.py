from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .views import AccouncementCRUDView, AccouncementList, CreateAnnouncement

urlpatterns = [
    path("admin/", admin.site.urls),
    path("announcements/", AccouncementList.as_view()),
    path("announcement/", CreateAnnouncement.as_view()),
]
