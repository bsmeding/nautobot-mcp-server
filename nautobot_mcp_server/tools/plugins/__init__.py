"""Optional Nautobot app (plugin) tool integrations.

Each module in this package wraps a NetworkToCode / Nautobot app
(design-builder, onboarding, ssot, ...) as MCP tools. Plugins are
*optional*: the core install only exposes Nautobot-core tools.

A plugin's tools are registered when it is **enabled**, which is decided
by :func:`is_plugin_enabled` from the ``plugins`` setting:

* ``"auto"`` (default) -- enable the plugin when its Python package is
  importable in this environment. This pairs with the pip extras, e.g.
  ``pip install nautobot-mcp-server[design-builder]``.
* an explicit key (``"design_builder"``, ``"onboarding"``, ``"ssot"``) --
  force-enable that plugin even if the package is not importable locally
  (useful for a standalone MCP server talking to a *remote* Nautobot that
  has the app installed).
* ``"all"`` -- force-enable every known plugin.

Each plugin module exposes:

    KEY: str                      # canonical plugin key
    DIST_PACKAGES: tuple[str,...] # importable package name(s) to detect
    def register(mcp) -> None     # attach the plugin's tools
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("nautobot_mcp_server.tools.plugins")

# Canonical plugin key -> module providing its tools.
_PLUGIN_MODULES: dict[str, str] = {
    "design_builder": "nautobot_mcp_server.tools.plugins.design_builder",
    "onboarding": "nautobot_mcp_server.tools.plugins.onboarding",
    "ssot": "nautobot_mcp_server.tools.plugins.ssot",
    "golden_config": "nautobot_mcp_server.tools.plugins.golden_config",
    "nornir": "nautobot_mcp_server.tools.plugins.nornir",
}


def available_plugins() -> tuple[str, ...]:
    """Return the canonical keys of every known plugin integration."""
    return tuple(_PLUGIN_MODULES)


def _package_importable(packages: tuple[str, ...]) -> bool:
    return any(importlib.util.find_spec(pkg) is not None for pkg in packages)


def is_plugin_enabled(
    key: str,
    plugins_setting: tuple[str, ...],
    dist_packages: tuple[str, ...],
) -> bool:
    """Decide whether ``key`` should be enabled given the configuration."""
    selectors = {s.lower().replace("-", "_") for s in plugins_setting}
    if "all" in selectors:
        return True
    if key in selectors:
        return True
    if "auto" in selectors:
        return _package_importable(dist_packages)
    return False


def register_plugins(mcp: FastMCP, plugins_setting: tuple[str, ...]) -> list[str]:
    """Register all enabled plugin tool modules. Returns the enabled keys."""
    enabled: list[str] = []
    for key, module_path in _PLUGIN_MODULES.items():
        module = importlib.import_module(module_path)
        if not is_plugin_enabled(
            key, plugins_setting, getattr(module, "DIST_PACKAGES", ())
        ):
            continue
        try:
            module.register(mcp)
        except Exception:  # pragma: no cover - defensive: never break startup
            logger.exception("Failed to register plugin tools for %r", key)
            continue
        enabled.append(key)
        logger.info("Enabled plugin tools: %s", key)
    return enabled
