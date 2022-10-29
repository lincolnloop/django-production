import os
import re
from pathlib import Path

import environ

env = environ.FileAwareEnv()

DJANGO_ENV = env.str("DJANGO_ENV", "dev")

INSTALLED_APPS.extend(
    [
        "django_webserver",  # Allow running webserver from manage.py
        "whitenoise.runserver_nostatic",  # Use whitenoise with runserver
    ]
)

# Insert whitenoise middleware
try:
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )
except ValueError:
    MIDDLEWARE.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")

# skip host checking for healthcheck URLs
MIDDLEWARE.insert(0, "django_alive.middleware.healthcheck_bypass_host_check")

X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = "same-origin"

# Staticfiles
staticfiles_parent_dir = Path(__file__).resolve().parents[$settings_depth]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_DIRS = [staticfiles_parent_dir / "static"]
STATIC_ROOT = staticfiles_parent_dir / "static_collected"
WHITENOISE_AUTOREFRESH = True
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: re.match(  # noqa: E731
    r"^.+\.[0-9a-f]{12}\..+$", url
)

if DJANGO_ENV == "production":
    DEBUG = env.bool("DEBUG", default=False)
    WHITENOISE_AUTOREFRESH = False
    SECRET_KEY = env.str("SECRET_KEY")
    if "DATABASE_URL" in os.environ:
        DATABASES = {"default": env.db("DATABASE_URL")}
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
    # Load cache from CACHE_URL or REDIS_URL
    if "CACHE_URL" in os.environ:
        CACHES = {"default": env.cache("CACHE_URL")}
    elif "REDIS_URL" in os.environ:
        CACHES = {"default": env.cache("REDIS_URL")}
    # Security
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HTTPS only behind a proxy that terminates SSL/TLS
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^-/"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_PRELOAD = True
    # Only set this to True if you are certain that all subdomains of your domain should be served exclusively via SSL.
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
    )
