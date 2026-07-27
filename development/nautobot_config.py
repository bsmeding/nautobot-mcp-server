"""Nautobot configuration for the local development environment.

Reads most settings from environment variables (see development.env /
creds.env). Enables this app and configures it via PLUGINS_CONFIG.
"""

import os

from nautobot.core.settings import *  # noqa: F401,F403
from nautobot.core.settings_funcs import is_truthy


def _env(key, default=None):
    return os.environ.get(key, default)


ALLOWED_HOSTS = _env("NAUTOBOT_ALLOWED_HOSTS", "*").split(" ")
SECRET_KEY = _env("NAUTOBOT_SECRET_KEY", "dev-secret-key")
DEBUG = is_truthy(_env("NAUTOBOT_DEBUG", "False"))

DATABASES = {
    "default": {
        "NAME": _env("NAUTOBOT_DB_NAME", "nautobot"),
        "USER": _env("NAUTOBOT_DB_USER", "nautobot"),
        "PASSWORD": _env("NAUTOBOT_DB_PASSWORD", ""),
        "HOST": _env("NAUTOBOT_DB_HOST", "localhost"),
        "PORT": _env("NAUTOBOT_DB_PORT", "5432"),
        "CONN_MAX_AGE": 300,
        "ENGINE": _env("NAUTOBOT_DB_ENGINE", "django.db.backends.postgresql"),
    }
}

redis_password = _env("NAUTOBOT_REDIS_PASSWORD", "")
redis_host = _env("NAUTOBOT_REDIS_HOST", "localhost")
redis_port = _env("NAUTOBOT_REDIS_PORT", "6379")
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{redis_url}/1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
CELERY_BROKER_URL = f"{redis_url}/0"

# --- Enable this app -------------------------------------------------------
PLUGINS = ["nautobot_mcp_server"]

PLUGINS_CONFIG = {
    "nautobot_mcp_server": {
        "nautobot_url": _env("NAUTOBOT_URL", "http://localhost:8080"),
        "nautobot_token": _env("NAUTOBOT_TOKEN", ""),
        "allow_writes": is_truthy(_env("NAUTOBOT_MCP_ALLOW_WRITES", "False")),
        "plugins": _env("NAUTOBOT_MCP_PLUGINS", "auto").split(","),
        "log_level": _env("NAUTOBOT_MCP_LOG_LEVEL", "INFO"),
    }
}
