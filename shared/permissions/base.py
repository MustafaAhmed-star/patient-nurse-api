from rest_framework.permissions import BasePermission


class IsAuthenticatedAndNotBlocked(BasePermission):
    message = "Authentication is required or this account is blocked."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not user.is_blocked)


class IsAdminRole(BasePermission):
    message = "Admin access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and not user.is_blocked
            and user.role == user.Role.ADMIN
        )


class IsPatientRole(BasePermission):
    message = "Patient access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and not user.is_blocked
            and user.role == user.Role.PATIENT
        )


class IsApprovedNurseRole(BasePermission):
    message = "Approved nurse access is required."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and not user.is_blocked):
            return False
        if user.role != user.Role.NURSE:
            return False
        return hasattr(user, "nurse_profile") and user.nurse_profile.is_approved
