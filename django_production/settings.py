import os
import re

import environ

env = environ.Env()

DJANGO_ENV = env.str("DJANGO_ENV", "dev")

# Allow running webserver from manage.py
INSTALLED_APPS.append("django_webserver")

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

if DJANGO_ENV == "production":
    DEBUG = env.bool("DEBUG", default=False)
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

    # Staticfiles
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    # Match filename with 12 hex digits before the extension
    WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: re.match(  # noqa: E731
        r"^.+\.[0-9a-f]{12}\..+$", url
    )
