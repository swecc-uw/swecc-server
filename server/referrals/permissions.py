from rest_framework import permissions


class ReferralProgramPermissions(permissions.BasePermission):
    def _set_user_roles(self, request, view):
        if not hasattr(request, "_user_roles_cached"):
            user_groups = set(request.user.groups.values_list("name", flat=True))
            view.is_admin_user = "is_admin" in user_groups
            view.is_referral_program_user = "is_referral_program" in user_groups
            view.is_verified_user = "is_verified" in user_groups
            request._user_roles_cached = True

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        self._set_user_roles(request, view)

        if request.method == "GET":
            return True
        else:
            return view.is_verified_user

    def has_object_permission(self, request, view, obj):
        self._set_user_roles(request, view)

        if view.is_admin_user:
            return True

        if view.is_referral_program_user and obj.status == "APPROVED":
            return True

        return obj.member == request.user
