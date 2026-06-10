"""Cross-domain search convenience tools.

These wrap common ``rest_list`` filter combinations so an LLM doesn't
have to remember Nautobot's exact filter names for everyday questions
("find all active core devices in Amsterdam"). For anything outside
these patterns, fall back to ``rest_list``.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def search_devices(
        q: str | None = None,
        status: str | None = None,
        location: str | None = None,
        role: str | None = None,
        manufacturer: str | None = None,
        platform: str | None = None,
        tenant: str | None = None,
        tag: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search devices by free-text query and common dimensions."""
        filters = clean_filters(
            {
                "q": q,
                "status": status,
                "location": location,
                "role": role,
                "manufacturer": manufacturer,
                "platform": platform,
                "tenant": tenant,
                "tag": tag,
            }
        )
        return await client().rest_list(
            "/api/dcim/devices/", filters=filters, limit=limit
        )

    @mcp.tool()
    async def search_ip_addresses(
        q: str | None = None,
        address: str | None = None,
        status: str | None = None,
        vrf: str | None = None,
        tenant: str | None = None,
        family: int | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search IP addresses."""
        filters = clean_filters(
            {
                "q": q,
                "address": address,
                "status": status,
                "vrf": vrf,
                "tenant": tenant,
                "family": family,
            }
        )
        return await client().rest_list(
            "/api/ipam/ip-addresses/", filters=filters, limit=limit
        )

    @mcp.tool()
    async def search_prefixes(
        q: str | None = None,
        prefix: str | None = None,
        status: str | None = None,
        vrf: str | None = None,
        tenant: str | None = None,
        family: int | None = None,
        within: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search prefixes. ``within`` accepts a CIDR to scope results."""
        filters = clean_filters(
            {
                "q": q,
                "prefix": prefix,
                "status": status,
                "vrf": vrf,
                "tenant": tenant,
                "family": family,
                "within": within,
            }
        )
        return await client().rest_list(
            "/api/ipam/prefixes/", filters=filters, limit=limit
        )

    @mcp.tool()
    async def search_locations(
        q: str | None = None,
        status: str | None = None,
        location_type: str | None = None,
        parent: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search locations."""
        filters = clean_filters(
            {
                "q": q,
                "status": status,
                "location_type": location_type,
                "parent": parent,
            }
        )
        return await client().rest_list(
            "/api/dcim/locations/", filters=filters, limit=limit
        )

    @mcp.tool()
    async def search_circuits(
        q: str | None = None,
        provider: str | None = None,
        circuit_type: str | None = None,
        status: str | None = None,
        tenant: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search circuits."""
        filters = clean_filters(
            {
                "q": q,
                "provider": provider,
                "circuit_type": circuit_type,
                "status": status,
                "tenant": tenant,
            }
        )
        return await client().rest_list(
            "/api/circuits/circuits/", filters=filters, limit=limit
        )
