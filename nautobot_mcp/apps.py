"""Nautobot/Django app configuration for nautobot-mcp.

This module is imported only when running inside a Nautobot environment.
It is safe to fail to import when Nautobot is not installed; the standalone
MCP stdio server (``nautobot-mcp``) does not need it.
"""

from __future__ import annotations

from nautobot.apps import NautobotAppConfig

from . import __version__


class NautobotMcpServerConfig(NautobotAppConfig):
    """Nautobot app configuration for the MCP Server."""

    # Nautobot loads urls, navigation, and jobs from ``<AppConfig.__module__>``.
    # This class lives in ``apps.py`` so a standalone MCP process can skip it,
    # but Nautobot must still look at the ``nautobot_mcp`` package.
    __module__ = "nautobot_mcp"

    name = "nautobot_mcp"
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
        # Optional file the status page tails. Empty = logs stay on the
        # nautobot-mcp process stderr only.
        "log_file": "",
        # When true, HTTP MCP clients must send their own Nautobot API token
        # (X-Nautobot-Token). Nautobot then audits each call as that user.
        # nautobot_token may be left empty in this mode.
        "require_client_token": False,
        # Tenant scoping (MSP multi-tenant isolation). Empty = no scoping.
        # Accepts a list of tenant names/slugs and/or tenant group names.
        "tenant_scope": [],
        "tenant_group_scope": [],
        # Plugin (Nautobot app) integrations to expose as MCP tools.
        # "auto" = enable a plugin's tools when /api/status/ lists that app,
        # or when its Python package is importable here. Explicit keys
        # (design_builder, onboarding, ssot) or "all" force-enable.
        "plugins": ["auto"],
    }
    caching_config: dict = {}
