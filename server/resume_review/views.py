from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from custom_auth.permissions import IsVerified
from rest_framework.views import APIView
from resume_review.models import Resume
from rest_framework.response import Response
from rest_framework import status
from aws.s3 import S3Client
from server.settings import AWS_BUCKET_NAME
from django.utils.crypto import get_random_string

# Create your views here.

MAX_RESUME_COUNT = 5

# Kilobytes
MAX_FILE_SIZE = 500


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def post(self, request):

        file_name = request.data.get("file_name")
        file_size = request.data.get("file_size")

        if file_size > MAX_FILE_SIZE:
            return Response(
                {"error": "File size too large."}, status=status.HTTP_400_BAD_REQUEST
            )

        existing_file_with_name = Resume.objects.filter(file_name=file_name).first()

        if existing_file_with_name:
            return Response(
                {"error": "File with name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume_count = Resume.objects.filter(member=request.user).count()

        if resume_count >= MAX_RESUME_COUNT:
            oldest_resume = (
                Resume.objects.filter(member=request.user)
                .order_by("created_at")
                .first()
            )
            oldest_resume.delete()

        added_resume = Resume.objects.create(
            member=request.user, file_name=file_name, file_size=file_size
        )

        presigned_url = S3Client().get_presigned_url(
            bucket=AWS_BUCKET_NAME, key=added_resume.file_name
        )

        return Response(
            {
                "presigned_url": presigned_url,
                "key": f"{request.user.id}-{added_resume.id}-{get_random_string(length=20)}",
            },
            status=status.HTTP_201_CREATED,
        )
