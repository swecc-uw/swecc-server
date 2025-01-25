import pydantic
from collections import defaultdict
from typing import Dict, List
from rest_framework import generics
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from datetime import datetime
import logging
from .serializers import AnnouncementSerializer
from .models import Announcement

class AccouncementList(generics.ListCreateAPIView):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()

class AccouncementCRUDView(RetrieveUpdateDestroyAPIView):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
