"""Tools for the Nautobot Nornir app (``nautobot-plugin-nornir``).

This app is primarily a *backend* library: it provides the Nornir
inventory, credential providers, and task dispatchers used by other apps
(notably Golden Config and Device Onboarding) to talk to devices. It does
not expose its own task-execution REST API, so there is little to drive
directly -- network actions run through the consuming app's Jobs.

These tools surface its configuration so an agent can confirm the backend
is present and how it is wired up.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .._helpers import client

KEY = "nornir"
DIST_PACKAGES: tuple[str, ...] = ("nautobot_plugin_nornir",)


def register(mcp: FastMCP) -> None:
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
        installed_apps = status.get("installed-apps") or status.get(
            "installed_apps"
        ) or {}
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
