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

# Security Hardening for Production
if not DEBUG:
    # Force HTTPS
    SECURE_SSL_REDIRECT = True
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Browser security headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    # Proxy SSL Header (Critical for Nginx/Azure to avoid infinite redirects)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"] if DEBUG else []

csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [x.strip() for x in csrf.split(",") if x.strip()]

AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME", "")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY", "")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "media")
AZURE_AUDIO_CONTAINER = os.getenv("AZURE_AUDIO_CONTAINER", "audio")
# Tăng timeout cho Azure Storage (django-storages)
AZURE_CONNECTION_TIMEOUT = 600  # giây
AZURE_READ_TIMEOUT = 6000        # giây
# Giảm kích thước block và tăng song song để giảm timeout khi upload file lớn
# (sử dụng các option mà django-storages chuyển vào BlobServiceClient)
AZURE_MAX_BLOCK_SIZE = 1024 * 1024  # 1MB mỗi block
AZURE_MAX_SINGLE_PUT_SIZE = 8 * 1024 * 1024  # 8MB
AZURE_MAX_CONCURRENCY = 4  # số kết nối song song khi upload
# (tùy chọn) tăng retry, giảm xác suất timeout mạng tạm thời

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
# Audio files are stored in a separate container
AUDIO_BASE_URL = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_AUDIO_CONTAINER}/"

# Application definition
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'nested_admin',

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
    'common',  # Common components and utilities
    'core',
    'vocab',
    'kanji',
    'video',
    'exam',
    'streak',
    'import_export',
    'grammar',
    'todos',
    'payment',
    'feedback',
    'wallet',
    'analytics',
    'rest_framework',
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
    
    # Analytics tracking
    'analytics.middleware.AnalyticsMiddleware',
    
    # Streak tracking - tự động tính streak khi user login
    'streak.middleware.StreakMiddleware',
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
                'common.context_processors.navigation_items',  # Navigation menu items
                'common.context_processors.footer_data',  # Footer data
                'common.context_processors.landing_page_data',  # Landing page data
                'common.context_processors.sidebar_data',  # Sidebar layout data
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
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[DailyFluent] "


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

# Payment Settings
# Bank Transfer
BANK_ACCOUNT_NAME = os.getenv("BANK_ACCOUNT_NAME", "CONG TY TNHH DAILYFLUENT")
BANK_ACCOUNT_NUMBER = os.getenv("BANK_ACCOUNT_NUMBER", "")
BANK_NAME = os.getenv("BANK_NAME", "Vietcombank")
BANK_BRANCH = os.getenv("BANK_BRANCH", "")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Increase limits for huge forms (TOEIC full tests with 200 questions)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 # 10MB

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
