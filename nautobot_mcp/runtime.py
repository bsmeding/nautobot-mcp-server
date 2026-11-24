"""Shared client and settings for the running MCP process.

Tool modules read it from here so they don't import the server module.
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
    """Store the client. Called when the server starts."""
    global _client
    _client = client


def get_client() -> NautobotClient:
    """Active client. Raises when the server has not started."""
    if _client is None:
        raise RuntimeError(
            "NautobotClient is not initialized. The MCP server must be "
            "started via nautobot_mcp.server.main()."
        )
    return _client


def set_settings(settings: NautobotMcpSettings) -> None:
    """Store the resolved settings."""
    global _settings
    _settings = settings


def get_settings() -> NautobotMcpSettings:
    """Resolved settings. Raises when they were not loaded."""
    if _settings is None:
        raise RuntimeError("Settings not initialized.")
    return _settings


def set_enabled_plugins(keys: tuple[str, ...]) -> None:
    """Remember which plugin tools were registered."""
    global _enabled_plugins
    _enabled_plugins = keys


def get_enabled_plugins() -> tuple[str, ...]:
    """Plugin keys registered on this process."""
    return _enabled_plugins


def reset() -> None:
    """Clear client, settings, and plugin list. Used by tests."""
    global _client, _settings, _enabled_plugins
    _client = None
    _settings = None
    _enabled_plugins = ()
