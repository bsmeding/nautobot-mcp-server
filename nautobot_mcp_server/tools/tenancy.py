"""Tenancy tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client, lookup_id_or_name


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_tenants(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List tenants. Filter by ``group``, ``q``."""
        return await client().rest_list(
            "/api/tenancy/tenants/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_tenant(name_or_id: str) -> dict[str, Any]:
        """Fetch a tenant by UUID or name."""
        return await lookup_id_or_name("/api/tenancy/tenants/", name_or_id)

    @mcp.tool()
    async def list_tenant_groups() -> Any:
        """List tenant groups."""
        return await client().rest_list(
            "/api/tenancy/tenant-groups/", paginate=True
        )
