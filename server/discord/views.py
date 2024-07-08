from .models import AuthKey
from .serializers import AuthKeySerializer
from rest_framework import generics, permissions
from .permissions import IsAuthenticatedOrReadOnlyWithAPIKey

class AuthKeyCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = AuthKey.objects.all()
    serializer_class = AuthKeySerializer

class AuthKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnlyWithAPIKey]
    queryset = AuthKey.objects.all()
    serializer_class = AuthKeySerializer

class AuthKeyListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = AuthKey.objects.all()
    serializer_class = AuthKeySerializer