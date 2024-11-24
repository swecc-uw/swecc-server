from rest_framework.permissions import BasePermission
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.exceptions import PermissionDenied

class IsApiKey(BasePermission):
    def has_permission(self, request, view):
        has_api_key = HasAPIKey().has_permission(request, view)
        if not has_api_key:
            raise PermissionDenied("Invalid or missing API key.")
        return has_api_key