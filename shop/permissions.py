from rest_framework.permissions import BasePermission


class IsAdminAuthenticated(BasePermission):
    """Autorise uniquement un utilisateur authentifié et superutilisateur."""

    def has_permission(self, request, view):
        return bool(request.user
                    and request.user.is_authenticated
                    and request.user.is_superuser)


class IsStaffAuthenticated(BasePermission):
    """Autorise uniquement un utilisateur authentifié membre du staff."""

    def has_permission(self, request, view):
        return bool(request.user
                    and request.user.is_authenticated
                    and request.user.is_staff)
