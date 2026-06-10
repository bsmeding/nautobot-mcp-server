"""Logging setup for the Nautobot MCP server.

Logs always go to stderr so the stdio MCP transport (stdout) stays clean.
"""

from __future__ import annotations

import logging
import sys

LOGGER_NAME = "nautobot_mcp_server"


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure (or reconfigure) the package logger and return it."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level.upper())
    logger.propagate = False
    return logger
