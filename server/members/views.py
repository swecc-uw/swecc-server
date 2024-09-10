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
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

class AuthenticatedMemberProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            member = User.objects.get(username=request.user)
            serializer = UserSerializer(member)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"detail": "Member profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            member = User.objects.get(username=request.user)
            serializer = UserSerializer(member, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"detail": "Member profile not found."}, status=status.HTTP_404_NOT_FOUND)

class UpdateDiscordID(APIView):
    permission_classes = [IsAuthenticatedOrReadOnlyWithAPIKey]

    def put(self, request, *args, **kwargs):
        username = request.data.get('username')
        discord_username = request.data.get('discord_username')
        new_discord_id = request.data.get('discord_id')

        if not username or not discord_username or not new_discord_id:
            return Response(
                {"detail": "Username, Discord username, and Discord ID are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = get_object_or_404(User, username=username)

        if member.discord_username.strip().lower() != discord_username.strip().lower():
            return Response(
                {"detail": "Discord username does not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member.discord_id = new_discord_id
        member.save()

        is_verified_group, created = Group.objects.get_or_create(name='is_verified')
        member.groups.add(is_verified_group)

        serializer = UserSerializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)