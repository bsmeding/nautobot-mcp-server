"""Deprecated module — kept for backwards compatibility.

The implementation moved to :mod:`nautobot_mcp_server.client`. This shim
re-exports :class:`NautobotClient` so that any external code importing
``from nautobot_mcp_server.nautobot_client import NautobotClient``
keeps working.

Will be removed in a future major release.
"""

from __future__ import annotations

import warnings

from .client import NautobotClient

__all__ = ["NautobotClient"]

warnings.warn(
    "nautobot_mcp_server.nautobot_client is deprecated; "
    "import from nautobot_mcp_server.client instead.",
    DeprecationWarning,
    stacklevel=2,
)
