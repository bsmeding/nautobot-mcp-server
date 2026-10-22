"""Deprecated import path for the project now named nautobot-mcp."""

import warnings

warnings.warn(
    "nautobot_mcp_server was renamed to nautobot_mcp. "
    'Install nautobot-mcp and set PLUGINS = ["nautobot_mcp"].',
    DeprecationWarning,
    stacklevel=2,
)
