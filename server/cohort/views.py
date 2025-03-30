from typing import Dict, List, Optional, Union

from custom_auth.permissions import IsAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Exists, IntegerField, Max, OuterRef, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from engagement.models import CohortStats
from members.models import User
from members.permissions import IsApiKey
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cohort, CohortStatsData
from .queries import COHORT_DASHBOARD_QUERY
from .serializers import (
    CohortHydratedPublicSerializer,
    CohortHydratedSerializer,
    CohortNoMembersSerializer,
    CohortSerializer,
)


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
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return _get_serializer_class(self.request)

    def get_queryset(self):
        return Cohort.objects.prefetch_related(
            Prefetch(
                "members",
                queryset=User.objects.prefetch_related("groups", "user_permissions"),
            ),
        ).all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        is_admin = request.user.groups.filter(name="is_admin").exists()
        serializer = (
            CohortHydratedSerializer if is_admin else CohortHydratedPublicSerializer
        )

        return Response(
            serializer(queryset, many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if not response.status_code == 201:
            return response

        member_ids = request.data.get("members", [])
        cohort_name = request.data.get("name")
        members = User.objects.filter(pk__in=member_ids)

        cohort = Cohort.objects.get(name=cohort_name)

        cohort_stats_objects = [
            CohortStats(cohort=cohort, member=member) for member in members
        ]

        CohortStats.objects.bulk_create(cohort_stats_objects, ignore_conflicts=True)

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

        cohorts = self.get_cohorts(cohort_ids, member_id)

        if not cohorts:
            return Response([])

        target_cohort_ids = [cohort.id for cohort in cohorts]

        all_stats = self.get_all_cohort_stats(target_cohort_ids, member_id)

        response = []
        for cohort in cohorts:
            if cohort.id in all_stats:
                cohort_data = {
                    "stats": all_stats[cohort.id],
                    "cohort": CohortNoMembersSerializer(cohort).data,
                }
                response.append(cohort_data)

        return Response(response)

    def get_member_id_from_discord_id(self, discord_id: str) -> Optional[int]:
        try:
            return (
                User.objects.filter(discord_id=discord_id)
                .values_list("id", flat=True)
                .first()
            )
        except ValueError:
            raise ValueError("Invalid discord_id format")

    def get_all_cohort_stats(self, cohort_ids, member_id=None):
        queryset = CohortStats.objects.filter(cohort_id__in=cohort_ids)

        if member_id is not None:
            queryset = queryset.filter(member_id=member_id)

        stats = queryset.values("cohort_id").annotate(
            applications_sum=Coalesce(
                Sum("applications"), Value(0), output_field=IntegerField()
            ),
            online_assessments_sum=Coalesce(
                Sum("onlineAssessments"), Value(0), output_field=IntegerField()
            ),
            interviews_sum=Coalesce(
                Sum("interviews"), Value(0), output_field=IntegerField()
            ),
            offers_sum=Coalesce(Sum("offers"), Value(0), output_field=IntegerField()),
            daily_checks_sum=Coalesce(
                Sum("dailyChecks"), Value(0), output_field=IntegerField()
            ),
            streak_max=Coalesce(Max("streak"), Value(0), output_field=IntegerField()),
        )

        result = {}
        for stat in stats:
            cohort_id = stat["cohort_id"]
            after = CohortStatsData.from_db_values(stat).to_dict()
            result[cohort_id] = after

        return result

    def get_cohorts(self, cohort_ids=None, member_id=None):
        queryset = Cohort.objects.all().order_by("name")

        if member_id is not None:
            queryset = queryset.filter(members__id=member_id)

        if cohort_ids:
            queryset = queryset.filter(id__in=cohort_ids)

        return queryset.only("id", "name", "level")

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
            if member_id is not None:
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


class CohortDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        with connection.cursor() as cursor:
            cursor.execute(COHORT_DASHBOARD_QUERY, [user.id])

            rows = cursor.fetchall()

        user_cohorts = []
        aggregate_stats = None

        columns = [col[0] for col in cursor.description]

        for row in rows:
            row_dict = dict(zip(columns, row))

            if row_dict["type"] == "user_cohorts":
                user_cohorts.append(
                    {
                        "id": row_dict["cohort_id"],
                        "name": row_dict["name"],
                        "level": row_dict["level"],
                        "stats": {
                            "applications": row_dict["applications"] or 0,
                            "onlineAssessments": row_dict["onlineAssessments"] or 0,
                            "interviews": row_dict["interviews"] or 0,
                            "offers": row_dict["offers"] or 0,
                            "dailyChecks": row_dict["dailyChecks"] or 0,
                            "streak": row_dict["streak"] or 0,
                        },
                    }
                )
            else:
                aggregate_stats = row_dict

        response_data = {
            "your_cohorts": user_cohorts,
            "cohorts_aggregated_stats_total": {
                "applications": aggregate_stats.get("applications_sum", 0),
                "onlineAssessments": aggregate_stats.get("online_assessments_sum", 0),
                "interviews": aggregate_stats.get("interviews_sum", 0),
                "offers": aggregate_stats.get("offers_sum", 0),
                "dailyChecks": aggregate_stats.get("daily_checks_sum", 0),
                "streak": aggregate_stats.get("streak_sum", 0),
            },
            "cohorts_aggregated_stats_max": {
                "applications": aggregate_stats.get("applications_max", 0),
                "onlineAssessments": aggregate_stats.get("online_assessments_max", 0),
                "interviews": aggregate_stats.get("interviews_max", 0),
                "offers": aggregate_stats.get("offers_max", 0),
                "dailyChecks": aggregate_stats.get("daily_checks_max", 0),
                "streak": aggregate_stats.get("streak_max", 0),
            },
            "cohorts_aggregated_stats_avg": {
                "applications": aggregate_stats.get("applications_avg", 0),
                "onlineAssessments": aggregate_stats.get("online_assessments_avg", 0),
                "interviews": aggregate_stats.get("interviews_avg", 0),
                "offers": aggregate_stats.get("offers_avg", 0),
                "dailyChecks": aggregate_stats.get("daily_checks_avg", 0),
                "streak": aggregate_stats.get("streak_avg", 0),
            },
        }

        return Response(response_data)
