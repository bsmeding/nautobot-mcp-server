"""Nautobot app config. Imported only inside Nautobot.

The standalone nautobot-mcp process does not need this module.
"""

from __future__ import annotations

from nautobot.apps import NautobotAppConfig

from . import __version__


class NautobotMcpServerConfig(NautobotAppConfig):
    """Nautobot app entry for the MCP status page."""

    # Nautobot loads urls/navigation/jobs from this class's module.
    # Keep __module__ on the package so those files are found, while this
    # class stays in apps.py and a standalone process can skip the import.
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
        # auto = tools for apps listed on /api/status/, or installed here.
        # Explicit keys (design_builder, onboarding, ssot) or "all" force them on.
        "plugins": ["auto"],
    }
    caching_config: dict = {}
