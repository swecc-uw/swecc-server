from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from members.models import User
from .serializers import DirectoryMemberSerializer
from custom_auth.permissions import IsVerified


# TODO: filter fields by isPrivate

class MemberDirectorySearchView(APIView):
    permission_classes = [IsVerified]
    def get(self, request):
        query = request.query_params.get('q', '')

        members = User.objects.all()

        if query:
            members = members.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        serializer = DirectoryMemberSerializer(members, many=True)
        return Response(serializer.data)

class MemberDirectoryView(APIView):
    permission_classes = [IsVerified]

    def get(self, request, id):
        try:
            member = User.objects.get(id=id)
            serializer = DirectoryMemberSerializer(member)
            return Response(serializer.data)
        except User.DoesNotExist:
            return JsonResponse({'detail': 'Member not found.'}, status=404)
