"""Auth URL patterns."""

from django.urls import path

from . import views
from .views_profile import ProfileDetailView

urlpatterns = [
    path("auth/signup/", views.SignupView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("auth/token/refresh/", views.TokenRefreshView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("auth/password-reset/", views.PasswordResetRequestView.as_view()),
    path("auth/password-reset/confirm/", views.PasswordResetConfirmView.as_view()),
    # Profile resource — IDOR-safe: IsOwner enforces user A cannot access user B's profile
    path("profiles/<int:user_pk>/", ProfileDetailView.as_view()),
]
