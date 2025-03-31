from rest_framework import permissions


class IsVerified(permissions.BasePermission):
    """
    Custom permission to only allow access to users in the 'is_verified' group.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="is_verified").exists()
        )


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow access to users in the 'is_admin' group.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="is_admin").exists()
        )
