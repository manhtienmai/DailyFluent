"""
TC-01: Auth Flow Tests — Signup, Login, JWT, OAuth, Profile Auto-creation.

Covers:
  - POST /api/v1/auth/signup   → JWT cookie signup
  - POST /api/v1/auth/login    → JWT cookie login
  - POST /api/v1/auth/refresh  → access token refresh
  - POST /api/v1/auth/logout   → clear cookies
  - GET  /api/v1/auth/me       → authenticated user info
  - GET  /                     → home view auto-creates UserProfile, StreakStat, etc.
  - SocialAccountAdapter       → Google OAuth merge with existing email
  - StreakMiddleware            → auto-registers login streak
"""

import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

# ── Constants ──────────────────────────────────────────────
API_SIGNUP = "/api/v1/auth/signup"
API_LOGIN = "/api/v1/auth/login"
API_REFRESH = "/api/v1/auth/refresh"
API_LOGOUT = "/api/v1/auth/logout"
API_ME = "/api/v1/auth/me"
API_CSRF = "/api/v1/auth/csrf"

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


# ===========================================================================
#  1. Signup API
# ===========================================================================
class SignupAPITests(TestCase):
    """Test POST /api/v1/auth/signup"""

    def test_signup_success(self):
        """Happy path: new user registers with valid email + password."""
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "newuser@example.com",
                "password1": "securepass123",
                "password2": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["user"]["email"], "newuser@example.com")

        # User is now in DB
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_signup_sets_jwt_cookies(self):
        """Signup should set both access_token and refresh_token cookies."""
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "cookie@example.com",
                "password1": "securepass123",
                "password2": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertIn(ACCESS_COOKIE, resp.cookies)
        self.assertIn(REFRESH_COOKIE, resp.cookies)

        # Cookies should be httpOnly
        self.assertTrue(resp.cookies[ACCESS_COOKIE]["httponly"])
        self.assertTrue(resp.cookies[REFRESH_COOKIE]["httponly"])

    def test_signup_password_mismatch(self):
        """Should return 400 when password1 ≠ password2."""
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "user@example.com",
                "password1": "password_one",
                "password2": "password_two",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertFalse(body["success"])
        self.assertIn("không khớp", body["message"])

    def test_signup_password_too_short(self):
        """Should return 400 when password < 8 chars."""
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "short@example.com",
                "password1": "abc",
                "password2": "abc",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertFalse(body["success"])
        self.assertIn("8 ký tự", body["message"])

    def test_signup_duplicate_email(self):
        """Should return 400 when email already exists."""
        User.objects.create_user(
            username="existing",
            email="dup@example.com",
            password="password123",
        )
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "dup@example.com",
                "password1": "password123",
                "password2": "password123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertFalse(body["success"])
        self.assertIn("đã được sử dụng", body["message"])

    def test_signup_generates_unique_username(self):
        """Username derived from email prefix, with counter for duplicates."""
        # Pre-create a user whose username matches what the signup would generate
        User.objects.create_user(
            username="testuser",
            email="other@mail.com",
            password="password123",
        )
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "testuser@example.com",
                "password1": "securepass123",
                "password2": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        new_user = User.objects.get(email="testuser@example.com")
        # Should be "testuser1" because "testuser" is taken
        self.assertEqual(new_user.username, "testuser1")

    def test_signup_username_collision_multiple(self):
        """Multiple username collisions → counter increments."""
        User.objects.create_user(username="alice", email="a1@test.com", password="pass1234")
        User.objects.create_user(username="alice1", email="a2@test.com", password="pass1234")
        User.objects.create_user(username="alice2", email="a3@test.com", password="pass1234")

        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "alice@example.com",
                "password1": "securepass123",
                "password2": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        new_user = User.objects.get(email="alice@example.com")
        self.assertEqual(new_user.username, "alice3")


