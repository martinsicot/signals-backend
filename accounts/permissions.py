from rest_framework.permissions import BasePermission


def _in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


class IsCustomer(BasePermission):
    """Authenticated user belonging to the 'customer' group."""

    def has_permission(self, request, view):
        return _in_group(request.user, "customer")


class IsCRM(BasePermission):
    """Authenticated user belonging to the 'crm' group."""

    def has_permission(self, request, view):
        return _in_group(request.user, "crm")


class IsOps(BasePermission):
    """Authenticated user belonging to the 'ops' group."""

    def has_permission(self, request, view):
        return _in_group(request.user, "ops")


class IsCRMOrOps(BasePermission):
    """Authenticated user belonging to 'crm' or 'ops'."""

    def has_permission(self, request, view):
        return _in_group(request.user, "crm") or _in_group(request.user, "ops")


class IsStaffOrReadOnly(BasePermission):
    """CRM/ops can write; customers get read-only on shared endpoints."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user.is_authenticated
        return _in_group(request.user, "crm") or _in_group(request.user, "ops")
