from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
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
from cache import CachedView, DjangoCacheHandler
from .managers import DirectoryManager

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class BaseMemberDirectoryView:
    def get_serializer_class(self, request):
        if IsAdmin.has_permission(self, request, None):
            return AdminDirectoryMemberSerializer
        return RegularDirectoryMemberSerializer


class MemberDirectorySearchView(APIView, BaseMemberDirectoryView, CachedView):
    permission_classes = [IsVerified]
    pagination_class = StandardResultsSetPagination

    def generate_key():
        return "user:all"

    manager = DirectoryManager(DjangoCacheHandler(expiration=60 * 60), generate_key)

    def get(self, request):
        query = request.query_params.get("q", "")
        logger.info("Searching for members with query: %s", query)

        members = self.manager.get_all()

        if query:
            terms = query.split()
            members = [
                member
                for term in terms
                for member in members
                if (
                    term in member.username
                    or term in member.first_name
                    or term in member.last_name
                )
            ]

        paginator = self.pagination_class()
        paginated_members = paginator.paginate_queryset(members, request)

        serializer_class = self.get_serializer_class(request)
        serializer = serializer_class(paginated_members, many=True)

        return paginator.get_paginated_response(serializer.data)


class MemberDirectoryView(APIView, BaseMemberDirectoryView, CachedView):
    permission_classes = [IsVerified]

    def generate_key(**kwargs):
        return f"user:member:{kwargs['id']}"

    manager = DirectoryManager(DjangoCacheHandler(60 * 3), generate_key)

    def get(self, request, id):
        try:
            member = self.manager.get(id, serializer=self.get_serializer_class(request))
            return Response(member)
        except User.DoesNotExist:
            logger.error("Error retrieving user: user with id %s not found", id)
            return JsonResponse({"detail": "Member not found."}, status=404)


def simple_hash(s: str) -> int:
    h = 5381
    for c in s.encode():
        h = ((h * 33) ^ c) & 0xFFFFFFFF
    return h


class RecommendedMembersView(APIView, BaseMemberDirectoryView, CachedView):
    permission_classes = [IsVerified]

    def get_daily_seed(self, username):
        """Generate a consistent daily seed for a user."""
        today = date.today().isoformat()
        seed_string = f"{username}:{today}"
        return simple_hash(seed_string)

    def generate_key(**kwargs):
        return "user:all"

    manager = DirectoryManager(DjangoCacheHandler(60 * 60), generate_key)

    def get(self, request):

        try:
            all_users = self.manager.get_all()
            all_users.remove(request.user)

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
