from rest_framework import generics
from .models import Cohort
from .serializers import (
    CohortSerializer,
    CohortHydratedSerializer,
    CohortStatsSerializer,
)
from rest_framework.views import APIView
from members.permissions import IsApiKey
from django.http import JsonResponse
from members.models import User
from .models import CohortStats
from rest_framework.response import Response
from rest_framework import status


# When assigning a user to a cohort, make sure to create a `CohortStats` object specific to that user and the cohort they're assigned to
class CohortListCreateView(generics.ListCreateAPIView):
    queryset = Cohort.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CohortHydratedSerializer
        return CohortSerializer


class CohortRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cohort.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CohortHydratedSerializer
        return CohortSerializer
