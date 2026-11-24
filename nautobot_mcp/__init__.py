"""Nautobot MCP server — REST and GraphQL as tools for an LLM.

Nautobot app: PLUGINS = ["nautobot_mcp"].
Standalone: nautobot-mcp with NAUTOBOT_URL and NAUTOBOT_TOKEN.
"""

from importlib import metadata

__all__ = ["__version__", "config"]


def _resolve_version() -> str:
    """Installed package version, or 0.0.0 when none of the names match."""
    for dist_name in ("nautobot-mcp", "nautobot-mcp-server", "nautobot-app-mcp-server", __name__):
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            continue
    return "0.0.0"


__version__ = _resolve_version()


# config is the Nautobot app class. Skip it when Nautobot is not installed
# so `nautobot-mcp` still starts on a machine that only has this package.
try:
    from .apps import NautobotMcpServerConfig

    config = NautobotMcpServerConfig
except Exception:  # pragma: no cover - fallback for non-Nautobot environments
    config = None  # type: ignore[assignment]
