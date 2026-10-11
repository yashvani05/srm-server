import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return str(env(name, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    return int(env(name, str(default)))


DEBUG = env_bool("DJANGO_DEBUG", False)
TESTING = "test" in sys.argv

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "dev-only-insecure-secret-key-change-me-0123456789"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.trycloudflare.com").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "core",
    "accounts",
    "service_requests",
    "dashboard",
]

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
WSGI_APPLICATION = "config.wsgi.application"
APPEND_SLASH = False

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DB_SSL = env_bool("DB_SSL", False)
if env("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.parse(env("DATABASE_URL"), conn_max_age=60, ssl_require=DB_SSL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "srm_django"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = []

REDIS_URL = env("REDIS_URL", "redis://localhost:6379").rstrip("/")

if TESTING:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"{REDIS_URL}/1",
            "KEY_PREFIX": "srmdj",
            "KEY_FUNCTION": "core.cache.make_key",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 2,
                "SOCKET_TIMEOUT": 2,
            },
        }
    }

DASHBOARD_CACHE_TTL_SECONDS = env_int("DASHBOARD_CACHE_TTL_SECONDS", 60)

JWT_SECRET = env("JWT_SECRET") or SECRET_KEY
JWT_EXPIRES_SECONDS = env_int("JWT_EXPIRES_SECONDS", 3600)
LOGIN_RATE_LIMIT_MAX = env_int("LOGIN_RATE_LIMIT_MAX", 10)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["accounts.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "DEFAULT_THROTTLE_RATES": {"login": f"{LOGIN_RATE_LIMIT_MAX}/15min"},
    "NUM_PROXIES": env_int("TRUST_PROXY", 0),
    "UNAUTHENTICATED_USER": None,
}

CORS_ALLOWED_ORIGINS = [o.strip() for o in env("CORS_ORIGIN", "http://localhost:5173").split(",") if o.strip()]

SWAGGER_USER = env("SWAGGER_USER", "apidocs")
SWAGGER_PASS = env("SWAGGER_PASS")
if not SWAGGER_PASS:
    if DEBUG or TESTING:
        SWAGGER_PASS = "ApiDocs@12345"
    else:
        raise ImproperlyConfigured("SWAGGER_PASS must be set when DJANGO_DEBUG is false.")

SPECTACULAR_SETTINGS = {
    "TITLE": "Service Request Management API",
    "VERSION": "1.0.0",
    "DESCRIPTION": (
        "Internal service request tracking: submit requests, move them through Open → In Progress → Resolved, "
        "and monitor them on a dashboard.\n\n"
        "**Authentication.** Call `POST /auth/login`, then click **Authorize** and paste the returned `token` (Bearer JWT).\n\n"
        "**Roles.** `ADMIN` has full access. `EMPLOYEE` can create requests and can read/edit only their own "
        "(editing only while `OPEN`); other people's requests return 404.\n\n"
        "**Overdue.** A request is overdue when it has been `OPEN` or `IN_PROGRESS` for more than 24 hours in its "
        "current status (`statusChangedAt`). Resolved requests are never overdue.\n\n"
        "**Envelope.** Success: `{ success: true, message, data }`. Error: `{ success: false, message, errors[] }`."
    ),
    "SERVERS": [{"url": "/api/v1", "description": "This server"}],
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True, "displayRequestDuration": True, "docExpansion": "list"},
    "TAGS": [
        {"name": "Auth", "description": "Registration, login, logout and the current user"},
        {"name": "Service Requests", "description": "Create, read, update, delete and change the status of requests"},
        {"name": "Dashboard", "description": "Summary figures"},
        {"name": "System", "description": "Health check"},
    ],
}

OVERDUE_CHECK_INTERVAL_SECONDS = env_int("OVERDUE_CHECK_INTERVAL_SECONDS", 60)

CELERY_BROKER_URL = f"{REDIS_URL}/2"
CELERY_TASK_IGNORE_RESULT = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {
    "overdue-check": {
        "task": "service_requests.tasks.check_overdue",
        "schedule": float(OVERDUE_CHECK_INTERVAL_SECONDS),
    },
}
if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}

if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
