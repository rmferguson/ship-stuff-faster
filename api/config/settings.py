"""
Django settings for ship-stuff-faster API.

Environment is validated at startup via pydantic-settings. Bad config doesn't boot.
__debug__ is the dev/prod discriminator — run with -O (PYTHONOPTIMIZE=1) in production.
"""

from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

MANAGE_FILE = "manage.py"
ENV_FILENAME = ".env"

SETTINGS_DIR_ABS_PATH = Path(__file__).resolve().parent
BASE_DIR_ABS_PATH = SETTINGS_DIR_ABS_PATH.parent

PROJECT_ROOT = SETTINGS_DIR_ABS_PATH
while PROJECT_ROOT.parent != PROJECT_ROOT and not (PROJECT_ROOT / MANAGE_FILE).exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

BASE_DIR = BASE_DIR_ABS_PATH.relative_to(PROJECT_ROOT)
ENV_FILE_PATH = PROJECT_ROOT / ENV_FILENAME

DEV_DEFAULT_SECRET_KEY = "dev-secret-key-at-least-32-bytes-long-for-jwt"


class Env(BaseSettings):
    """All environment variables. Validated at startup — missing required vars raise immediately."""

    on_local: bool = True
    on_staging: bool = False
    on_live: bool = False

    secret_key: str = DEV_DEFAULT_SECRET_KEY

    database_name: str = "ssf_db"
    database_user: str = "ssf_app"
    database_password: str = "incorrectpassword"
    database_host: str = "localhost"
    database_port: str = "5432"

    allowed_hosts: str = ""
    frontend_base_url: str = ""

    # Email: empty = console backend (dev). Set for production SMTP.
    email_backend: str = ""
    email_host: str = ""
    email_port: str = "587"
    email_host_user: str = ""
    email_host_password: str = ""
    email_use_tls: bool = True
    default_from_email: str = "webmaster@localhost"

    def get_allowed_hosts(self) -> list[str]:
        if not self.allowed_hosts:
            return []
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH if ENV_FILE_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


environ = Env()

# --- Boot validation ---

if environ.on_local:
    assert not environ.on_live, "on_live set while on_local is set"
    assert not environ.on_staging, "on_staging set while on_local is set"
else:
    if __debug__:
        raise RuntimeError("__debug__ is True on a non-local environment. Set PYTHONOPTIMIZE=1 in production.")
    if environ.secret_key == DEV_DEFAULT_SECRET_KEY:
        raise RuntimeError("DEV_DEFAULT_SECRET_KEY in use on non-local environment.")
    if environ.on_staging and environ.on_live:
        raise RuntimeError("on_staging and on_live cannot both be True.")

if not any((environ.on_local, environ.on_staging, environ.on_live)):
    raise RuntimeError("No environment set. Set on_local, on_staging, or on_live.")

PYJWT_MIN_KEY_BYTES = 32
if len(environ.secret_key.encode()) < PYJWT_MIN_KEY_BYTES:
    raise RuntimeError(f"secret_key must be at least {PYJWT_MIN_KEY_BYTES} bytes for HS256.")

ALLOWED_HOSTS: list[str] = environ.get_allowed_hosts() if not __debug__ else []
if not __debug__ and not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS is empty on a non-local environment.")

FRONTEND_BASE_URL: str = environ.frontend_base_url
if not FRONTEND_BASE_URL:
    if __debug__:
        FRONTEND_BASE_URL = "http://localhost:3000"
    elif environ.on_staging:
        FRONTEND_BASE_URL = ""  # set via env on staging
    elif environ.on_live:
        FRONTEND_BASE_URL = ""  # set via env on live
if not FRONTEND_BASE_URL:
    raise RuntimeError("FRONTEND_BASE_URL is not set.")

del PYJWT_MIN_KEY_BYTES
del DEV_DEFAULT_SECRET_KEY

if __debug__:
    print("Django starting in development mode (__debug__ = True)")
else:
    print("Django starting in production mode (__debug__ = False)")

# --- Core settings ---

SECRET_KEY = environ.secret_key
SECRET_KEY_FALLBACKS: list[str] = []
DEBUG = __debug__

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    # Token revocation (blacklist on rotation). Separate app because simplejwt ships it
    # as opt-in — adding it enables the BLACKLIST_AFTER_ROTATION behaviour below.
    "rest_framework_simplejwt.token_blacklist",
    "core.apps.CoreConfig",
    "apps.users.apps.UsersConfig",
]

# Middleware order matters:
# - WhiteNoiseMiddleware must be directly after SecurityMiddleware to serve static files
#   before any auth checks run.
# - CorsMiddleware must be before CommonMiddleware (and anything that can short-circuit
#   a request) so preflight OPTIONS responses include CORS headers.
# - Session + CSRF middleware are kept for Django admin. API endpoints use JWT and don't
#   need them, but removing them breaks the admin login flow.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_ROOT / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ.database_name,
        "USER": environ.database_user,
        "PASSWORD": environ.database_password,
        "HOST": environ.database_host,
        "PORT": environ.database_port,
        **({} if __debug__ else {"OPTIONS": {"sslmode": "require"}}),
    }
}

