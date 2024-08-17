from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Member
from .serializers import MemberSerializer
from .permissions import IsAuthenticatedOrReadOnlyWithAPIKey
from django.shortcuts import get_object_or_404

class MembersList(generics.ListCreateAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class MemberRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    lookup_field = 'pk'

class AuthenticatedMemberProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            member = Member.objects.get(user=request.user)
            serializer = MemberSerializer(member)
            return Response(serializer.data)
        except Member.DoesNotExist:
            return Response({"detail": "Member profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            member = Member.objects.get(user=request.user)
            serializer = MemberSerializer(member, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Member.DoesNotExist:
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


        member = get_object_or_404(Member, user__username__iexact=username)

        if member.discord_username.strip().lower() != discord_username.strip().lower():
            return Response(
                {"detail": "Discord username does not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member.discord_id = new_discord_id
        member.save()

        serializer = MemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)
