"""Circuits domain tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client, lookup_id_or_name


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_circuits(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List circuits. Filters: ``provider``, ``circuit_type``,
        ``status``, ``tenant``, ``location``, ``q``."""
        return await client().rest_list(
            "/api/circuits/circuits/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_circuit(cid_or_id: str) -> dict[str, Any]:
        """Fetch a circuit by UUID or by ``cid`` (circuit ID string)."""
        return await lookup_id_or_name(
            "/api/circuits/circuits/", cid_or_id, name_field="cid"
        )

    @mcp.tool()
    async def list_providers() -> Any:
        """List circuit providers."""
        return await client().rest_list(
            "/api/circuits/providers/", paginate=True
        )

    @mcp.tool()
    async def list_circuit_types() -> Any:
        """List circuit types."""
        return await client().rest_list(
            "/api/circuits/circuit-types/", paginate=True
        )

    @mcp.tool()
    async def list_circuit_terminations(circuit_cid_or_id: str) -> Any:
        """List terminations for a given circuit."""
        circuit = await lookup_id_or_name(
            "/api/circuits/circuits/", circuit_cid_or_id, name_field="cid"
        )
        return await client().rest_list(
            "/api/circuits/circuit-terminations/",
            filters={"circuit_id": circuit["id"]},
            paginate=True,
        )
