# directory/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from members.models import Member
from .serializers import DirectoryMemberSerializer

# TODO: filter fields by isPrivate

class MemberDirectoryView(APIView):
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