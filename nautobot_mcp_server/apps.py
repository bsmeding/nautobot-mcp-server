"""Nautobot/Django app configuration for nautobot-mcp-server.

This module is imported only when running inside a Nautobot environment.
It is safe to fail to import when Nautobot is not installed; the standalone
MCP stdio server (``nautobot-mcp-server``) does not need it.
"""

from __future__ import annotations

from nautobot.apps import NautobotAppConfig

from . import __version__


class NautobotMcpServerConfig(NautobotAppConfig):
    """Nautobot app configuration for the MCP Server."""

    name = "nautobot_mcp_server"
    verbose_name = "Nautobot MCP Server"
    version = __version__
    author = "bsmeding"
    description = (
        "Expose Nautobot built-in REST and GraphQL APIs as MCP tools "
        "for LLM/AI integrations."
    )
    base_url = "mcp-server"
    required_settings: list[str] = []
    default_settings = {
        # Connection
        "nautobot_url": "",
        "nautobot_token": "",
        "verify_ssl": True,
        "ca_bundle": "",
        # Behavior
        "request_timeout": 30,
        "max_pagination_records": 5000,
        "allow_writes": False,
        "log_level": "INFO",
        # Tenant scoping (MSP multi-tenant isolation). Empty = no scoping.
        # Accepts a list of tenant names/slugs and/or tenant group names.
        "tenant_scope": [],
        "tenant_group_scope": [],
        # Plugin (Nautobot app) integrations to expose as MCP tools.
        # "auto" = enable a plugin's tools when its Python package is
        # importable. Use explicit keys (design_builder, onboarding, ssot)
        # or "all" to force-enable regardless of local importability
        # (useful for a standalone MCP server talking to a remote Nautobot).
        "plugins": ["auto"],
    }
    caching_config: dict = {}
