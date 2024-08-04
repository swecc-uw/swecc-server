from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from members.models import Member
import status
from .serializers import DirectoryMemberSerializer

# TODO: filter fields by isPrivate

class MemberDirectorySearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.query_params.get('q', '')

        members = Member.objects.all()

        if query:
            members = members.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        serializer = DirectoryMemberSerializer(members, many=True)
        return Response(serializer.data)

class MemberDirectoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # get id from path parameter
        id = request.query_params.get('id')

        # get Member object with member.user.id == id
        try:
            member = Member.objects.get(user__id=id)
        except Member.DoesNotExist:
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)