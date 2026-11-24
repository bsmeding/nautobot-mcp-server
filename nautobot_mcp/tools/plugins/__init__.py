"""Optional Nautobot app tools (Design Builder, Onboarding, SSoT, ...).

Core tools are always on. These are extra.

auto (default): enable a tool when GET /api/status/ lists the app under
nautobot-apps, or when that Python package is installed in this process.
An explicit key (design_builder, onboarding, ssot, ...) or "all" forces it on.

Each module exposes KEY, DIST_PACKAGES, and register(mcp).
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import TYPE_CHECKING, Any

import httpx

from nautobot_mcp.config import NautobotMcpSettings

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("nautobot_mcp.tools.plugins")

# Canonical plugin key -> module providing its tools.
_PLUGIN_MODULES: dict[str, str] = {
    "design_builder": "nautobot_mcp.tools.plugins.design_builder",
    "onboarding": "nautobot_mcp.tools.plugins.onboarding",
    "ssot": "nautobot_mcp.tools.plugins.ssot",
    "golden_config": "nautobot_mcp.tools.plugins.golden_config",
    "nornir": "nautobot_mcp.tools.plugins.nornir",
}


def available_plugins() -> tuple[str, ...]:
    """Return the canonical keys of every known plugin integration."""
    return tuple(_PLUGIN_MODULES)


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _package_importable(packages: tuple[str, ...]) -> bool:
    return any(importlib.util.find_spec(pkg) is not None for pkg in packages)


def installed_app_names(status: dict[str, Any]) -> set[str]:
    """App names from /api/status/.

    nautobot-apps is the PLUGINS list. Fall back to plugins, then installed-apps.
    """
    for key in ("nautobot-apps", "plugins"):
        block = status.get(key)
        if isinstance(block, dict):
            return {_normalize_name(name) for name in block if str(name).strip()}

    block = status.get("installed-apps") or status.get("installed_apps") or {}
    if isinstance(block, dict):
        names = block.keys()
    elif isinstance(block, (list, tuple)):
        names = block
    else:
        names = ()
    return {_normalize_name(str(name)) for name in names if str(name).strip()}


def fetch_installed_app_names(settings: NautobotMcpSettings) -> set[str]:
    """Enabled app names from GET /api/status/.

    Empty set when this process has no token or the call fails.
    Startup then falls back to local packages.
    """
    if not settings.token:
        logger.info(
            "Skipping plugin discovery from /api/status/: no API token on this process."
        )
        return set()

    url = f"{settings.url.rstrip('/')}/api/status/"
    try:
        with httpx.Client(
            headers={
                "Accept": "application/json",
                "Authorization": f"Token {settings.token}",
                "User-Agent": "nautobot-mcp",
            },
            verify=settings.verify_ssl,
            timeout=settings.request_timeout,
            follow_redirects=True,
        ) as http:
            response = http.get(url)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.warning("Could not read installed apps from %s: %s", url, exc)
        return set()

    if not isinstance(payload, dict):
        logger.warning(
            "Unexpected /api/status/ payload type: %s", type(payload).__name__
        )
        return set()

    names = installed_app_names(payload)
    logger.info(
        "Nautobot /api/status/ apps: %s",
        ", ".join(sorted(names)) or "(none)",
    )
    return names


def is_plugin_enabled(
    key: str,
    plugins_setting: tuple[str, ...],
    dist_packages: tuple[str, ...],
    remote_apps: set[str] | None = None,
) -> bool:
    """True when this plugin's tools should be registered.

    remote_apps comes from /api/status/. None means that call was skipped.
    """
    selectors = {_normalize_name(s) for s in plugins_setting}
    if "all" in selectors:
        return True
    if _normalize_name(key) in selectors:
        return True
    if "auto" in selectors:
        if _package_importable(dist_packages):
            return True
        if remote_apps:
            wanted = {_normalize_name(pkg) for pkg in dist_packages}
            return bool(wanted & remote_apps)
    return False


def register_plugins(
    mcp: MCPServer,
    plugins_setting: tuple[str, ...],
    remote_apps: set[str] | None = None,
) -> list[str]:
    """Register all enabled plugin tool modules. Returns the enabled keys."""
    enabled: list[str] = []
    for key, module_path in _PLUGIN_MODULES.items():
        module = importlib.import_module(module_path)
        if not is_plugin_enabled(
            key,
            plugins_setting,
            getattr(module, "DIST_PACKAGES", ()),
            remote_apps,
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
