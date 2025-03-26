from typing import Dict, List, Optional, Union
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Max
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from members.permissions import IsApiKey
from .models import Cohort, CohortStatsData
from .serializers import (
    CohortPublicSerializer,
    CohortSerializer,
    CohortHydratedPublicSerializer,
    CohortHydratedSerializer,
)
from members.models import User
from engagement.models import CohortStats
from custom_auth.permissions import IsAdmin


def _get_serializer_class(req):

    is_admin = req.user.groups.filter(name="is_admin").exists()
    is_readonly = req.method == "GET"
    include_profiles = req.query_params.get("include_profiles", True)

    if not is_admin and not is_readonly:
        raise PermissionError("You do not have permission to perform this action")

    if not include_profiles:
        return (
            CohortPublicSerializer if not is_admin else CohortSerializer
        )

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
        """
        try:
            cohort_ids, member_id = self.parse_ids(request.query_params)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if member_id:
            cohorts = self.get_cohorts(None, member_id)
            cohort_ids = [cohort.id for cohort in cohorts]
            stats_queryset = CohortStats.objects.filter(
                member_id=member_id, cohort_id__in=cohort_ids
            )
        else:
            cohorts = self.get_cohorts(cohort_ids)
            stats_queryset = CohortStats.objects.filter(
                cohort_id__in=[cohort.id for cohort in cohorts]
            )

        stats_by_cohort = stats_queryset.values('cohort_id').annotate(
            total_applications=Sum('applications'),
            total_onlineAssessments=Sum('onlineAssessments'),
            total_interviews=Sum('interviews'),
            total_offers=Sum('offers'),
            total_dailyChecks=Sum('dailyChecks'),
            max_streak=Max('streak')
        )

        stats_dict = {item['cohort_id']: item for item in stats_by_cohort}

        response = []
        for cohort in cohorts:
            stats = stats_dict.get(cohort.id, {})
            aggregate_stats = CohortStatsData(
                applications=stats.get('total_applications', 0),
                online_assessments=stats.get('total_onlineAssessments', 0),
                interviews=stats.get('total_interviews', 0),
                offers=stats.get('total_offers', 0),
                daily_checks=stats.get('total_dailyChecks', 0),
                streak=stats.get('max_streak', 0)
            )

            cohort_data = {
                "stats": aggregate_stats.to_dict(),
                "cohort": CohortSerializer(cohort).data,
            }
            response.append(cohort_data)

        return Response(response)

    def get_member_id_from_discord_id(self, discord_id: str) -> Optional[int]:
        try:
            user = User.objects.get(discord_id=discord_id)
            return user.id
        except ObjectDoesNotExist:
            return None
        except ValueError:
            raise ValueError("Invalid discord_id format")

    def get_cohorts(
        self, cohort_ids: Optional[List[int]] = None, member_id: Optional[int] = None
    ):
        queryset = Cohort.objects.all()

        if member_id:
            queryset = queryset.filter(members__id=member_id)

        if cohort_ids:
            queryset = queryset.filter(id__in=cohort_ids)

        return queryset.select_related().prefetch_related('members')

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
