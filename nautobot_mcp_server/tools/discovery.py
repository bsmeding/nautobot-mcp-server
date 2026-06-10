"""Discovery / metadata tools.

Useful for an LLM to figure out *what* endpoints exist before calling them.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def nautobot_status() -> dict[str, Any]:
        """Return Nautobot's ``/api/status/`` document.

        Includes Django/Python/Nautobot versions, installed apps, plugins,
        and database backend.
        """
        return await client().status()

    @mcp.tool()
    async def list_api_roots() -> dict[str, Any]:
        """List Nautobot's REST API root document at ``/api/``.

        Returns a mapping of category → endpoint URL (dcim, ipam, extras,
        circuits, tenancy, virtualization, users, etc.). Use this to
        discover which endpoints are available before calling
        ``rest_list``.
        """
        return await client().list_api_roots()

    @mcp.tool()
    async def list_content_types() -> list[dict[str, Any]]:
        """List Django content types (``app_label.model``).

        Useful when working with custom fields, tags, relationships, or
        any feature scoped by content type.
        """
        return await client().rest_list(
            "/api/extras/content-types/", paginate=True
        )

    @mcp.tool()
    async def tenant_scope_info() -> dict[str, Any]:
        """Report the active tenant scope enforced by this server.

        In MSP/multi-tenant deployments the server can be locked to one or
        more tenants (or tenant groups). When a scope is active, every read
        and write is restricted to those tenants. Returns the configured
        names and the resolved tenant UUIDs (resolving them on first call).
        When no scope is configured, ``active`` is ``False`` and access is
        limited only by what the API token itself permits.
        """
        cli = client()
        if cli.tenant_scope.active:
            await cli._resolve_tenant_ids()
        return cli.tenant_scope.describe()

    @mcp.tool()
    async def list_active_plugins() -> dict[str, Any]:
        """Report which optional Nautobot app (plugin) integrations are active.

        Plugin tools (design_builder, onboarding, ssot, ...) are optional and
        gated by the ``plugins`` setting. Returns the configured selectors,
        the enabled plugin keys (whose tools are registered on this server),
        and all known plugin keys.
        """
        from ..runtime import get_enabled_plugins, get_settings
        from .plugins import available_plugins

        return {
            "configured": list(get_settings().plugins),
            "enabled": list(get_enabled_plugins()),
            "available": list(available_plugins()),
        }

    @mcp.tool()
    async def list_endpoints_in(category: str) -> dict[str, Any]:
        """List the sub-endpoints inside an API category, e.g. ``dcim``.

        Equivalent to GET ``/api/<category>/``.
        """
        return await client().rest_get(f"/api/{category.strip('/')}/")
