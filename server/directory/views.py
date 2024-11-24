from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from members.models import User
from .serializers import (
    RegularDirectoryMemberSerializer,
    AdminDirectoryMemberSerializer,
)
from custom_auth.permissions import IsAdmin, IsVerified
import logging
from datetime import date
import random

logger = logging.getLogger(__name__)


class BaseMemberDirectoryView:

    def get_serializer_class(self, request):

        if IsAdmin.has_permission(self, request, None):
            return AdminDirectoryMemberSerializer
        return RegularDirectoryMemberSerializer


class MemberDirectorySearchView(APIView, BaseMemberDirectoryView):
    permission_classes = [IsVerified]

    def get(self, request):
        query = request.query_params.get("q", "")
        logger.info("Searching for members with query: %s", query)

        members = User.objects.all()
        if query:
            members = members.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )

        serializer_class = self.get_serializer_class(request)
        serializer = serializer_class(members, many=True)
        return Response(serializer.data)


class MemberDirectoryView(APIView, BaseMemberDirectoryView):
    permission_classes = [IsVerified]

    def get(self, request, id):
        try:
            member = User.objects.get(id=id)
            serializer_class = self.get_serializer_class(request)
            serializer = serializer_class(member)
            return Response(serializer.data)
        except User.DoesNotExist:
            logger.error("Error retrieving user: user with id %s not found", id)
            return JsonResponse({"detail": "Member not found."}, status=404)


def simple_hash(s: str) -> int:
    h = 5381
    for c in s.encode():
        h = ((h * 33) ^ c) & 0xFFFFFFFF
    return h


class RecommendedMembersView(APIView, BaseMemberDirectoryView):
    permission_classes = [IsVerified]

    def get_daily_seed(self, username):
        """Generate a consistent daily seed for a user."""
        today = date.today().isoformat()
        seed_string = f"{username}:{today}"
        return simple_hash(seed_string)

    def get(self, request):
        try:
            all_users = list(User.objects.exclude(id=request.user.id))

            if not all_users:
                return Response([])

            seed = self.get_daily_seed(request.user.username)

            r = random.Random(seed)
            r.shuffle(all_users)

            recommended = all_users[:5]

            serializer_class = self.get_serializer_class(request)
            serializer = serializer_class(recommended, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error("Error getting recommended members: %s", str(e))
            return JsonResponse(
                {"detail": "Error getting recommendations."}, status=500
            )
