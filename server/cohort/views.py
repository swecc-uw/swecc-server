from typing import Dict, List, Optional, Union
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from members.permissions import IsApiKey
from .models import Cohort, CohortStatsData
from .serializers import (
    CohortHydratedPublicSerializer,
    CohortSerializer,
    CohortHydratedSerializer,
)
from members.models import User
from engagement.models import CohortStats
from custom_auth.permissions import IsAdmin


def _get_serializer_class(req):

    is_admin = req.user.groups.filter(name="is_admin").exists()
    is_readonly = req.method == "GET"

    if not is_admin and not is_readonly:
        raise PermissionError("You do not have permission to perform this action")

    if is_readonly:
        return (
            CohortHydratedPublicSerializer if not is_admin else CohortHydratedSerializer
        )

    return CohortSerializer


# When assigning a user to a cohort, make sure to create a `CohortStats` object specific to that user and the cohort they're assigned to
class CohortListCreateView(generics.ListCreateAPIView):
    queryset = Cohort.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return _get_serializer_class(self.request)

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
        return _get_serializer_class(self.request)

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
            member = User.objects.get(pk=member_id)
            CohortStats.objects.get_or_create(cohort=cohort, member=member)

        return response


class CohortStatsView(APIView):
    permission_classes = [IsAuthenticated | IsApiKey]

    def get(self, request):
        """
        - if cohort_id is provided, return stats for specified cohorts
        - if member_id or discord_id is provided, return stats for cohorts where member belongs and has stats
        - only one of cohort_id, member_id, or discord_id can be provided
        - if include_profiles is true, include cohort profiles in the response
        """
        try:
            cohort_ids, member_id = self.parse_ids(request.query_params)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        include_profiles = (
            request.query_params.get("include_profiles", "").lower() == "true"
        )

        stats_queryset = self.get_queryset(cohort_ids, member_id)

        if member_id:
            cohort_ids = stats_queryset.values_list("cohort_id", flat=True).distinct()
            cohorts = self.get_cohorts(cohort_ids, member_id=member_id)
        else:
            cohorts = self.get_cohorts(cohort_ids)

        cohort_serializer = (
            _get_serializer_class(request) if include_profiles else CohortSerializer
        )

        response = []
        for cohort in cohorts:
            stats = self.aggregate_stats(stats_queryset, cohort.id)
            response.append(
                {
                    "stats": stats.to_dict(),
                    "cohort": cohort_serializer(cohort).data,
                }
            )

        return Response(response)

    def get_member_id_from_discord_id(self, discord_id: str) -> Optional[int]:
        try:
            user = User.objects.get(discord_id=discord_id)
            return user.id
        except ObjectDoesNotExist:
            return None
        except ValueError:
            raise ValueError("Invalid discord_id format")

    def get_queryset(
        self, cohort_ids: Optional[List[int]] = None, member_id: Optional[int] = None
    ):

        queryset = CohortStats.objects.all()

        if member_id:
            member_cohort_ids = Cohort.objects.filter(
                members__id=member_id
            ).values_list("id", flat=True)

            queryset = queryset.filter(
                member_id=member_id, cohort_id__in=member_cohort_ids
            )
        elif cohort_ids:
            queryset = queryset.filter(cohort_id__in=cohort_ids)

        return queryset

    def aggregate_stats(self, queryset, cohort_id: int) -> CohortStatsData:
        stats = queryset.filter(cohort_id=cohort_id).aggregate(
            Sum("applications"),
            Sum("onlineAssessments"),
            Sum("interviews"),
            Sum("offers"),
            Sum("dailyChecks"),
        )
        return CohortStatsData.from_db_values(stats)

    def get_cohorts(
        self, cohort_ids: Optional[List[int]] = None, member_id: Optional[int] = None
    ):
        queryset = Cohort.objects.all()

        if member_id:
            queryset = queryset.filter(members__id=member_id)

        if cohort_ids:
            queryset = queryset.filter(id__in=cohort_ids)

        return queryset

    def parse_ids(self, params: dict) -> tuple[Optional[List[int]], Optional[int]]:
        cohort_ids = params.getlist("cohort_id", [])
        member_id = params.get("member_id")
        discord_id = params.get("discord_id")

        if sum(bool(x) for x in (cohort_ids, member_id, discord_id)) > 1:
            raise ValueError(
                "Only one of 'cohort_id', 'discord_id', or 'member_id' can be provided"
            )

        try:
            if cohort_ids:
                return [int(cid) for cid in cohort_ids], None
            if member_id:
                return None, int(member_id)
            if discord_id:
                member_id = self.get_member_id_from_discord_id(discord_id)
                if member_id is None:
                    raise ValueError(f"No user found with discord_id: {discord_id}")
                return None, member_id
            return None, None
        except ValueError as e:
            if str(e).startswith("No user found"):
                raise
            raise ValueError("Invalid ID format provided")


class CohortRemoveMemberView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        """
        - Remove a member from a cohort
        - Remove stats for that member from the cohort
        """
        try:
            member_id = request.data.get("member_id")
            cohort_id = request.data.get("cohort_id")
        except KeyError:
            return Response(
                {"error": "Please provide both 'member_id' and 'cohort_id'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            member = User.objects.get(pk=member_id)
        except User.DoesNotExist:
            return Response(
                {"error": f"No user found with id: {member_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            cohort = Cohort.objects.get(pk=cohort_id)
        except Cohort.DoesNotExist:
            return Response(
                {"error": f"No cohort found with id: {cohort_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cohort.members.remove(member)
        CohortStats.objects.filter(member=member, cohort=cohort).delete()

        return Response(
            {"message": f"Member {member_id} removed from cohort {cohort_id}"},
            status=status.HTTP_200_OK,
        )


class CohortTransferView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        """
        - Transfer a member from one cohort to another
        - Update stats for that member accordingly
        """
        try:
            member_id = request.data.get("member_id")
            from_cohort_id = request.data.get("from_cohort_id")
            to_cohort_id = request.data.get("to_cohort_id")
        except KeyError:
            return Response(
                {
                    "error": "Please provide 'member_id', 'from_cohort_id', and 'to_cohort_id'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            member = User.objects.get(pk=member_id)
        except User.DoesNotExist:
            return Response(
                {"error": f"No user found with id: {member_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            from_cohort = Cohort.objects.get(pk=from_cohort_id)
        except Cohort.DoesNotExist:
            return Response(
                {"error": f"No cohort found with id: {from_cohort_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            to_cohort = Cohort.objects.get(pk=to_cohort_id)
        except Cohort.DoesNotExist:
            return Response(
                {"error": f"No cohort found with id: {to_cohort_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from_cohort.members.remove(member)
        to_cohort.members.add(member)

        associated_cohort_stats = CohortStats.objects.filter(
            member=member, cohort=from_cohort
        ).first()
        associated_cohort_stats.cohort = to_cohort
        associated_cohort_stats.save()

        return Response(
            {
                "message": f"Member {member_id} transferred from cohort {from_cohort_id} to cohort {to_cohort_id}"
            },
            status=status.HTTP_200_OK,
        )
