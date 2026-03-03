"""
JWT Cookie Authentication for DailyFluent.

Stores JWT tokens in httpOnly cookies instead of Authorization headers.
This prevents XSS token theft while maintaining stateless auth.
"""

from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.http import HttpResponse
from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

# Cookie names
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

# Cookie settings
COOKIE_SECURE = not settings.DEBUG  # True in production (HTTPS only)
COOKIE_SAMESITE = "Lax"
COOKIE_HTTPONLY = True
COOKIE_PATH = "/"
ACCESS_MAX_AGE = int(timedelta(minutes=15).total_seconds())
REFRESH_MAX_AGE = int(timedelta(days=7).total_seconds())


class JWTCookieAuth(HttpBearer):
    """
    Django Ninja authenticator that reads JWT from:
      1. httpOnly cookie (primary — browser)
      2. Authorization: Bearer header (API clients)
      3. Django session (backward compat)

    Overrides __call__ because HttpBearer's default __call__
    returns None immediately when no Authorization header exists,
    which skips our cookie-reading logic.
    """

    def __call__(self, request):
        # 1. Try cookie first
        cookie_token = request.COOKIES.get(ACCESS_COOKIE)
        if cookie_token:
            user = self._validate_token(cookie_token, request)
            if user:
                return user

        # 2. Try Authorization: Bearer header (via parent)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user = self._validate_token(token, request)
            if user:
                return user

        # 3. Fall back to Django session (backward compat)
        if hasattr(request, "user") and request.user.is_authenticated:
            return request.user

        return None

    def authenticate(self, request, token=None):
        # Called by HttpBearer parent, but we handle everything in __call__
        return None

    def _validate_token(self, raw_token: str, request):
        """Validate an access token and return the user."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            access = AccessToken(raw_token)
            user_id = access.get("user_id")
            if user_id is None:
                return None
            user = User.objects.get(pk=user_id)
            if not user.is_active:
                return None
            request.user = user
            return user
        except (TokenError, User.DoesNotExist):
            return None


def get_tokens_for_user(user) -> dict:
    """Generate access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def set_jwt_cookies(response: HttpResponse, user) -> HttpResponse:
    """Set access + refresh JWT tokens as httpOnly cookies."""
    tokens = get_tokens_for_user(user)

    response.set_cookie(
        ACCESS_COOKIE,
        tokens["access"],
        max_age=ACCESS_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens["refresh"],
        max_age=REFRESH_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,  # Must be / so cookies flow through Next.js proxy
    )
    return response


def clear_jwt_cookies(response: HttpResponse) -> HttpResponse:
    """Clear JWT cookies (logout)."""
    response.delete_cookie(ACCESS_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    return response


def refresh_access_token(refresh_token_str: str) -> Optional[str]:
    """Generate a new access token from a refresh token."""
    try:
        refresh = RefreshToken(refresh_token_str)
        return str(refresh.access_token)
    except TokenError:
        return None
