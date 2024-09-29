from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from .permissions import IsAuthenticatedOrReadOnlyWithAPIKey
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
import logging

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
            logger.error('Error retrieving user: %s', serializer.errors)
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

class AuthenticatedMemberProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            member = User.objects.get(username=request.user)
            serializer = UserSerializer(member)
            return Response(serializer.data)
        except User.DoesNotExist:
            logger.error('Error retrieving user: %s', serializer.errors)
            return Response({"detail": "Member profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            member = User.objects.get(username=request.user)
            serializer = UserSerializer(member, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                logger.error('Error updating user: %s', serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            logger.error('Error updating user: %s', serializer.errors)
            return Response({"detail": "Member profile not found."}, status=status.HTTP_404_NOT_FOUND)

class UpdateDiscordID(APIView):
    permission_classes = [IsAuthenticatedOrReadOnlyWithAPIKey]

    def put(self, request, *args, **kwargs):
        username = request.data.get('username')
        discord_username = request.data.get('discord_username')
        new_discord_id = request.data.get('discord_id')

        logger.info("updating discord id for user: %s", username)

        if not username or not discord_username or not new_discord_id:
            logger.error("Error updating discord id for user: %s: discord_id, discord_username, and username are required", username)
            return Response(
                {"detail": "Username, Discord username, and Discord ID are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = get_object_or_404(User, username=username)


        if member.discord_username.strip().lower() != discord_username.strip().lower():
            logger.error("Error updating discord id for user: %s: discord_username does not match", username)
            return Response(
                {"detail": "Discord username does not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member.discord_id = new_discord_id
        member.save()
        logger.info("saved discord id %s for user: %s", new_discord_id, username)

        is_verified_group, created = Group.objects.get_or_create(name='is_verified')
        member.groups.add(is_verified_group)
        logger.info("added user %s to is_verified group", username)

        serializer = UserSerializer(member)

        return Response(serializer.data, status=status.HTTP_200_OK)