"""Shared permission classes."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(BasePermission):
    """Object-level permission: obj.user must be the requesting user."""

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        return getattr(obj, "user", None) == request.user
