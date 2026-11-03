

from __future__ import annotations

from typing import Callable

from rest_framework.permissions import BasePermission

from .permissions import has_role_permission


class HasConfiguredPermission(BasePermission):
    

    permission_name: str | None = None
    message = "You do not have the required permission."

    def _permission_name(self, view) -> str | None:
        """Read the configured permission from the view or the subclass."""
        return getattr(view, "permission_name", None) or self.permission_name

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        permission_name = self._permission_name(view)

        if not user or not user.is_authenticated:
            self.message = "Authentication is required."
            return False

        if not permission_name:
            self.message = "The API view has no permission_name configured."
            return False

        if not getattr(user, "is_active", True):
            self.message = "This account is inactive."
            return False

        allowed = has_role_permission(
            role=getattr(user, "role", ""),
            permission=permission_name,
        )
        if not allowed:
            self.message = "Your role does not have this permission."
        return allowed


class HasAnyConfiguredPermission(HasConfiguredPermission):


    permission_names: set[str] = set()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        names = getattr(view, "permission_names", None) or self.permission_names

        if not user or not user.is_authenticated:
            self.message = "Authentication is required."
            return False
        if not getattr(user, "is_active", True):
            self.message = "This account is inactive."
            return False
        if not names:
            self.message = "The API view has no permission_names configured."
            return False

        allowed = any(
            has_role_permission(getattr(user, "role", ""), name)
            for name in names
        )
        if not allowed:
            self.message = "Your role does not have any required permission."
        return allowed


class IsAssignedInspector(BasePermission):
 

    message = "This handover is not assigned to you."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_active", True)
            and getattr(user, "role", None) == "INSPECTOR"
        )

    def has_object_permission(self, request, view, obj) -> bool:
        resolver: Callable | None = getattr(
            view,
            "assigned_inspector_resolver",
            None,
        )
        if resolver is None:
            self.message = "The API view has no assigned-inspector resolver."
            return False
        return bool(resolver(request, obj))