"""GraphQL tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def graphql_query(
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run an arbitrary GraphQL query against ``/api/graphql/``.

        Useful for cross-model queries that REST handles awkwardly, e.g.
        "all interfaces of all devices in site X with their connected
        cables and IPs".

        Pair with ``graphql_introspect`` to discover available types.
        """
        return await client().graphql_query(query, variables)

    @mcp.tool()
    async def graphql_introspect() -> dict[str, Any]:
        """Return Nautobot's GraphQL schema (types, kinds, descriptions).

        Use this before writing a complex GraphQL query so the LLM knows
        which fields exist.
        """
        return await client().graphql_introspect()
