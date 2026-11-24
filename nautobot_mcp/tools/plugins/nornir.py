"""Nornir — backend used by Golden Config and Onboarding.

No task API of its own. This only reports whether it is installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer


from .._helpers import client

KEY = "nornir"
DIST_PACKAGES: tuple[str, ...] = ("nautobot_plugin_nornir",)


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def nornir_plugin_info() -> dict[str, Any]:
        """Report the Nautobot Nornir backend's presence and configuration.

        Reads ``/api/status/`` and returns whether ``nautobot_plugin_nornir``
        is installed plus its ``PLUGINS_CONFIG`` block (dispatcher mapping,
        credentials provider, connection options) when exposed. Use this to
        confirm device-execution backends are wired up before running Golden
        Config or Onboarding jobs that depend on Nornir.
        """
        status = await client().status()
        installed_apps = status.get("installed-apps") or status.get("installed_apps") or {}
        present = "nautobot_plugin_nornir" in installed_apps
        plugins_cfg = status.get("plugins") or {}
        return {
            "installed": present,
            "version": installed_apps.get("nautobot_plugin_nornir"),
            "plugins_config": plugins_cfg.get("nautobot_plugin_nornir"),
            "note": (
                "nautobot-plugin-nornir is a backend used by other apps "
                "(Golden Config, Onboarding); device tasks run via those "
                "apps' Jobs rather than a dedicated REST API."
            ),
        }
