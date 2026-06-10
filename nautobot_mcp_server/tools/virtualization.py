"""Virtualization tools (clusters, VMs, VM interfaces)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client, lookup_id_or_name


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_virtual_machines(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List virtual machines. Filters: ``cluster``, ``status``,
        ``tenant``, ``role``, ``platform``, ``q``."""
        return await client().rest_list(
            "/api/virtualization/virtual-machines/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_virtual_machine(name_or_id: str) -> dict[str, Any]:
        """Fetch a virtual machine by UUID or name."""
        return await lookup_id_or_name(
            "/api/virtualization/virtual-machines/", name_or_id
        )

    @mcp.tool()
    async def list_clusters(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List clusters. Filters: ``cluster_type``, ``cluster_group``,
        ``location``, ``tenant``."""
        return await client().rest_list(
            "/api/virtualization/clusters/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def list_cluster_types() -> Any:
        """List cluster types."""
        return await client().rest_list(
            "/api/virtualization/cluster-types/", paginate=True
        )

    @mcp.tool()
    async def get_vm_interfaces(
        vm_name_or_id: str,
        paginate: bool = True,
    ) -> Any:
        """List interfaces on a virtual machine."""
        vm = await lookup_id_or_name(
            "/api/virtualization/virtual-machines/", vm_name_or_id
        )
        return await client().rest_list(
            "/api/virtualization/interfaces/",
            filters={"virtual_machine_id": vm["id"]},
            paginate=paginate,
        )
