"""UI views for the Nautobot MCP Server app.

This app has no database models -- it exposes Nautobot's APIs over MCP. The
single view is an operational status page showing the resolved (redacted)
configuration and the enabled plugin integrations, so operators can confirm
how the server is wired up from within Nautobot.

This module is imported only inside a Nautobot/Django environment.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from . import __version__


class MCPServerHomeView(LoginRequiredMixin, TemplateView):
    """Operational status page for the MCP server."""

    template_name = "nautobot_mcp/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["version"] = __version__

        log_file = ""
        try:
            from .config import load_settings

            context["settings"] = load_settings().redacted()
            context["config_error"] = None
            log_file = context["settings"].get("log_file") or ""
        except Exception as exc:  # configuration not yet provided
            context["settings"] = None
            context["config_error"] = str(exc)
            try:
                from .config import plugin_config_snapshot

                log_file = str(plugin_config_snapshot().get("log_file") or "")
            except Exception:
                log_file = ""

        from .logging_config import read_log_tail

        context["log_file"] = log_file
        context["log_text"] = read_log_tail(log_file)

        try:
            from .tools.plugins import available_plugins

            context["available_plugins"] = list(available_plugins())
        except Exception:
            context["available_plugins"] = []

        return context
