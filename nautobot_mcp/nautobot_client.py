"""Old import path. Use nautobot_mcp.client.

`from nautobot_mcp.nautobot_client import NautobotClient` still works.
"""

from __future__ import annotations

import warnings

from .client import NautobotClient

__all__ = ["NautobotClient"]

warnings.warn(
    "nautobot_mcp.nautobot_client is deprecated; "
    "import from nautobot_mcp.client instead.",
    DeprecationWarning,
    stacklevel=2,
)
