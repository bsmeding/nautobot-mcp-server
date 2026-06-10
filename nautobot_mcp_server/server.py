"""MCP server entrypoint for Nautobot.

Run as a stdio MCP server::

    nautobot-mcp-server

Or programmatically::

    from nautobot_mcp_server.server import build_server, main
    main()
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from .client import NautobotClient
from .config import NautobotMcpSettings, load_settings
from .logging_config import configure_logging
from .runtime import set_client, set_settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("nautobot_mcp_server.server")


def build_server(settings: NautobotMcpSettings | None = None) -> FastMCP:
    """Construct a configured FastMCP server.

    The actual NautobotClient is created in the ``lifespan`` so the
    HTTP connection is opened only when the server starts (this matters
    for cleanly closing the client on shutdown).
    """
    from mcp.server.fastmcp import FastMCP  # local import keeps import cost low

    from .tools import register_all

    resolved = settings or load_settings()
    set_settings(resolved)
    configure_logging(resolved.log_level)
    logger.info("Nautobot MCP server starting; settings=%s", resolved.redacted())

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        client = NautobotClient(resolved)
        set_client(client)
        try:
            yield {"client": client, "settings": resolved}
        finally:
            await client.aclose()
            logger.info("Nautobot MCP server shut down cleanly")

    mcp = FastMCP(
        "nautobot-mcp-server",
        instructions=(
            "Tools for interacting with a Nautobot instance via its built-in "
            "REST and GraphQL APIs. Start with `nautobot_status` and "
            "`list_api_roots` for discovery, then use domain-specific tools "
            "(DCIM, IPAM, circuits, virtualization, extras, jobs) or fall "
            "back to the generic `rest_list` / `rest_get` tools for any "
            "endpoint not covered by a wrapper."
        ),
        lifespan=lifespan,
    )

    register_all(mcp)
    return mcp


async def _async_main(transport: str) -> None:
    try:
        mcp = build_server()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr, flush=True)
        sys.exit(2)

    if transport == "stdio":
        await mcp.run_stdio_async()
    elif transport in {"streamable-http", "http"}:
        await mcp.run_streamable_http_async()
    elif transport == "sse":
        await mcp.run_sse_async()
    else:
        raise ValueError(f"Unsupported transport: {transport}")


def main() -> None:
    """Console-script entrypoint."""
    parser = argparse.ArgumentParser(
        prog="nautobot-mcp-server",
        description="Nautobot MCP server (stdio by default).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport to use (default: stdio).",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Override log level (DEBUG, INFO, WARNING, ERROR).",
    )
    args = parser.parse_args()

    if args.log_level:
        # Set early so any startup errors are logged at the requested level.
        configure_logging(args.log_level)

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_async_main(args.transport))


if __name__ == "__main__":
    main()
