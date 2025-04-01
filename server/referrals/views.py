import logging
import uuid

from aws.s3 import S3Client
from custom_auth.permissions import IsAdmin, IsVerified
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.db.models import Prefetch, Q
from rest_framework import exceptions, generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from server.settings import REFERRAL_AWS_BUCKET_NAME

from .models import ReferralDetails, ReferralDocument
from .permissions import IsOwnerOrAdmin
from .producers import publish_status_changed_event
from .serializers import (
    AdminReferralDetailsSerializer,
    BaseReferralDetailsSerializer,
    CreateReferralSerializer,
    ReferralProgramMemberSerializer,
)

logger = logging.getLogger(__name__)

s3_client = S3Client()

UPLOAD_EXPIRATION_SECONDS = 86400  # 24 hours


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ListCreateReferralView(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        status_filter = self.request.query_params.get("status")

        if self.is_admin_user:
            queryset = ReferralDetails.objects.select_related(
                "member"
            ).prefetch_related(
                Prefetch("documents", queryset=ReferralDocument.objects.all())
            )

            if status_filter:
                queryset = queryset.filter(status=status_filter)

        elif self.is_referral_program_user:
            queryset = ReferralDetails.objects.filter(
                Q(status="APPROVED") | Q(member=self.request.user)
            ).select_related("member")

        else:
            queryset = ReferralDetails.objects.filter(
                member=self.request.user
            ).select_related("member")

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateReferralSerializer

        return (
            AdminReferralDetailsSerializer
            if self.is_admin_user
            else ReferralProgramMemberSerializer
        )

    def perform_create(self, serializer):
        try:
            referral = serializer.save(member=self.request.user, status="PENDING")
        except IntegrityError as e:
            logger.error(f"Error creating referral: {e}")
            if "unique_pending_referral_per_member" in str(e):
                raise exceptions.ValidationError(
                    {
                        "error": "You already have a pending referral. Please update your existing referral or wait for it to be processed."
                    }
                )
            raise exceptions.ValidationError({"error": "Failed to create referral"})
        except Exception as e:
            logger.error(f"Error creating referral: {e}")
            raise exceptions.ValidationError({"error": "Failed to create referral"})

        document_id = str(uuid.uuid4())
        document = ReferralDocument.objects.create(
            referral=referral, file_path=f"referrals/{referral.id}/{document_id}.pdf"
        )

        upload_url = s3_client.get_presigned_url(
            bucket=REFERRAL_AWS_BUCKET_NAME,
            key=document.file_path,
            expiration=UPLOAD_EXPIRATION_SECONDS,
        )

        serializer._data = {
            **serializer.data,
            "upload_url": upload_url,
            "document_id": document.id,
        }


class ReferralDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        return (
            AdminReferralDetailsSerializer
            if self.is_admin_user
            else BaseReferralDetailsSerializer
        )

    def get_queryset(self):
        return ReferralDetails.objects.select_related("member").prefetch_related(
            "documents"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        old_status = instance.status

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if (
            "status" in serializer.validated_data
            and serializer.validated_data["status"] != old_status
        ):
            return Response(
                {
                    "error": "Status change not allowed in this view",
                    "old_status": old_status,
                    "requested_status": serializer.validated_data["status"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_update(serializer)

        return Response(serializer.data)


class DocumentUploadView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, referral_id):
        try:
            referral = ReferralDetails.objects.get(id=referral_id)

            document_id = str(uuid.uuid4())
            document = ReferralDocument.objects.create(
                referral=referral,
                file_path=f"referrals/{referral.id}/{document_id}.pdf",
                uploaded=False,
            )

            old_status = referral.status
            if old_status != "PENDING":
                referral.status = "PENDING"
                referral.save(update_fields=["status", "updated_at"])

                publish_status_changed_event(
                    referral_id=referral.id,
                    notes="User is requesting to upload a document, moving them back to PENDING",
                    member_id=referral.member.id,
                    previous_status=old_status,
                    new_status="PENDING",
                )

            upload_url = s3_client.get_presigned_url(
                bucket=REFERRAL_AWS_BUCKET_NAME,
                key=document.file_path,
                expiration=UPLOAD_EXPIRATION_SECONDS,
            )

            return Response(
                {
                    "upload_url": upload_url,
                    "document_id": document.id,
                    "expires_in_seconds": UPLOAD_EXPIRATION_SECONDS,
                }
            )

        except ReferralDetails.DoesNotExist:
            return Response(
                {"error": "Referral not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ReferralReviewView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, referral_id):
        try:
            decision = request.data.get("decision")
            if decision not in ["APPROVED", "DENIED"]:
                return Response(
                    {"error": "Decision must be either APPROVED or DENIED"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            notes = request.data.get("notes")
            referral = ReferralDetails.objects.select_related("member").get(
                id=referral_id
            )

            valid_transitions = {
                "PENDING": ["APPROVED", "DENIED"],
            }

            current_status = referral.status
            if (
                current_status not in valid_transitions
                or decision not in valid_transitions.get(current_status, [])
            ):
                return Response(
                    {
                        "error": f"Invalid status transition from {current_status} to {decision}",
                        "valid_transitions": valid_transitions.get(current_status, []),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            previous_status = referral.status
            referral.status = decision
            referral.save(update_fields=["status", "updated_at"])

            if decision == "APPROVED":
                group, _ = Group.objects.get_or_create(name="is_referral_program")
                referral.member.groups.add(group)
            elif decision != "APPROVED":
                group = Group.objects.filter(name="is_referral_program").first()
                if group:
                    referral.member.groups.remove(group)

            publish_status_changed_event(
                referral_id=referral.id,
                member_id=referral.member.id,
                notes=notes,
                previous_status=previous_status,
                new_status=decision,
            )

            return Response({"status": "Review submitted successfully"})

        except ReferralDetails.DoesNotExist:
            return Response(
                {"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND
            )


class MyPendingReferralsView(generics.ListAPIView):
    permission_classes = [IsVerified]
    serializer_class = BaseReferralDetailsSerializer

    def get_queryset(self):
        return ReferralDetails.objects.filter(
            member=self.request.user, status="PENDING"
        ).select_related("member")
