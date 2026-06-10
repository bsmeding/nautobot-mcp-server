"""Users / groups / permissions tools (read-only metadata)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_users(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List Nautobot users. Filters: ``username``, ``is_active``, ``q``.

        Note: results never include passwords or sensitive credentials.
        """
        return await client().rest_list(
            "/api/users/users/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def list_groups() -> Any:
        """List user groups."""
        return await client().rest_list(
            "/api/users/groups/", paginate=True
        )

    @mcp.tool()
    async def list_object_permissions() -> Any:
        """List object permission definitions."""
        return await client().rest_list(
            "/api/users/permissions/", paginate=True
        )
