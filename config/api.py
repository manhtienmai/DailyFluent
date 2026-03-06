"""
Central Django Ninja API instance for DailyFluent.

All Next.js frontend requests go through /api/v1/.
Uses JWT cookie authentication (httpOnly cookies).
OpenAPI docs available at /api/v1/docs (DEBUG only).
"""

from ninja import NinjaAPI, Schema
from ninja.security import django_auth

from config.jwt_auth import (
    JWTCookieAuth,
    set_jwt_cookies,
    clear_jwt_cookies,
    refresh_access_token,
    get_tokens_for_user,
    REFRESH_COOKIE,
)

from kanji.api import router as kanji_router
from streak.api import router as streak_router
from wallet.api import router as wallet_router
from shop.api import router as shop_router

# ── JWT Auth instance ──────────────────────────────────────
jwt_auth = JWTCookieAuth()

api = NinjaAPI(
    title="DailyFluent API",
    version="1.0.0",
    description="REST API for the DailyFluent language learning platform.",
    auth=jwt_auth,
    urls_namespace="api",
)


# ── Auth Schemas ───────────────────────────────────────────

class UserOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str


class LoginIn(Schema):
    email: str
    password: str


class SignupIn(Schema):
    email: str
    password1: str
    password2: str


class AuthResult(Schema):
    success: bool
    message: str = ""
    user: UserOut | None = None
    access_token: str | None = None
    refresh_token: str | None = None


class CSRFOut(Schema):
    csrfToken: str


# ── Auth Endpoints ─────────────────────────────────────────

@api.post("/auth/login", response={200: AuthResult, 401: AuthResult}, auth=None, tags=["Auth"])
def login(request, payload: LoginIn):
    """Login with email + password. Sets JWT cookies."""
    from django.contrib.auth import authenticate

    user = authenticate(
        request,
        username=payload.email,
        password=payload.password,
    )
    if user is None:
        return 401, {"success": False, "message": "Email hoặc mật khẩu không đúng."}

    tokens = get_tokens_for_user(user)
    response = api.create_response(
        request,
        {
            "success": True,
            "message": "Đăng nhập thành công.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
        },
        status=200,
    )
    return set_jwt_cookies(response, user)


@api.post("/auth/signup", response={201: AuthResult, 400: AuthResult}, auth=None, tags=["Auth"])
def signup(request, payload: SignupIn):
    """Signup with email + password. Sets JWT cookies."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    if payload.password1 != payload.password2:
        return 400, {"success": False, "message": "Mật khẩu không khớp."}

    if len(payload.password1) < 8:
        return 400, {"success": False, "message": "Mật khẩu tối thiểu 8 ký tự."}

    if User.objects.filter(email=payload.email).exists():
        return 400, {"success": False, "message": "Email đã được sử dụng."}

    # Create user
    username = payload.email.split("@")[0]
    # Ensure unique username
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    user = User.objects.create_user(
        username=username,
        email=payload.email,
        password=payload.password1,
    )

    tokens = get_tokens_for_user(user)
    response = api.create_response(
        request,
        {
            "success": True,
            "message": "Đăng ký thành công.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
        },
        status=201,
    )
    return set_jwt_cookies(response, user)


@api.post("/auth/refresh", auth=None, tags=["Auth"])
def refresh_token(request):
    """Refresh the access token using the refresh cookie or body."""
    # Accept refresh token from body (mobile) or cookie (web)
    import json
    body_token = None
    try:
        body = json.loads(request.body) if request.body else {}
        body_token = body.get("refresh_token")
    except Exception:
        pass
    refresh_cookie = body_token or request.COOKIES.get(REFRESH_COOKIE)

    if not refresh_cookie:
        return api.create_response(
            request,
            {"success": False, "message": "No refresh token."},
            status=401,
        )

    new_access = refresh_access_token(refresh_cookie)
    if new_access is None:
        resp = api.create_response(
            request,
            {"success": False, "message": "Refresh token expired."},
            status=401,
        )
        return clear_jwt_cookies(resp)

    from config.jwt_auth import ACCESS_COOKIE, COOKIE_HTTPONLY, COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_PATH, ACCESS_MAX_AGE

    response = api.create_response(
        request,
        {"success": True, "access_token": new_access},
        status=200,
    )
    response.set_cookie(
        ACCESS_COOKIE,
        new_access,
        max_age=ACCESS_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )
    return response


@api.post("/auth/logout", tags=["Auth"])
def logout(request):
    """Clear JWT cookies."""
    response = api.create_response(
        request,
        {"success": True, "message": "Đăng xuất thành công."},
        status=200,
    )
    return clear_jwt_cookies(response)


@api.get("/auth/me", response=UserOut, tags=["Auth"])
def me(request):
    """Return the currently authenticated user."""
    return request.user


@api.get("/auth/csrf", response=CSRFOut, auth=None, tags=["Auth"])
def csrf_token(request):
    """Return a fresh CSRF token (backward compatibility)."""
    from django.middleware.csrf import get_token
    return {"csrfToken": get_token(request)}


# ── App routers ────────────────────────────────────────────

api.add_router("/kanji/", kanji_router, tags=["Kanji"])
api.add_router("/streak/", streak_router, tags=["Streak"])
api.add_router("/wallet/", wallet_router, tags=["Wallet"])
api.add_router("/shop/", shop_router, tags=["Shop"])

# ── New module routers ─────────────────────────────────────

from video.api import router as video_router
from todos.api import router as todos_router
from payment.api import router as payment_router
from feedback.api import router as feedback_router
from core.api import router as core_router
from grammar.api import router as grammar_router
from exam.api import router as exam_router
from placement.api import router as placement_router
from vocab.api import router as vocab_router

api.add_router("/videos/", video_router, tags=["Videos"])
api.add_router("/todos/", todos_router, tags=["Todos"])
api.add_router("/payment/", payment_router, tags=["Payment"])
api.add_router("/feedback/", feedback_router, tags=["Feedback"])
api.add_router("/", core_router, tags=["Core"])
api.add_router("/grammar/", grammar_router, tags=["Grammar"])
api.add_router("/exam/", exam_router, tags=["Exam"])
api.add_router("/placement/", placement_router, tags=["Placement"])
api.add_router("/vocab/", vocab_router, tags=["Vocab"])

from common.api import router as common_router
api.add_router("/", common_router, tags=["Common"])

from ebook.api import router as ebook_router
api.add_router("/ebooks/", ebook_router, tags=["Ebooks"])

from notifications.api import router as notifications_router
api.add_router("/notifications/", notifications_router, tags=["Notifications"])

# ── Admin API (for Next.js admin dashboard) ────────────────
from config.admin_api import router as admin_router
api.add_router("/admin/", admin_router, tags=["Admin"])

from config.admin_crud import router as admin_crud_router
api.add_router("/admin/crud/", admin_crud_router, tags=["Admin CRUD"])

from notifications.teacher_api import router as teacher_dashboard_router
api.add_router("/admin/teacher-dashboard/", teacher_dashboard_router, tags=["Teacher Dashboard"])

from config.admin_user_history import router as admin_user_history_router
api.add_router("/admin/users/", admin_user_history_router, tags=["Admin User History"])
