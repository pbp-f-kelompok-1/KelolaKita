from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import Profile


def _has_role(user, role):
    return user.is_authenticated and Profile.objects.filter(
        user=user,
        role=role,
    ).exists()


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, Profile.Role.MANAGER)


class CanSubmitDepositRequest(BasePermission):
    def has_permission(self, request, view):
        return (
            (request.method in SAFE_METHODS or request.method == "POST")
            and _has_role(request.user, Profile.Role.USER)
        )


class CanDeleteDepositRequest(BasePermission):
    def has_permission(self, request, view):
        return (
            (
                request.method in SAFE_METHODS
                or request.method in ("POST", "DELETE")
            )
            and (
                _has_role(request.user, Profile.Role.MANAGER)
                or _has_role(request.user, Profile.Role.USER)
            )
        )

    def has_object_permission(self, request, view, obj):
        if _has_role(request.user, Profile.Role.MANAGER):
            return True

        return (
            _has_role(request.user, Profile.Role.USER)
            and obj.pengguna_id == request.user.pk
            and obj.kategori_penanganan == "Menunggu"
        )


class CanViewInspectionResults(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated or _has_role(user, Profile.Role.MANAGER):
            return True
        return obj.pengguna_id == user.pk
