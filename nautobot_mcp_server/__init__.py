"""Nautobot MCP Server.

A Model Context Protocol (MCP) server that exposes Nautobot's built-in
REST and GraphQL APIs as tools for LLMs and AI assistants.

Can be used in two ways:

1. As a Nautobot app (installed in a Nautobot environment): set
   ``PLUGINS = ["nautobot_mcp_server"]`` and configure ``PLUGINS_CONFIG``.
2. As a standalone MCP stdio server via the ``nautobot-mcp-server`` console
   script, configured with ``NAUTOBOT_URL`` / ``NAUTOBOT_TOKEN`` env vars.
"""

from importlib import metadata

__all__ = ["__version__", "config"]


def _resolve_version() -> str:
    """Resolve the installed package version, with fallbacks."""
    for dist_name in ("nautobot-mcp-server", "nautobot-app-mcp-server", __name__):
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            continue
    return "0.0.0"


__version__ = _resolve_version()


# Expose ``config`` only when Nautobot is available (i.e. when imported
# inside a Nautobot/Django environment). This lets the standalone MCP
# stdio server run in environments where Nautobot is not installed.
try:
    from .apps import NautobotMcpServerConfig

    config = NautobotMcpServerConfig
except Exception:  # pragma: no cover - fallback for non-Nautobot environments
    config = None  # type: ignore[assignment]
