"""Navigation menu for the Nautobot MCP Server app.

Adds a single menu item pointing at the status page. Imported only inside a
Nautobot/Django environment.
"""

from __future__ import annotations

from nautobot.apps.ui import NavMenuGroup, NavMenuItem, NavMenuTab

menu_items = (
    NavMenuTab(
        label="Apps",
        groups=(
            NavMenuGroup(
                name="MCP Server",
                weight=150,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_mcp_server:home",
                        name="MCP Server Status",
                        permissions=[],
                    ),
                ),
            ),
        ),
    ),
)
