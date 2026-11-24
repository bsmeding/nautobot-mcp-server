"""Logging setup for the Nautobot MCP server.

Logs always go to stderr so the stdio MCP transport (stdout) stays clean.
"""

from __future__ import annotations

import logging
import sys

LOGGER_NAME = "nautobot_mcp"


def configure_logging(level: str = "INFO", log_file: str = "") -> logging.Logger:
    """Configure (or reconfigure) the package logger and return it.

    Stderr is always attached so the stdio MCP transport stays clean.
    ``log_file`` is optional and is what the Nautobot status page reads.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setFormatter(formatter)
    logger.addHandler(stderr)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.setLevel(level.upper())
    logger.propagate = False
    return logger


def read_log_tail(path: str, *, max_lines: int = 200, max_bytes: int = 65_536) -> str | None:
    """Return the end of a log file.

    ``None`` when ``path`` is empty (logging to a file is not configured).
    An empty string when the path is set but the file is not there yet.
    """
    from pathlib import Path

    if not path:
        return None
    file = Path(path)
    if not file.is_file():
        return ""
    data = file.read_bytes()
    if len(data) > max_bytes:
        data = data[-max_bytes:]
    text = data.decode("utf-8", errors="replace")
    return "\n".join(text.splitlines()[-max_lines:])
