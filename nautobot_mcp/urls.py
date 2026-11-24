"""Routes under /plugins/mcp-server/. Nautobot only."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "nautobot_mcp"

urlpatterns = [
    path("", views.MCPServerHomeView.as_view(), name="home"),
]
