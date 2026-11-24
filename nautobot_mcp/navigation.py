"""Apps menu item for the MCP status page. Nautobot only."""

from __future__ import annotations

from nautobot.apps.ui import NavMenuGroup, NavMenuItem, NavMenuTab

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(
            NavMenuGroup(
                name="MCP Server",
                weight=150,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_mcp:home",
                        name="MCP Server Status",
                        permissions=[],
                    ),
                ),
            ),
        ),
    ),
)
