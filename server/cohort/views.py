from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from custom_auth.permissions import IsAdmin
from .models import Cohort
from .serializers import (
    CohortHydratedPublicSerializer,
    CohortSerializer,
    CohortHydratedSerializer,
)
from members.models import User
from engagement.models import CohortStats


# When assigning a user to a cohort, make sure to create a `CohortStats` object specific to that user and the cohort they're assigned to
class CohortListCreateView(generics.ListCreateAPIView):
    queryset = Cohort.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        is_admin = self.request.user.groups.filter(name="is_admin").exists()
        is_readonly = self.request.method == "GET"

        if not is_admin and not is_readonly:
            raise PermissionError("You do not have permission to perform this action")

        if is_readonly:
            return (
                CohortHydratedPublicSerializer
                if not is_admin
                else CohortHydratedSerializer
            )

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
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        is_admin = self.request.user.groups.filter(name="is_admin").exists()
        is_readonly = self.request.method == "GET"

        if not is_admin and not is_readonly:
            raise PermissionError("You do not have permission to perform this action")

        if self.request.method == "GET":
            return (
                CohortHydratedPublicSerializer
                if not is_admin
                else CohortHydratedSerializer
            )

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
