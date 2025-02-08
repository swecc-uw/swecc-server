from rest_framework import generics
from .models import Cohort
from .serializers import CohortSerializer, CohortHydratedSerializer


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
