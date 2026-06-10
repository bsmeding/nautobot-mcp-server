"""URL patterns for the Nautobot MCP Server app.

Mounted by Nautobot under the app's ``base_url`` (``/plugins/mcp-server/``).
Imported only inside a Nautobot/Django environment.
"""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "nautobot_mcp_server"

urlpatterns = [
    path("", views.MCPServerHomeView.as_view(), name="home"),
]
