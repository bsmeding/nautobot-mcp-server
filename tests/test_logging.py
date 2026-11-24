"""Tests for MCP log file setup and the status-page tail."""

from __future__ import annotations

import logging

from nautobot_mcp.config import load_settings
from nautobot_mcp.logging_config import LOGGER_NAME, configure_logging, read_log_tail


def test_read_log_tail_empty_path() -> None:
    assert read_log_tail("") is None


def test_read_log_tail_missing_file(tmp_path) -> None:
    assert read_log_tail(str(tmp_path / "missing.log")) == ""


def test_configure_logging_writes_file(tmp_path) -> None:
    path = tmp_path / "nautobot-mcp.log"
    logger = configure_logging("INFO", str(path))
    logger.info("status page can read this")
    for handler in logging.getLogger(LOGGER_NAME).handlers:
        handler.flush()

    text = read_log_tail(str(path))
    assert text is not None
    assert "status page can read this" in text


def test_log_file_from_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", "https://x.example.com")
    monkeypatch.setenv("NAUTOBOT_TOKEN", "tok")
    monkeypatch.setenv("NAUTOBOT_MCP_LOG_FILE", str(tmp_path / "mcp.log"))
    settings = load_settings()
    assert settings.log_file == str(tmp_path / "mcp.log")
    assert settings.redacted()["log_file"] == str(tmp_path / "mcp.log")