AUTH_USER_MODEL = "users.User"

# Django's default backend authenticates by username. EmailBackend replaces it so
# users log in with email + password instead.
AUTHENTICATION_BACKENDS = [
    "apps.users.backends.EmailBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # CompressedManifestStaticFilesStorage appends a content hash to filenames so browsers
    # can cache static files indefinitely without stale-file bugs after deploys.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --- Email ---

if environ.email_backend:
    EMAIL_BACKEND = environ.email_backend
    EMAIL_HOST = environ.email_host
    EMAIL_PORT = int(environ.email_port)
    EMAIL_HOST_USER = environ.email_host_user
    EMAIL_HOST_PASSWORD = environ.email_host_password
    EMAIL_USE_TLS = environ.email_use_tls
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = environ.default_from_email
# Django's PasswordResetTokenGenerator uses this to expire links. 3 h is short enough
# to limit the window for a stolen link but long enough for a user in a slow email queue.
PASSWORD_RESET_TIMEOUT = 3 * 60 * 60  # 3 hours in seconds

# --- DRF ---

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # JWT-only: tokens arrive in the Authorization header so CSRF protection is not
    # required for API views. SessionAuthentication is intentionally omitted here —
    # admin uses its own session-based flow independently of DRF.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/hour",
        "user": "10000/hour",
        # Tighter limits on auth endpoints to mitigate brute-force attacks.
        "signup": "10/minute",
        "login": "5/minute",
    },
}

# --- SimpleJWT ---

# Access tokens are short-lived (15 min) so a leaked token expires quickly.
# Refresh tokens rotate on use: each refresh returns a new refresh token and blacklists
# the old one, so a stolen refresh token can only be used once before it's invalidated.
# BLACKLIST_AFTER_ROTATION requires rest_framework_simplejwt.token_blacklist in INSTALLED_APPS.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- CORS ---

CORS_ALLOWED_ORIGINS: list[str] = []
if __debug__:
    CORS_ALLOWED_ORIGINS += ["http://localhost:3000", "http://127.0.0.1:3000"]
if environ.on_staging or environ.on_live:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_BASE_URL)

# Must be True so the browser sends cookies (e.g. session) and the Authorization header
# on cross-origin requests from the Next.js frontend.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# --- CSRF ---

CSRF_TRUSTED_ORIGINS: list[str] = []
if __debug__:
    CSRF_TRUSTED_ORIGINS += ["http://localhost:3000", "http://127.0.0.1:3000"]
if environ.on_staging or environ.on_live:
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_BASE_URL)

# False so JavaScript can read the token and attach it as the X-CSRFToken header.
# Counterintuitive — normally HttpOnly cookies are safer — but the CSRF cookie is
# not a secret; it only needs to prove same-origin JS initiated the request.
CSRF_COOKIE_HTTPONLY = False
# "Lax" allows the cookie on top-level navigations (e.g. OAuth redirects) but blocks it
# on cross-site sub-requests. "Strict" would break password-reset links from email clients.
# "None" would require Secure=True everywhere and is unnecessary here.
CSRF_COOKIE_SAMESITE = "Lax"
# False: store CSRF state in a cookie, not the session. Session-based CSRF requires an
# active session, which JWT-authenticated requests don't have.
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = not environ.on_local

# --- Security ---

SESSION_COOKIE_SECURE = not environ.on_local
SECURE_SSL_REDIRECT = not environ.on_local
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Behind a reverse proxy (nginx, load balancer) Django sees all traffic as HTTP.
# This header tells Django to trust the proxy's claim that the original request was HTTPS.
# Not set locally — a client-supplied X-Forwarded-Proto header would be trusted otherwise.
if not __debug__ and not environ.on_local:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS tells browsers to refuse plain HTTP to this origin for SECURE_HSTS_SECONDS seconds.
# Enabling it on localhost would brick the dev environment until the timer expires.
# Starting at 90 s (not the full year) lets us verify HTTPS works before committing.
# Increase toward 31536000 once confident the cert and redirects are stable.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
if not __debug__ and (environ.on_staging or environ.on_live):
    SECURE_HSTS_SECONDS = 90
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- Logging ---

_LOG_DIR = PROJECT_ROOT / "_debug"
if __debug__:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _logging_handlers = {
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": str(_LOG_DIR / "api.log"),
            "mode": "a",
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    }
    _handler_names = ["console", "file"]
else:
    _logging_handlers = {
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "simple"},
    }
    _handler_names = ["console"]

LOGGING = {
    "version": 1,
    # False: keep Django's own loggers active. True would silence them and hide
    # request errors, migrations, and security warnings.
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{name}.{levelname} {asctime} — {message}", "style": "{"},
        "simple": {"format": "{levelname} {asctime}: {message}", "style": "{"},
    },
    "handlers": _logging_handlers,
    "root": {"level": "INFO", "handlers": _handler_names},
    "loggers": {"django": {"handlers": [], "propagate": True}},
}
