from pathlib import Path
import os 
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = os.getenv("ENV_FILE")
if ENV_FILE and Path(ENV_FILE).exists():
    load_dotenv(ENV_FILE)
else:
    shared_env = Path("/home/mtmanh/apps/DailyFluent/shared/.env")
    if shared_env.exists():
        load_dotenv(shared_env)
    else:
        load_dotenv(BASE_DIR / ".env") 

SECRET_KEY = os.getenv("SECRET_KEY", "dev")

def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").lower() in ("1", "true", "yes", "on")

DEBUG = env_bool("DEBUG", default=False)

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"] if DEBUG else []

csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [x.strip() for x in csrf.split(",") if x.strip()]

AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME", "")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY", "")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "media")

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", "/home/mtmanh/apps/DailyFluent/shared/staticfiles"))
STATICFILES_DIRS = [BASE_DIR / "static"]

SOCIALACCOUNT_LOGIN_ON_GET = True

STORAGES = {
    "default": {"BACKEND": "config.storage_backends.AzureMediaStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

if not DEBUG and (not AZURE_ACCOUNT_NAME or not AZURE_ACCOUNT_KEY):
    raise RuntimeError("Azure storage env missing (AZURE_ACCOUNT_NAME/AZURE_ACCOUNT_KEY)")

MEDIA_URL = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/"

# Application definition
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'storages',

    # must have for django-allauth
    'django.contrib.sites',

    # django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'tailwind',
    'theme',
    'core',
    'vocab',
    'kanji',
    'video',
    'exam',
    'streak',
    'import_export',
    'grammar',
]

TAILWIND_APP_NAME = 'theme'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # BẮT BUỘC cho django-allauth (bản mới)
    'allauth.account.middleware.AccountMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Check /home/mtmanh/apps/DailyFluent/shared/.env")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    # để Django admin login vẫn dùng backend mặc định
    'django.contrib.auth.backends.ModelBackend',

    # backend của allauth
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_ADAPTER = "core.adapters.SocialAccountAdapter"

# Cấu hình Google OAuth
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        },
        # Tin cậy email đã verify từ Google để gộp tài khoản cùng email
        "VERIFIED_EMAIL": True,
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "offline",
        },
    }
}


LANGUAGE_CODE = 'en-us'
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True
SITE_ID = 1


LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Đăng nhập bằng email (allauth >= 65.4)
ACCOUNT_LOGIN_METHODS = {"email"} 
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"] 

ACCOUNT_EMAIL_VERIFICATION = "mandatory"  
ACCOUNT_CONFIRM_EMAIL_ON_GET = True      

ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv("ACCOUNT_DEFAULT_HTTP_PROTOCOL", "http") 
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[DailyFluent] " :contentReference[oaicite:6]{index=6}


# === Email settings === 
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))

# .env để "True"/"False" dạng chuỗi, convert sang bool
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False") == "True"

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER or "no-reply@dailyfluent.local",
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
