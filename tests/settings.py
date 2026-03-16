"""Minimal Django settings for running django-watch tests.

Uses an in-memory SQLite database so that ``connection.queries`` is
populated (requires ``DEBUG = True``) without touching the filesystem.
"""

SECRET_KEY = "django-watch-test-secret-key-not-for-production"

DEBUG = True  # Required for connection.queries to be recorded.

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_watch",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MIDDLEWARE = [
    "django_watch.middleware.WatchMiddleware",
]

ROOT_URLCONF = "tests.urls"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
