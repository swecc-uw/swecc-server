from django.contrib.auth.models import User 
from rest_framework import generics
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary='Register a new user',
    request=UserSerializer,
    responses={201: UserSerializer}
)
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, IsAuthenticated)
