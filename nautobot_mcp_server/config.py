"""Configuration loading for the Nautobot MCP server.

Resolution order (highest priority first):

1. Explicit kwargs passed to :func:`load_settings`.
2. Environment variables (``NAUTOBOT_URL``, ``NAUTOBOT_TOKEN``,
   ``NAUTOBOT_VERIFY_SSL``, ``NAUTOBOT_CA_BUNDLE``, ``NAUTOBOT_TIMEOUT``,
   ``NAUTOBOT_MAX_PAGINATION_RECORDS``, ``NAUTOBOT_ALLOW_WRITES``,
   ``NAUTOBOT_TENANT_SCOPE``, ``NAUTOBOT_TENANT_GROUP_SCOPE``,
   ``NAUTOBOT_MCP_PLUGINS``, ``MCP_LOG_LEVEL``).
3. ``settings.PLUGINS_CONFIG["nautobot_mcp_server"]`` when running inside
   Nautobot/Django.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


def _coerce_str_tuple(value: Any) -> tuple[str, ...]:
    """Coerce a value into a tuple of non-empty strings.

    Accepts a list/tuple, or a comma-separated string (handy for env vars
    like ``NAUTOBOT_TENANT_SCOPE=acme,globex``).
    """
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        items: list[Any] = list(value)
    else:
        items = str(value).split(",")
    return tuple(s.strip() for s in (str(i) for i in items) if s.strip())


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "":
        return default
    return text not in {"0", "false", "no", "off"}


def _from_django_settings() -> dict[str, Any]:
    """Pull plugin config from Nautobot's PLUGINS_CONFIG, if available."""
    try:
        from django.conf import settings  # type: ignore[import-not-found]
    except ImportError:
        return {}
    try:
        plugins_config = getattr(settings, "PLUGINS_CONFIG", {}) or {}
        cfg = plugins_config.get("nautobot_mcp_server", {}) or {}
        return dict(cfg)
    except Exception:
        return {}


@dataclass(frozen=True)
class NautobotMcpSettings:
    """Resolved runtime settings for the MCP server."""

    url: str
    token: str
    verify_ssl: bool | str = True
    request_timeout: float = 30.0
    max_pagination_records: int = 5000
    allow_writes: bool = False
    log_level: str = "INFO"
    tenant_scope: tuple[str, ...] = ()
    tenant_group_scope: tuple[str, ...] = ()
    plugins: tuple[str, ...] = ("auto",)

    @property
    def tenant_scoped(self) -> bool:
        """True when any tenant or tenant-group restriction is configured."""
        return bool(self.tenant_scope or self.tenant_group_scope)

    def redacted(self) -> dict[str, Any]:
        """Return a dict suitable for logging (token masked)."""
        token_preview = (
            f"{self.token[:4]}…{self.token[-4:]}" if len(self.token) >= 8 else "<set>"
        )
        return {
            "url": self.url,
            "token": token_preview,
            "verify_ssl": self.verify_ssl,
            "request_timeout": self.request_timeout,
            "max_pagination_records": self.max_pagination_records,
            "allow_writes": self.allow_writes,
            "log_level": self.log_level,
            "tenant_scope": list(self.tenant_scope),
            "tenant_group_scope": list(self.tenant_group_scope),
            "plugins": list(self.plugins),
        }


def load_settings(**overrides: Any) -> NautobotMcpSettings:
    """Resolve settings from kwargs > env > Django PLUGINS_CONFIG."""
    django_cfg = _from_django_settings()

    def _pick(key: str, env: str, *, default: Any = None) -> Any:
        if overrides.get(key) not in (None, ""):
            return overrides[key]
        env_val = os.getenv(env)
        if env_val not in (None, ""):
            return env_val
        django_val = django_cfg.get(_django_key(key))
        if django_val not in (None, ""):
            return django_val
        return default

    url = str(_pick("url", "NAUTOBOT_URL", default="") or "").rstrip("/")
    token = str(_pick("token", "NAUTOBOT_TOKEN", default="") or "")

    # SSL verification: bool, or path to CA bundle, or False to disable.
    ca_bundle = (
        overrides.get("ca_bundle")
        or os.getenv("NAUTOBOT_CA_BUNDLE")
        or django_cfg.get("ca_bundle")
        or ""
    )
    if "verify_ssl" in overrides and overrides["verify_ssl"] is not None:
        verify_ssl: bool | str = overrides["verify_ssl"]
    elif ca_bundle:
        verify_ssl = str(ca_bundle)
    elif os.getenv("NAUTOBOT_VERIFY_SSL") is not None:
        verify_ssl = _coerce_bool(os.getenv("NAUTOBOT_VERIFY_SSL"), True)
    else:
        verify_ssl = bool(django_cfg.get("verify_ssl", True))

    request_timeout = float(
        _pick("request_timeout", "NAUTOBOT_TIMEOUT", default=30.0) or 30.0
    )
    max_pagination_records = int(
        _pick(
            "max_pagination_records",
            "NAUTOBOT_MAX_PAGINATION_RECORDS",
            default=5000,
        )
        or 5000
    )
    allow_writes = _coerce_bool(
        _pick("allow_writes", "NAUTOBOT_ALLOW_WRITES", default=False), False
    )
    log_level = str(
        _pick("log_level", "MCP_LOG_LEVEL", default="INFO") or "INFO"
    ).upper()
    tenant_scope = _coerce_str_tuple(
        _pick("tenant_scope", "NAUTOBOT_TENANT_SCOPE", default=())
    )
    tenant_group_scope = _coerce_str_tuple(
        _pick("tenant_group_scope", "NAUTOBOT_TENANT_GROUP_SCOPE", default=())
    )
    plugins = _coerce_str_tuple(
        _pick("plugins", "NAUTOBOT_MCP_PLUGINS", default="auto")
    ) or ("auto",)

    if not url:
        raise ValueError(
            "Nautobot URL is not configured. Set the NAUTOBOT_URL env var "
            "or PLUGINS_CONFIG['nautobot_mcp_server']['nautobot_url']."
        )
    if not token:
        raise ValueError(
            "Nautobot API token is not configured. Set the NAUTOBOT_TOKEN env "
            "var or PLUGINS_CONFIG['nautobot_mcp_server']['nautobot_token']."
        )

    return NautobotMcpSettings(
        url=url,
        token=token,
        verify_ssl=verify_ssl,
        request_timeout=request_timeout,
        max_pagination_records=max_pagination_records,
        allow_writes=allow_writes,
        log_level=log_level,
        tenant_scope=tenant_scope,
        tenant_group_scope=tenant_group_scope,
        plugins=tuple(p.lower().replace("-", "_") for p in plugins),
    )


def _django_key(key: str) -> str:
    """Map an internal setting name to the Django PLUGINS_CONFIG key."""
    return {
        "url": "nautobot_url",
        "token": "nautobot_token",
    }.get(key, key)
