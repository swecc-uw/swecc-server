import os
import uuid
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from supabase import Client, create_client

from server import settings
from .models import User
from .serializers import UserSerializer
from .permissions import IsApiKey
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

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

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        return Response({"uid": uid, "token": token}, status=200)
