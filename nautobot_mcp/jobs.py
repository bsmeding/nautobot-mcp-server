"""Nautobot Jobs for the MCP Server app.

This app ships no Jobs of its own -- it exposes Nautobot's existing APIs and
Jobs over MCP. This module follows the standard Nautobot app layout and is
the place to register any future Jobs. Imported only inside Nautobot.
"""

from __future__ import annotations

from nautobot.apps.jobs import register_jobs

jobs: list = []

if jobs:
    register_jobs(*jobs)
