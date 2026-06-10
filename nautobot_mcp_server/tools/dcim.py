"""DCIM (Data Center Infrastructure Management) tools.

Covers devices, interfaces, racks, locations, device types, manufacturers,
platforms, and cables.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client, lookup_id_or_name


def register(mcp: FastMCP) -> None:
    # ---- devices -------------------------------------------------------

    @mcp.tool()
    async def list_devices(
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        paginate: bool = False,
    ) -> Any:
        """List Nautobot devices.

        Common filters: ``status``, ``location``, ``role``, ``device_type``,
        ``manufacturer``, ``platform``, ``tenant``, ``tag``, ``q``
        (free-text search).
        """
        return await client().rest_list(
            "/api/dcim/devices/",
            filters=clean_filters(filters),
            limit=limit,
            paginate=paginate,
        )

    @mcp.tool()
    async def get_device(name_or_id: str) -> dict[str, Any]:
        """Fetch a device by UUID or by name."""
        return await lookup_id_or_name("/api/dcim/devices/", name_or_id)

    @mcp.tool()
    async def get_device_interfaces(
        device_name_or_id: str,
        filters: dict[str, Any] | None = None,
        paginate: bool = True,
    ) -> Any:
        """List interfaces on a device, with optional extra filters."""
        device = await lookup_id_or_name("/api/dcim/devices/", device_name_or_id)
        merged = clean_filters(filters)
        merged["device_id"] = device["id"]
        return await client().rest_list(
            "/api/dcim/interfaces/", filters=merged, paginate=paginate
        )

    @mcp.tool()
    async def get_device_config_context(device_name_or_id: str) -> dict[str, Any]:
        """Return the rendered config context for a device.

        Equivalent to GET ``/api/dcim/devices/{id}/`` and reading the
        ``config_context`` field. Helpful when an LLM is generating
        device configuration.
        """
        device = await lookup_id_or_name("/api/dcim/devices/", device_name_or_id)
        return {
            "id": device["id"],
            "name": device.get("name"),
            "config_context": device.get("config_context"),
            "local_config_context_data": device.get("local_config_context_data"),
        }

    @mcp.tool()
    async def get_device_inventory(
        device_name_or_id: str,
        paginate: bool = True,
    ) -> Any:
        """List inventory items (modules, line cards, etc.) on a device."""
        device = await lookup_id_or_name("/api/dcim/devices/", device_name_or_id)
        return await client().rest_list(
            "/api/dcim/inventory-items/",
            filters={"device_id": device["id"]},
            paginate=paginate,
        )

    # ---- locations & racks --------------------------------------------

    @mcp.tool()
    async def list_locations(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List Nautobot locations (sites, regions, rooms, etc. in 2.x)."""
        return await client().rest_list(
            "/api/dcim/locations/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_location(name_or_id: str) -> dict[str, Any]:
        """Fetch a location by UUID or name."""
        return await lookup_id_or_name("/api/dcim/locations/", name_or_id)

    @mcp.tool()
    async def list_location_types() -> Any:
        """List location types (the hierarchy levels: Region, Site, ...)."""
        return await client().rest_list(
            "/api/dcim/location-types/", paginate=True
        )

    @mcp.tool()
    async def list_racks(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List racks. Filter by ``location``, ``status``, ``role``, etc."""
        return await client().rest_list(
            "/api/dcim/racks/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_rack(name_or_id: str) -> dict[str, Any]:
        """Fetch a rack by UUID or name."""
        return await lookup_id_or_name("/api/dcim/racks/", name_or_id)

    @mcp.tool()
    async def get_rack_elevation(rack_name_or_id: str) -> Any:
        """Return the elevation (unit-by-unit layout) of a rack."""
        rack = await lookup_id_or_name("/api/dcim/racks/", rack_name_or_id)
        return await client().rest_get(
            f"/api/dcim/racks/{rack['id']}/elevation/"
        )

    # ---- device types & roles -----------------------------------------

    @mcp.tool()
    async def list_device_types(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List device types. Filter by ``manufacturer``, ``model``, etc."""
        return await client().rest_list(
            "/api/dcim/device-types/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def list_device_roles(
        filters: dict[str, Any] | None = None,
    ) -> Any:
        """List device roles (now ``/api/extras/roles/?content_types=dcim.device``)."""
        merged = clean_filters(filters)
        merged.setdefault("content_types", "dcim.device")
        return await client().rest_list(
            "/api/extras/roles/", filters=merged, paginate=True
        )

    @mcp.tool()
    async def list_manufacturers() -> Any:
        """List device manufacturers."""
        return await client().rest_list(
            "/api/dcim/manufacturers/", paginate=True
        )

    @mcp.tool()
    async def list_platforms() -> Any:
        """List platforms (network OS families)."""
        return await client().rest_list(
            "/api/dcim/platforms/", paginate=True
        )

    # ---- cables -------------------------------------------------------

    @mcp.tool()
    async def list_cables(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List cables. Filter by ``status``, ``type``, ``termination_a_*``."""
        return await client().rest_list(
            "/api/dcim/cables/",
            filters=clean_filters(filters),
            paginate=paginate,
        )
