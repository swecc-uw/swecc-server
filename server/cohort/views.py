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


class CohortStatsBase(APIView):
    permission_classes = [IsApiKey]

    def get_user_id_from_discord(self, discord_id):
        if not discord_id:
            return None, "Discord ID is required"

        try:
            user = User.objects.get(discord_id=discord_id)
            return user.id, None
        except User.DoesNotExist:
            return None, "User with discord ID not found"

    def update_stats(self, cohort_stats_object: CohortStats, amount):
        pass

    def put(self, request, amt):

        try:
            amt = int(amt)
        except ValueError:
            return JsonResponse(
                {"error": "Invalid amount, must be an integer"}, status=400
            )

        user_id, error = self.get_user_id_from_discord(request.data.get("discord_id"))

        if error:
            return JsonResponse({"error": error}, status=400)

        try:
            cohort_stats_object = CohortStats.objects.get(member__id=user_id)
        except CohortStats.DoesNotExist:
            return JsonResponse(
                {"error": "Cohort stats object doesn't exist for this user"}, status=404
            )

        self.update_stats(cohort_stats_object, amt)
        cohort_stats_object.save()

        serializer = CohortStatsSerializer(cohort_stats_object)

        return Response({"cohort_stats": serializer.data}, status=status.HTTP_200_OK)


class UpdateApplicationStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object, amount):
        cohort_stats_object.applications += amount


class UpdateOAStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object: CohortStats, amount):
        cohort_stats_object.onlineAssessments += amount


class UpdateInterviewStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object: CohortStats, amount):
        cohort_stats_object.interviews += amount


class UpdateOffersStatsView(CohortStatsBase):
    def update_stats(self, cohort_stats_object, amount):
        cohort_stats_object.offers += amount


class UpdateDailyChecksView(CohortStatsBase):
    def update_stats(self, cohort_stats_object, amount):
        cohort_stats_object.dailyChecks += amount

    def put(self, request):
        return super().put(request, 1)
