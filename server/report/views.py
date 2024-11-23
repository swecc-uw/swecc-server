import time
from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.views import APIView
from custom_auth.permissions import IsAdmin, IsVerified
from rest_framework.permissions import IsAuthenticated

from interview.models import Interview
from members.models import User
from rest_framework import permissions

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

        return Response(
            {
                "reports": serializer.data
            },
            status=status.HTTP_200_OK
        )


class GetAllReports(APIView):
    permission_classes = [IsAdmin]
    def get(self, _):
        reports = Report.objects.all()
        serializer = ReportSerializer(reports, many=True)

        return Response(
            {
                "reports": serializer.data
            },
            status=status.HTTP_200_OK
        )


class GetReportByID(APIView):
    # should change this to admin only @hoang
    permission_classes = [IsAuthenticated, IsVerified]
    def get(self, _, report_id):
        
        report = Report.objects.filter(report_id=report_id)
        if not report:
            return Response(
                {
                    "error": "Report not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ReportSerializer(report[0])
        return Response(
            {
                "report": serializer.data
            },
            status=status.HTTP_200_OK
        )


class AssignReportToAdmin(APIView):
    permission_classes = [IsAdmin]
    def patch(self, _, report_id):
        
        report = Report.objects.filter(report_id=report_id)
        if not report:
            return Response(
                {
                    "error": "Report not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if 'admin_id' not in self.request.data:
            return Response(
                {
                    "error": "admin_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        report = report[0]

        # check if admin exists
        member = User.objects.filter(id=self.request.data['admin_id'])
        if not member:
            return Response(
                {
                    "error": "Admin not found"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        if not member[0].is_staff:
            return Response(
                {
                    "error": "User is not an admin"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        

        report.admin_id = self.request.data['admin_id']
        report.save()

        return Response(
            {
                "report": ReportSerializer(report).data
            },
            status=status.HTTP_200_OK
        )


class CreateReport(APIView):
    permission_classes = [IsAuthenticated, IsVerified]
    def post(self, _):
        # check if all fields are present
        required_fields = ['reporter_user_id', 'type', 'associated_id']
        for field in required_fields:
            if field not in self.request.data:
                return Response(
                    {
                        "error": f"{field} is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        self.request.data['created'] = time.time()
        self.request.data['updated'] = time.time()
        self.request.data['status'] = 'pending'

        if 'reason' not in self.request.data:
            self.request.data['reason'] = 'No reason provided'
        
        type = self.request.data['type']
        if type == 'interview':
            # check if they have interview
            find_interview = Interview.objects.filter(
                interview_id=self.request.data['associated_id']
            )

            if not find_interview:
                return Response(
                    {
                        "error": "Interview not found"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # check user is in the interview
            interview = find_interview[0]
            if not (interview.interviewer.id == self.request.data['reporter_user_id'] or interview.interviewee.id == self.request.data['reporter_user_id']):
                return Response(
                    {
                        "error": "User not in interview"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                ) 
        
        serializer = ReportSerializer(data=self.request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "report": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {
                "error": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class UpdateReportStatus(APIView):
    permission_classes = [IsAdmin]
    def patch(self, request, report_id):
        
        report = Report.objects.filter(report_id=report_id)
        if not report:
            return Response(
                {
                    "error": "Report not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if 'status' not in request.data:
            return Response(
                {
                    "error": "status is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        report = report[0]
        report.status = request.data['status']
        report.save()

        return Response(
            {
                "report": ReportSerializer(report).data
            },
            status=status.HTTP_200_OK
        )