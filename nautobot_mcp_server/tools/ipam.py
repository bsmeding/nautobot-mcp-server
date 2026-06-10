"""IPAM (IP Address Management) tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client, lookup_id_or_name


def register(mcp: FastMCP) -> None:
    # ---- prefixes -----------------------------------------------------

    @mcp.tool()
    async def list_prefixes(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List prefixes. Filters: ``status``, ``vrf``, ``tenant``, ``role``,
        ``family`` (4 or 6), ``within``, ``within_include``, ``contains``."""
        return await client().rest_list(
            "/api/ipam/prefixes/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_prefix(prefix_or_id: str) -> dict[str, Any]:
        """Fetch a prefix by UUID, or by CIDR string (e.g. ``10.0.0.0/24``)."""
        cli = client()
        try:
            return await cli.rest_get_object("/api/ipam/prefixes/", prefix_or_id)
        except Exception:
            page = await cli.rest_get(
                "/api/ipam/prefixes/", params={"prefix": prefix_or_id, "limit": 2}
            )
            results = (page or {}).get("results") or []
            if not results:
                raise ValueError(
                    f"No prefix found matching {prefix_or_id!r}"
                ) from None
            if len(results) > 1:
                raise ValueError(
                    f"Ambiguous prefix lookup: multiple matches for {prefix_or_id!r}"
                ) from None
            return results[0]

    @mcp.tool()
    async def get_available_ips(prefix_id: str, count: int = 1) -> Any:
        """Return up to ``count`` available IPs inside a prefix.

        This is a read-only preview of the next free addresses; it does
        not allocate them. To actually allocate, ``rest_create`` an IP
        address with the desired ``address`` and assign it.
        """
        return await client().rest_get(
            f"/api/ipam/prefixes/{prefix_id}/available-ips/",
            params={"limit": count},
        )

    @mcp.tool()
    async def get_available_prefixes(prefix_id: str) -> Any:
        """List available child prefixes inside a parent prefix."""
        return await client().rest_get(
            f"/api/ipam/prefixes/{prefix_id}/available-prefixes/"
        )

    # ---- IP addresses -------------------------------------------------

    @mcp.tool()
    async def list_ip_addresses(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List IP addresses. Filters include ``address``, ``parent``,
        ``status``, ``vrf``, ``tenant``, ``family``, ``role``."""
        return await client().rest_list(
            "/api/ipam/ip-addresses/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_ip_address(address_or_id: str) -> dict[str, Any]:
        """Fetch an IP address by UUID or by ``address`` string."""
        cli = client()
        try:
            return await cli.rest_get_object("/api/ipam/ip-addresses/", address_or_id)
        except Exception:
            page = await cli.rest_get(
                "/api/ipam/ip-addresses/",
                params={"address": address_or_id, "limit": 2},
            )
            results = (page or {}).get("results") or []
            if not results:
                raise ValueError(
                    f"No IP address found matching {address_or_id!r}"
                ) from None
            if len(results) > 1:
                raise ValueError(
                    f"Ambiguous IP lookup: multiple matches for {address_or_id!r}"
                ) from None
            return results[0]

    # ---- VLANs --------------------------------------------------------

    @mcp.tool()
    async def list_vlans(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List VLANs. Filters: ``vid``, ``name``, ``status``, ``location``,
        ``vlan_group``, ``tenant``, ``role``."""
        return await client().rest_list(
            "/api/ipam/vlans/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_vlan(name_or_id: str) -> dict[str, Any]:
        """Fetch a VLAN by UUID or by name."""
        return await lookup_id_or_name("/api/ipam/vlans/", name_or_id)

    @mcp.tool()
    async def list_vlan_groups() -> Any:
        """List VLAN groups."""
        return await client().rest_list(
            "/api/ipam/vlan-groups/", paginate=True
        )

    # ---- VRFs / RIRs / Namespaces -------------------------------------

    @mcp.tool()
    async def list_vrfs(
        filters: dict[str, Any] | None = None,
    ) -> Any:
        """List VRFs."""
        return await client().rest_list(
            "/api/ipam/vrfs/",
            filters=clean_filters(filters),
            paginate=True,
        )

    @mcp.tool()
    async def list_rirs() -> Any:
        """List RIRs (Regional Internet Registries)."""
        return await client().rest_list("/api/ipam/rirs/", paginate=True)

    @mcp.tool()
    async def list_namespaces() -> Any:
        """List IPAM namespaces (Nautobot 2.x)."""
        return await client().rest_list(
            "/api/ipam/namespaces/", paginate=True
        )