# ===========================================================================
#  2. Login API
# ===========================================================================
class LoginAPITests(TestCase):
    """Test POST /api/v1/auth/login"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="correctpass123",
        )

    def test_login_success(self):
        """Happy path: correct email + password → 200 + JWT cookies."""
        resp = self.client.post(
            API_LOGIN,
            data=json.dumps({
                "email": "login@example.com",
                "password": "correctpass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["user"]["email"], "login@example.com")

        # JWT cookies are set
        self.assertIn(ACCESS_COOKIE, resp.cookies)
        self.assertIn(REFRESH_COOKIE, resp.cookies)

    def test_login_wrong_password(self):
        """Should return 401 for wrong password."""
        resp = self.client.post(
            API_LOGIN,
            data=json.dumps({
                "email": "login@example.com",
                "password": "wrong_password",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)
        body = resp.json()
        self.assertFalse(body["success"])

    def test_login_nonexistent_email(self):
        """Should return 401 for email that doesn't exist."""
        resp = self.client.post(
            API_LOGIN,
            data=json.dumps({
                "email": "nobody@example.com",
                "password": "password123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_login_inactive_user(self):
        """Should return 401 for deactivated user.

        Note: Django's ModelBackend rejects inactive users at authenticate()
        level, so the response message is the generic 'wrong credentials'
        rather than 'tài khoản bị vô hiệu hóa'.
        """
        self.user.is_active = False
        self.user.save()

        resp = self.client.post(
            API_LOGIN,
            data=json.dumps({
                "email": "login@example.com",
                "password": "correctpass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)
        body = resp.json()
        self.assertFalse(body["success"])


# ===========================================================================
#  3. JWT Cookie Lifecycle
# ===========================================================================
class JWTCookieLifecycleTests(TestCase):
    """Test JWT refresh, /me, and logout."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="jwtuser",
            email="jwt@example.com",
            password="password123",
        )
        # Login to get cookies
        resp = self.client.post(
            API_LOGIN,
            data=json.dumps({
                "email": "jwt@example.com",
                "password": "password123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_me_with_valid_token(self):
        """/me should return current user info when JWT cookie is valid."""
        resp = self.client.get(API_ME)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["email"], "jwt@example.com")
        self.assertEqual(body["username"], "jwtuser")

    def test_me_without_token(self):
        """/me should return 401 when no cookie/header."""
        client = Client()  # Fresh client — no cookies
        resp = client.get(API_ME)
        self.assertIn(resp.status_code, [401, 403])

    def test_refresh_token(self):
        """POST /auth/refresh should return new access token."""
        resp = self.client.post(API_REFRESH, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        # Access cookie should be (re-)set
        self.assertIn(ACCESS_COOKIE, resp.cookies)

    def test_refresh_without_cookie(self):
        """Refresh without refresh_token cookie → 401."""
        client = Client()
        resp = client.post(API_REFRESH, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

    def test_logout_clears_cookies(self):
        """POST /auth/logout should clear JWT cookies."""
        resp = self.client.post(API_LOGOUT, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])

        # After logout, cookies should be cleared — /me should fail
        resp = self.client.get(API_ME)
        self.assertIn(resp.status_code, [401, 403])

    def test_csrf_endpoint_public(self):
        """GET /auth/csrf should work without auth (auth=None)."""
        client = Client()
        resp = client.get(API_CSRF)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("csrfToken", body)
        self.assertTrue(len(body["csrfToken"]) > 0)


# ===========================================================================
#  4. JWT Token Validation (JWTCookieAuth)
# ===========================================================================
class JWTCookieAuthTests(TestCase):
    """Test the JWTCookieAuth authenticator directly."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="authtest",
            email="authtest@example.com",
            password="password123",
        )

    def test_auth_via_bearer_header(self):
        """Should accept valid Bearer token in Authorization header."""
        from config.jwt_auth import get_tokens_for_user

        tokens = get_tokens_for_user(self.user)

        resp = self.client.get(
            API_ME,
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["email"], "authtest@example.com")

    def test_auth_with_invalid_token(self):
        """Should reject invalid/expired tokens."""
        resp = self.client.get(
            API_ME,
            HTTP_AUTHORIZATION="Bearer invalid.token.here",
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_auth_inactive_user_token(self):
        """Should reject token of deactivated user."""
        from config.jwt_auth import get_tokens_for_user

        tokens = get_tokens_for_user(self.user)
        self.user.is_active = False
        self.user.save()

        resp = self.client.get(
            API_ME,
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_auth_fallback_to_session(self):
        """Should fall back to Django session if no JWT present."""
        self.client.force_login(self.user)
        resp = self.client.get(API_ME)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["email"], "authtest@example.com")


# ===========================================================================
#  5. Home View — Auto-creation of Related Models
# ===========================================================================
class HomeViewAutoCreationTests(TestCase):
    """
    Verify that accessing the home view auto-creates:
    - StreakStat (via get_or_create)
    - UserStudySettings (via get_or_create)
    - UserProfile (via get_or_create_for_user)
    - ExamGoal (via get_or_create)

    We mock django.shortcuts.render to avoid TemplateDoesNotExist in test env.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="homeuser",
            email="home@example.com",
            password="password123",
        )
        self.client.force_login(self.user)
        # Patcher to bypass template rendering
        from django.http import HttpResponse
        self._render_patcher = patch(
            "core.views.render",
            side_effect=lambda request, template, context=None: HttpResponse(
                f"mocked:{template}", content_type="text/html"
            ),
        )
        self._mock_render = self._render_patcher.start()

    def tearDown(self):
        self._render_patcher.stop()

    def test_home_creates_streak_stat(self):
        """Home view should auto-create StreakStat for logged-in user."""
        from streak.models import StreakStat

        self.assertFalse(StreakStat.objects.filter(user=self.user).exists())
        self.client.get("/")
        self.assertTrue(StreakStat.objects.filter(user=self.user).exists())

    def test_home_creates_study_settings(self):
        """Home view should auto-create UserStudySettings."""
        from vocab.models import UserStudySettings

        self.assertFalse(UserStudySettings.objects.filter(user=self.user).exists())
        self.client.get("/")
        self.assertTrue(UserStudySettings.objects.filter(user=self.user).exists())

    def test_home_creates_user_profile(self):
        """Home view should auto-create UserProfile."""
        from core.models import UserProfile

        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())
        self.client.get("/")
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_home_creates_exam_goal(self):
        """Home view should auto-create ExamGoal."""
        from core.models import ExamGoal

        self.assertFalse(ExamGoal.objects.filter(user=self.user).exists())
        self.client.get("/")
        self.assertTrue(ExamGoal.objects.filter(user=self.user).exists())

    def test_home_landing_for_anonymous(self):
        """Home should render landing page for unauthenticated users."""
        client = Client()
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        # Verify render was called with landingpage.html
        self._mock_render.assert_called()
        last_call_args = self._mock_render.call_args_list[-1]
        self.assertEqual(last_call_args[0][1], "landingpage.html")

    def test_home_dashboard_for_authenticated(self):
        """Home should render dashboard (home.html) for logged-in users."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        # Verify render was called with home.html
        last_call_args = self._mock_render.call_args_list[-1]
        self.assertEqual(last_call_args[0][1], "home.html")

    def test_repeated_home_visits_no_duplicate(self):
        """Visiting home twice should not create duplicate related models."""
        from streak.models import StreakStat

        self.client.get("/")
        self.client.get("/")
        self.assertEqual(
            StreakStat.objects.filter(user=self.user).count(),
            1,
        )


# ===========================================================================
#  6. StreakMiddleware
# ===========================================================================
class StreakMiddlewareTests(TestCase):
    """Test that StreakMiddleware auto-registers login streak.

    Uses /api/v1/auth/csrf (auth=None, always 200) as a lightweight
    endpoint that goes through the full Django middleware stack
    without needing template rendering.
    """

    SAFE_URL = API_CSRF  # No auth required, no templates

    def setUp(self):
        self.user = User.objects.create_user(
            username="streakuser",
            email="streak@example.com",
            password="password123",
        )
        self.client.force_login(self.user)

    @patch("streak.services.register_login_streak")
    def test_middleware_calls_register(self, mock_register):
        """Middleware should call register_login_streak for authenticated requests."""
        self.client.get(self.SAFE_URL)
        mock_register.assert_called_with(self.user)

    @patch("streak.services.register_login_streak")
    def test_middleware_skips_static(self, mock_register):
        """Middleware should skip static file paths."""
        self.client.get("/static/somefile.css")
        mock_register.assert_not_called()

    @patch("streak.services.register_login_streak")
    def test_middleware_skips_anonymous(self, mock_register):
        """Middleware should skip anonymous (non-authenticated) requests."""
        client = Client()  # No login
        client.get(self.SAFE_URL)
        mock_register.assert_not_called()

    @patch("streak.services.register_login_streak", side_effect=Exception("DB error"))
    def test_middleware_swallows_errors(self, mock_register):
        """Middleware should not break the request on streak errors."""
        resp = self.client.get(self.SAFE_URL)
        # Should still get a successful response despite streak error
        self.assertEqual(resp.status_code, 200)


# ===========================================================================
#  7. SocialAccountAdapter — Google OAuth Merge
# ===========================================================================
class SocialAccountAdapterTests(TestCase):
    """Test SocialAccountAdapter.pre_social_login — merging Google login
    with existing email account."""

    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.create_user(
            username="existing",
            email="shared@example.com",
            password="password123",
        )

    def test_merge_google_with_existing_email(self):
        """
        When a Google login arrives for an email that already has an account,
        the adapter should connect the social account to the existing user.
        """
        from core.adapters import SocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin, SocialAccount

        adapter = SocialAccountAdapter()

        # Build a mock sociallogin with a new user that has the same email
        new_user = User(email="shared@example.com")
        social_account = SocialAccount(provider="google", uid="123456")

        sociallogin = MagicMock(spec=SocialLogin)
        sociallogin.is_existing = False
        sociallogin.user = new_user

        request = self.factory.get("/accounts/google/login/callback/")

        adapter.pre_social_login(request, sociallogin)

        # Should have called connect() with the existing user
        sociallogin.connect.assert_called_once_with(request, self.existing_user)

    def test_skip_if_already_existing(self):
        """Should skip merging if social account already exists."""
        from core.adapters import SocialAccountAdapter

        adapter = SocialAccountAdapter()

        sociallogin = MagicMock()
        sociallogin.is_existing = True

        request = self.factory.get("/callback/")
        adapter.pre_social_login(request, sociallogin)

        sociallogin.connect.assert_not_called()

    def test_skip_if_no_email(self):
        """Should skip merging if the social login has no email."""
        from core.adapters import SocialAccountAdapter

        adapter = SocialAccountAdapter()

        new_user = MagicMock()
        new_user.email = ""

        sociallogin = MagicMock()
        sociallogin.is_existing = False
        sociallogin.user = new_user

        request = self.factory.get("/callback/")
        adapter.pre_social_login(request, sociallogin)

        sociallogin.connect.assert_not_called()

    def test_skip_if_email_not_in_db(self):
        """Should skip if email doesn't match any existing user."""
        from core.adapters import SocialAccountAdapter

        adapter = SocialAccountAdapter()

        new_user = MagicMock()
        new_user.email = "newperson@example.com"

        sociallogin = MagicMock()
        sociallogin.is_existing = False
        sociallogin.user = new_user

        request = self.factory.get("/callback/")
        adapter.pre_social_login(request, sociallogin)

        sociallogin.connect.assert_not_called()


# ===========================================================================
#  8. Signup + Login Integration (E2E-like)
# ===========================================================================
class SignupThenLoginIntegrationTests(TestCase):
    """End-to-end: signup → logout → login → /me."""

    def test_full_flow(self):
        """Register → access /me → logout → re-login → access /me again."""
        # 1. Signup
        resp = self.client.post(
            API_SIGNUP,
            data=json.dumps({
                "email": "e2e@example.com",
                "password1": "securepass123",
                "password2": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)

        # 2. Access /me — should work (JWT cookies set from signup)
        resp = self.client.get(API_ME)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "e2e@example.com")

        # 3. Logout
        resp = self.client.post(API_LOGOUT, content_type="application/json")
        self.assertEqual(resp.status_code, 200)

        # 4. /me should fail now
        resp = self.client.get(API_ME)
        self.assertIn(resp.status_code, [401, 403])

        # 5. Re-login
        resp = self.client.post(
            API_LOGIN,
            data=json.dumps({
                "email": "e2e@example.com",
                "password": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # 6. /me should work again
        resp = self.client.get(API_ME)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "e2e@example.com")


# ===========================================================================
#  9. Allauth Settings Verification
# ===========================================================================
class AllAuthSettingsTests(TestCase):
    """Verify allauth settings are configured correctly."""

    def test_email_verification_mandatory(self):
        from django.conf import settings
        self.assertEqual(settings.ACCOUNT_EMAIL_VERIFICATION, "mandatory")

    def test_login_methods_email_only(self):
        from django.conf import settings
        self.assertEqual(settings.ACCOUNT_LOGIN_METHODS, {"email"})

    def test_login_redirect_to_home(self):
        from django.conf import settings
        self.assertEqual(settings.LOGIN_REDIRECT_URL, "/")

    def test_logout_redirect_to_home(self):
        from django.conf import settings
        self.assertEqual(settings.ACCOUNT_LOGOUT_REDIRECT_URL, "/")

    def test_social_adapter_configured(self):
        from django.conf import settings
        self.assertEqual(
            settings.SOCIALACCOUNT_ADAPTER,
            "core.adapters.SocialAccountAdapter",
        )

    def test_google_provider_configured(self):
        from django.conf import settings
        self.assertIn("google", settings.SOCIALACCOUNT_PROVIDERS)

    def test_jwt_settings_present(self):
        from django.conf import settings
        self.assertIn("ACCESS_TOKEN_LIFETIME", settings.SIMPLE_JWT)
        self.assertIn("REFRESH_TOKEN_LIFETIME", settings.SIMPLE_JWT)


# ===========================================================================
# 10. JWT Helper Functions
# ===========================================================================
class JWTHelperFunctionTests(TestCase):
    """Test jwt_auth helper functions directly."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="helper",
            email="helper@example.com",
            password="password123",
        )

    def test_get_tokens_for_user(self):
        """get_tokens_for_user should return access and refresh tokens."""
        from config.jwt_auth import get_tokens_for_user

        tokens = get_tokens_for_user(self.user)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)
        self.assertTrue(len(tokens["access"]) > 20)
        self.assertTrue(len(tokens["refresh"]) > 20)

    def test_refresh_access_token(self):
        """refresh_access_token should generate a new access token."""
        from config.jwt_auth import get_tokens_for_user, refresh_access_token

        tokens = get_tokens_for_user(self.user)
        new_access = refresh_access_token(tokens["refresh"])
        self.assertIsNotNone(new_access)
        self.assertTrue(len(new_access) > 20)

    def test_refresh_with_invalid_token(self):
        """refresh_access_token should return None for invalid token."""
        from config.jwt_auth import refresh_access_token

        result = refresh_access_token("invalid.token.string")
        self.assertIsNone(result)

    def test_set_and_clear_cookies(self):
        """set_jwt_cookies / clear_jwt_cookies should manage cookies."""
        from django.http import HttpResponse
        from config.jwt_auth import set_jwt_cookies, clear_jwt_cookies

        response = HttpResponse()
        response = set_jwt_cookies(response, self.user)

        # Both cookies should be set
        self.assertIn(ACCESS_COOKIE, response.cookies)
        self.assertIn(REFRESH_COOKIE, response.cookies)

        # Clear
        response = clear_jwt_cookies(response)
        # After clearing, cookies should have max_age=0 or empty value
        self.assertEqual(response.cookies[ACCESS_COOKIE]["max-age"], 0)
        self.assertEqual(response.cookies[REFRESH_COOKIE]["max-age"], 0)
