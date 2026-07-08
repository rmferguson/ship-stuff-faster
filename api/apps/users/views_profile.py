"""
Profile detail view — demonstrates IDOR-safe resource access.

The IsOwner permission ensures user A cannot access user B's profile.
Copy this pattern when adding new resources that belong to a user.
"""

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwner

from .models import Profile, User


class ProfileDetailView(APIView):
    """
    Retrieve the profile for a given user pk.

    GET /api/v1/profiles/<user_pk>/
    - Returns 200 if request.user owns this profile
    - Returns 403 if request.user does not own this profile (IsOwner)
    - Returns 404 if the user/profile does not exist
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def get_object(self, user_pk: int) -> Profile:
        user = get_object_or_404(User, pk=user_pk)
        profile, _ = Profile.get_or_create_for_user(user)
        self.check_object_permissions(self.request, profile)
        return profile

    def get(self, request: Request, user_pk: int) -> Response:
        profile = self.get_object(user_pk)
        return Response({"user_id": profile.user_id, "email": profile.user.email})
