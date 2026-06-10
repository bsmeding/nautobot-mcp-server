"""Process-wide runtime state for the MCP server.

The MCP tool functions need access to a shared :class:`NautobotClient`
instance. We hold it here so tool modules can grab it lazily without
creating import cycles with the server module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import NautobotClient
    from .config import NautobotMcpSettings


_client: NautobotClient | None = None
_settings: NautobotMcpSettings | None = None
_enabled_plugins: tuple[str, ...] = ()


def set_client(client: NautobotClient) -> None:
    """Register the active NautobotClient (called from server lifespan)."""
    global _client
    _client = client


def get_client() -> NautobotClient:
    """Return the active client or raise if not initialized."""
    if _client is None:
        raise RuntimeError(
            "NautobotClient is not initialized. The MCP server must be "
            "started via nautobot_mcp_server.server.main()."
        )
    return _client


def set_settings(settings: NautobotMcpSettings) -> None:
    """Register the active settings."""
    global _settings
    _settings = settings


def get_settings() -> NautobotMcpSettings:
    """Return the active settings or raise if not initialized."""
    if _settings is None:
        raise RuntimeError("Settings not initialized.")
    return _settings


def set_enabled_plugins(keys: tuple[str, ...]) -> None:
    """Record which plugin integrations were enabled at registration."""
    global _enabled_plugins
    _enabled_plugins = keys


def get_enabled_plugins() -> tuple[str, ...]:
    """Return the plugin integrations enabled for this server."""
    return _enabled_plugins


def reset() -> None:
    """Clear runtime state (useful for tests)."""
    global _client, _settings, _enabled_plugins
    _client = None
    _settings = None
    _enabled_plugins = ()
