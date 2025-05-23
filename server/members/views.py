import logging
import os
import time

import jwt
from custom_auth.permissions import IsAdmin, IsVerified
from custom_auth.views import create_password_reset_creds
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from email_util.send_email import send_email
from mq.producers import publish_verified_email
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from supabase import Client, create_client

from server import settings
from server.settings import JWT_SECRET, VERIFICATION_EMAIL_ADDR

from .models import User
from .notification import verify_school_email_html
from .permissions import IsApiKey
from .serializers import UserSerializer

logger = logging.getLogger(__name__)


class MembersList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MemberRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, member_id):
        try:
            member = User.objects.get(id=member_id)
            serializer = UserSerializer(member)
            return Response(serializer.data)
        except User.DoesNotExist:
            logger.error("Error retrieving user: %s", serializer.errors)
            return Response(
                {"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND
            )


class AuthenticatedMemberProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            member = User.objects.get(username=request.user)
            serializer = UserSerializer(member)
            return Response(serializer.data)
        except User.DoesNotExist:
            logger.error("Error retrieving user: %s", serializer.errors)
            return Response(
                {"detail": "Member profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request):
        try:
            member = User.objects.get(username=request.user)
            serializer = UserSerializer(member, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                logger.error("Error updating user: %s", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            logger.error("Error updating user: %s", serializer.errors)
            return Response(
                {"detail": "Member profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class UpdateDiscordID(APIView):
    permission_classes = [IsApiKey]

    def put(self, request, *args, **kwargs):
        username = request.data.get("username")
        discord_username = request.data.get("discord_username")
        new_discord_id = request.data.get("discord_id")

        logger.info("updating discord id for user: %s", username)

        if not username or not discord_username or not new_discord_id:
            logger.error(
                "Error updating discord id for user: %s: discord_id, discord_username, and username are required",
                username,
            )
            return Response(
                {"detail": "Username, Discord username, and Discord ID are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member = get_object_or_404(User, username=username)

        if member.discord_username.strip().lower() != discord_username.strip().lower():
            logger.error(
                "Error updating discord id for user: %s: discord_username does not match",
                username,
            )
            return Response(
                {"detail": "Discord username does not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.discord_id = new_discord_id
        member.save()
        logger.info("saved discord id %s for user: %s", new_discord_id, username)

        is_verified_group, created = Group.objects.get_or_create(name="is_verified")
        member.groups.add(is_verified_group)
        logger.info("added user %s to is_verified group", username)

        serializer = UserSerializer(member)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfilePictureUploadView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def post(self, request, *args, **kwargs):
        # Check if file was uploaded
        if "profile_picture" not in request.FILES:
            return JsonResponse({"error": "No file was uploaded"}, status=400)

        # get the user
        user = request.user

        file = request.FILES["profile_picture"]

        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            return JsonResponse(
                {
                    "error": "Invalid file type. Only JPEG, PNG and GIF files are allowed."
                },
                status=400,
            )

        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse(
                {"error": "File too large. Maximum size is 5MB."}, status=400
            )

        # Generate unique filename
        file_extension = os.path.splitext(file.name)[1]
        upload_name = f"{user.username}_profile_picture"

        # Initialize Supabase client
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        # Upload to Supabase storage
        # The bucket should be public and already created in Supabase
        bucket_name = "assets"
        file_path = f"profile_pictures/{upload_name}{file_extension}"

        try:
            # Remove existing file if it exists
            supabase.storage.from_(bucket_name).remove([file_path])

            # Upload the file to Supabase storage
            supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file.read(),
                file_options={"content-type": file.content_type},
            )

            # Get the public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

            member = User.objects.get(username=user.username)
            # Delete old profile picture if it exists
            if member.profile_picture_url:
                try:
                    old_file_path = request.user.profile_picture_url.split(
                        f"{bucket_name}/"
                    )[1]
                    supabase.storage.from_(bucket_name).remove([old_file_path])
                except Exception as e:
                    logger.warning(f"Failed to delete old profile picture: {str(e)}")

            # Update user's profile picture URL
            request.user.profile_picture_url = public_url
            request.user.save()

            return JsonResponse(
                {"message": "Profile picture updated successfully", "url": public_url}
            )

        except Exception as e:
            logger.error(f"Supabase storage error: {str(e)}")
            return JsonResponse(
                {"error": "Failed to upload file to storage"}, status=500
            )


class PasswordResetRequest(APIView):
    permission_classes = [IsApiKey]

    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        user = get_object_or_404(User, discord_id=discord_id)

        uuid, token = create_password_reset_creds(user)

        return Response({"uid": uuid, "token": token}, status=200)


class AdminList(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        return Group.objects.get(name="is_admin").user_set.all()


class UpdateDiscordUsername(APIView):
    permission_classes = [IsAuthenticated, ~IsVerified]

    def post(self, request):
        new_discord_username = request.data.get("new_discord_username")

        request.user.discord_username = new_discord_username
        request.user.save()
        logger.info(
            "Updated `discord_username` for user %s with value: %s",
            request.user.username,
            request.user.discord_username,
        )

        return Response({"success": True}, status=200)


class VerifySchoolEmailRequest(APIView):
    permission_classes = [IsApiKey | IsVerified]

    def post(self, request):
        discord_id = request.data.get("discord_id")
        user_id = request.data.get("user_id")
        school_email = request.data.get("school_email")

        if not discord_id and not user_id:
            return Response(
                {"detail": "Discord ID or user ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not school_email:
            return Response(
                {"detail": "School email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not IsApiKey().has_permission(request, self) and request.user.id != user_id:
            return Response({"detail": "Provided user does not match."}, status=403)

        existing_user_with_email = User.objects.filter(
            school_email=school_email
        ).first()
        if existing_user_with_email:
            return Response(
                {"detail": "Email already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = (
            get_object_or_404(User, discord_id=discord_id)
            if discord_id
            else get_object_or_404(User, id=user_id)
        )

        hour = 60 * 60
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": int(time.time()) + hour,
            "email": school_email,
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        send_email(
            from_email=VERIFICATION_EMAIL_ADDR,
            to_email=school_email,
            subject="SWECC Verification: Verify your school email",
            html_content=verify_school_email_html(token.decode()),
        )
        return Response({"token": token}, status=200)


class ConfirmVerifySchoolEmail(APIView):
    permission_classes = [IsVerified]

    def post(self, request, token):
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response(
                {"detail": "Token has expired"}, status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.InvalidTokenError:
            return Response(
                {"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.id != payload["user_id"]:
            return Response({"detail": "User does not match token"}, status=403)

        try:
            request.user.school_email = payload["email"]
            request.user.save()
        except IntegrityError:
            return Response(
                {"detail": "Email already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        publish_verified_email(request.user.discord_id)

        return Response({"detail": "School email verified"}, status=200)
