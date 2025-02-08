from rest_framework import generics
from .models import Cohort
from .serializers import (
    CohortSerializer,
    CohortHydratedSerializer,
)
from members.models import User
from engagement.models import CohortStats


# When assigning a user to a cohort, make sure to create a `CohortStats` object specific to that user and the cohort they're assigned to
class CohortListCreateView(generics.ListCreateAPIView):
    queryset = Cohort.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CohortHydratedSerializer
        return CohortSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if not response.status_code == 201:
            return response

        # Create cohort stats for each member when cohort is created
        member_ids = request.data.get("members", [])
        for member_id in member_ids:
            member = User.objects.get(pk=member_id)
            cohort = Cohort.objects.get(name=request.data.get("name"))
            CohortStats.objects.get_or_create(cohort=cohort, member=member)

        return response


class CohortRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cohort.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CohortHydratedSerializer
        return CohortSerializer

    def put(self, request, *args, **kwargs):

        response = super().put(request, *args, **kwargs)
        if not response.status_code == 200:
            return response

        member_ids = request.data.get("members", [])
        cohort = Cohort.objects.get(name=request.data.get("name"))
        past_member_ids = cohort.members.values_list("id", flat=True)

        # Update cohort stats for each member accordingly
        # Not deleting old stats since users can use those stats to benchmark progress
        for member_id in member_ids:
            if member_id not in past_member_ids:
                member = User.objects.get(pk=member_id)
                CohortStats.objects.get_or_create(cohort=cohort, member=member)

        return response
