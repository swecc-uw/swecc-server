import time
from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.views import APIView
from custom_auth.permissions import IsAdmin, IsVerified
from rest_framework.permissions import IsAuthenticated

from interview.models import Interview
from members.models import User
from rest_framework import permissions

from questions.models import TechnicalQuestion

from .serializers import ReportSerializer
from .models import Report

from rest_framework import status


class ReportOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.reporter_user_id == request.user.id


# Create your views here.
class GetReportByUserID(APIView):
    permission_classes = [IsAuthenticated, ReportOwnerPermission, IsVerified]

    def get(self, request, user_id):
        reports = Report.objects.filter(reporter_user_id=user_id)
        serializer = ReportSerializer(reports, many=True)

        return Response({"reports": serializer.data}, status=status.HTTP_200_OK)


class GetAllReports(APIView):
    permission_classes = [IsAdmin]

    def get(self, _):
        reports = Report.objects.all()
        serializer = ReportSerializer(reports, many=True)

        return Response({"reports": serializer.data}, status=status.HTTP_200_OK)


class GetReportByID(APIView):
    permission_classes = [IsAdmin]

    def get(self, _, report_id):

        report = Report.objects.filter(report_id=report_id)
        if not report:
            return Response(
                {"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReportSerializer(report[0])
        return Response({"report": serializer.data}, status=status.HTTP_200_OK)


class AssignReportToAdmin(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, report_id):

        report = Report.objects.filter(report_id=report_id)
        if not report:
            return Response(
                {"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if "assignee" not in request.data:
            return Response(
                {"error": "assignee is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        report = report[0]

        # check if admin exists
        member = User.objects.get(id=request.data["assignee"])
        if not member:
            return Response(
                {"error": "Admin not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not member.groups.filter(name="is_admin").exists():
            return Response(
                {"error": "User is not an admin"}, status=status.HTTP_400_BAD_REQUEST
            )

        report.assignee = member
        report.status = "resolving"
        report.save()

        return Response(
            {"report": ReportSerializer(report).data}, status=status.HTTP_200_OK
        )


class CreateReport(APIView):
    permission_classes = [IsVerified]

    def post(self, request):
        required_fields = ["reporter_user_id", "type", "associated_id"]
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {"error": f"{field} is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            reporter = User.objects.get(id=request.data["reporter_user_id"])

            report_data = {
                "reporter_user_id": reporter,
                "type": request.data["type"],
                "reason": request.data.get("reason", "No reason provided"),
                "status": "pending",
            }

            if report_data["type"] == "interview":
                interview = Interview.objects.get(
                    interview_id=request.data["associated_id"]
                )
                if not (
                    interview.interviewer.id == reporter.id
                    or interview.interviewee.id == reporter.id
                ):
                    return Response(
                        {"error": "User not in interview"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                report_data["associated_interview"] = interview

            elif report_data["type"] == "question":
                question = TechnicalQuestion.objects.get(
                    question_id=request.data["associated_id"]
                )
                report_data["associated_question"] = question

            elif report_data["type"] == "member":
                member = User.objects.get(id=request.data["associated_id"])
                if member.id == reporter.id:
                    return Response(
                        {"error": "Cannot report yourself"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                report_data["associated_member"] = member

            else:
                return Response(
                    {"error": "Invalid report type"}, status=status.HTTP_400_BAD_REQUEST
                )
            report = Report.objects.create(**report_data)
            serializer = ReportSerializer(report)
            return Response({"report": serializer.data}, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response(
                {"error": "Reporter user not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except (Interview.DoesNotExist, TechnicalQuestion.DoesNotExist):
            return Response(
                {"error": f"{report_data['type'].capitalize()} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateReportStatus(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, report_id):

        report = Report.objects.filter(report_id=report_id)
        if not report:
            return Response(
                {"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if "status" not in request.data:
            return Response(
                {"error": "status is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.data["status"] not in Report.STATUS_CHOICES:
            return Response(
                {"error": "Invalid status provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        report = report[0]
        report.status = request.data["status"]
        report.save()

        return Response(
            {"report": ReportSerializer(report).data}, status=status.HTTP_200_OK
        )
