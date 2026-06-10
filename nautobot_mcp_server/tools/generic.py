"""Generic REST passthrough tools.

These tools let an LLM hit any Nautobot REST endpoint without us having
to hand-wrap every model. They are the backbone of "internal Nautobot
access".
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def rest_list(
        endpoint: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = False,
        max_records: int | None = None,
    ) -> Any:
        """List objects from any Nautobot REST endpoint.

        Args:
            endpoint: REST path under ``/api/``, e.g. ``/api/dcim/devices/``.
            filters: Optional filter parameters. Nautobot supports rich
                filtering, e.g. ``{"status": "active", "location": "ams01"}``.
                Use ``{"q": "core"}`` for free-text search where supported.
            limit: Page size (default 50, max 200 per Nautobot).
            offset: Page offset for manual pagination.
            paginate: If ``True``, walks every page automatically and
                returns a flat list (capped at ``max_records`` or the
                configured ``max_pagination_records``).
            max_records: Optional cap when ``paginate=True``.
        """
        return await client().rest_list(
            endpoint,
            filters=clean_filters(filters),
            limit=limit,
            offset=offset,
            paginate=paginate,
            max_records=max_records,
        )

    @mcp.tool()
    async def rest_get(endpoint: str, object_id: str) -> dict[str, Any]:
        """Fetch a single object: ``GET <endpoint>/<object_id>/``.

        Args:
            endpoint: Collection endpoint, e.g. ``/api/dcim/devices/``.
            object_id: UUID, slug, or numeric id of the object.
        """
        return await client().rest_get_object(endpoint, object_id)

    @mcp.tool()
    async def rest_create(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new object via POST. Requires writes to be enabled.

        Args:
            endpoint: Collection endpoint, e.g. ``/api/ipam/prefixes/``.
            data: Payload matching Nautobot's REST schema for that model.
        """
        return await client().rest_create(endpoint, data)

    @mcp.tool()
    async def rest_update(
        endpoint: str,
        object_id: str,
        data: dict[str, Any],
        partial: bool = True,
    ) -> dict[str, Any]:
        """Update an object via PATCH (or PUT if ``partial=False``).

        Requires writes to be enabled.
        """
        return await client().rest_update(
            endpoint, object_id, data, partial=partial
        )

    @mcp.tool()
    async def rest_delete(endpoint: str, object_id: str) -> dict[str, Any]:
        """Delete an object via DELETE. Requires writes to be enabled."""
        return await client().rest_delete(endpoint, object_id)
