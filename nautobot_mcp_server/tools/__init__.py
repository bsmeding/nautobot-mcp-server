"""Tool registration for the Nautobot MCP server.

Each submodule defines a ``register(mcp)`` function that attaches its
tools to a :class:`mcp.server.fastmcp.FastMCP` instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_all(mcp: FastMCP) -> None:
    """Register every tool module with the given FastMCP server."""
    from . import (
        circuits,
        dcim,
        discovery,
        extras,
        generic,
        graphql,
        ipam,
        search,
        tenancy,
        users,
        virtualization,
    )

    discovery.register(mcp)
    generic.register(mcp)
    dcim.register(mcp)
    ipam.register(mcp)
    circuits.register(mcp)
    tenancy.register(mcp)
    virtualization.register(mcp)
    extras.register(mcp)
    users.register(mcp)
    graphql.register(mcp)
    search.register(mcp)

    # Optional Nautobot app (plugin) integrations -- gated by the ``plugins``
    # setting (see nautobot_mcp_server.tools.plugins).
    from ..runtime import get_settings, set_enabled_plugins
    from . import plugins

    try:
        plugins_setting = get_settings().plugins
    except RuntimeError:  # settings not initialized (e.g. some test paths)
        plugins_setting = ("auto",)
    set_enabled_plugins(tuple(plugins.register_plugins(mcp, plugins_setting)))
