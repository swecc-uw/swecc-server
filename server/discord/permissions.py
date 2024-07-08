from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework_api_key.permissions import HasAPIKey

class IsAuthenticatedOrReadOnlyWithAPIKey(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return HasAPIKey().has_permission(request, view)