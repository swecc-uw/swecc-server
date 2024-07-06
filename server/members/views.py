from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Member
from .serializers import MemberSerializer

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