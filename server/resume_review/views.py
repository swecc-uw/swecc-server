from aws.s3 import S3Client
from custom_auth.permissions import IsVerified
from django.db import IntegrityError
from mq.producers import dev_publish_to_review_resume
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from resume_review.models import Resume

from server.settings import AWS_BUCKET_NAME, DJANGO_DEBUG

# Create your views here.

MAX_RESUME_COUNT = 5

# Kilobytes
MAX_FILE_SIZE = 500


class ResumeUploadView(APIView):
    permission_classes = [IsVerified]

    def post(self, request):

        file_name = request.data.get("file_name")
        file_size = request.data.get("file_size")

        if not file_name or not file_size:
            return Response(
                {"error": "File name or file size not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file_size > MAX_FILE_SIZE:
            return Response(
                {"error": "File size too large."}, status=status.HTTP_400_BAD_REQUEST
            )

        resume_count = Resume.objects.filter(member=request.user).count()

        if resume_count >= MAX_RESUME_COUNT:
            oldest_resume = (
                Resume.objects.filter(member=request.user)
                .order_by("created_at")
                .first()
            )
            oldest_resume.delete()

        try:
            added_resume = Resume.objects.create(
                member=request.user, file_name=file_name, file_size=file_size
            )
            added_resume.save()
        except IntegrityError:
            return Response(
                {"error": "Duplicate file name."}, status=status.HTTP_400_BAD_REQUEST
            )

        file_key = f"{request.user.id}-{added_resume.id}-{file_name}"
        presigned_url = S3Client().get_presigned_url(
            bucket=AWS_BUCKET_NAME, key=file_key
        )

        return Response(
            {
                "presigned_url": presigned_url,
                "key": file_key,
            },
            status=status.HTTP_201_CREATED,
        )


class DevPublishToReview(APIView):
    permission_classes = [IsVerified]

    def post(self, request):

        if not DJANGO_DEBUG:
            return Response(
                {"error": "This endpoint is only available in debug mode."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_key = request.data.get("key")

        if not file_key:
            return Response(
                {"error": "File key not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not file_key.startswith(f"{request.user.id}-"):
            return Response(
                {"error": "Invalid file key."}, status=status.HTTP_400_BAD_REQUEST
            )

        dev_publish_to_review_resume(file_key)
        return Response({"success": True}, status=status.HTTP_200_OK)
