"""MCP server entrypoint for Nautobot.

Run as a stdio MCP server::

    nautobot-mcp

Or programmatically::

    from nautobot_mcp.server import build_server, main
    main()
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import __version__
from .client import NautobotClient
from .config import NautobotMcpSettings, load_settings
from .logging_config import configure_logging
from .runtime import set_client, set_settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("nautobot_mcp.server")

# Loopback by default so a local stdio-style HTTP listener is not reachable
# from the network. Override with --host / NAUTOBOT_MCP_HOST for a reverse proxy.
_DEFAULT_HTTP_HOST = "127.0.0.1"
_DEFAULT_HTTP_PORT = 8000
_HTTP_TRANSPORTS = frozenset({"streamable-http", "http", "sse"})


def resolve_http_bind(host: str | None, port: int | None) -> tuple[str, int]:
    """Resolve the HTTP/SSE listen address.

    CLI values win over ``NAUTOBOT_MCP_HOST`` / ``NAUTOBOT_MCP_PORT``.
    """
    resolved_host = (host or os.getenv("NAUTOBOT_MCP_HOST") or _DEFAULT_HTTP_HOST).strip()
    if not resolved_host:
        resolved_host = _DEFAULT_HTTP_HOST

    if port is not None:
        resolved_port = port
    else:
        raw_port = os.getenv("NAUTOBOT_MCP_PORT")
        if raw_port is None or raw_port.strip() == "":
            resolved_port = _DEFAULT_HTTP_PORT
        else:
            try:
                resolved_port = int(raw_port)
            except ValueError as exc:
                raise ValueError(
                    f"NAUTOBOT_MCP_PORT must be an integer, got {raw_port!r}."
                ) from exc

    if not 0 <= resolved_port <= 65535:
        raise ValueError(f"HTTP port must be between 0 and 65535, got {resolved_port}.")
    return resolved_host, resolved_port


def build_server(settings: NautobotMcpSettings | None = None) -> MCPServer:
    """Construct a configured MCP server.

    The actual NautobotClient is created in the ``lifespan`` so the
    HTTP connection is opened only when the server starts (this matters
    for cleanly closing the client on shutdown).
    """
    from mcp.server.mcpserver import MCPServer  # local import keeps import cost low

    from .tools import register_all

    resolved = settings or load_settings()
    set_settings(resolved)
    configure_logging(resolved.log_level)
    logger.info("Nautobot MCP server starting; settings=%s", resolved.redacted())

    @asynccontextmanager
    async def lifespan(_server: MCPServer) -> AsyncIterator[dict[str, Any]]:
        client = NautobotClient(resolved)
        set_client(client)
        try:
            yield {"client": client, "settings": resolved}
        finally:
            await client.aclose()
            logger.info("Nautobot MCP server shut down cleanly")

    mcp = MCPServer(
        "nautobot-mcp",
        instructions=(
            "Tools for interacting with a Nautobot instance via its built-in "
            "REST and GraphQL APIs. Start with `nautobot_status` and "
            "`list_api_roots` for discovery, then use domain-specific tools "
            "(DCIM, IPAM, circuits, virtualization, extras, jobs) or fall "
            "back to the generic `rest_list` / `rest_get` tools for any "
            "endpoint not covered by a wrapper."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    register_all(mcp)
    return mcp


async def _async_main(
    transport: str,
    *,
    host: str | None = None,
    port: int | None = None,
) -> None:
    try:
        mcp = build_server()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr, flush=True)
        sys.exit(2)

    if transport == "stdio":
        await mcp.run_stdio_async()
        return

    bind_host = host if host is not None else _DEFAULT_HTTP_HOST
    bind_port = port if port is not None else _DEFAULT_HTTP_PORT
    if transport in {"streamable-http", "http"}:
        logger.info("Streamable HTTP MCP endpoint at http://%s:%s/mcp", bind_host, bind_port)
        await mcp.run_streamable_http_async(host=bind_host, port=bind_port)
    elif transport == "sse":
        logger.info("SSE MCP endpoint at http://%s:%s/sse", bind_host, bind_port)
        await mcp.run_sse_async(host=bind_host, port=bind_port)
    else:
        raise ValueError(f"Unsupported transport: {transport}")


def main() -> None:
    """Console-script entrypoint."""
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).name,
        description="Nautobot MCP server (stdio by default).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport to use (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default=None,
        help=(
            "Bind address for streamable-http and sse "
            f"(default: {_DEFAULT_HTTP_HOST}, or NAUTOBOT_MCP_HOST). "
            "Use 0.0.0.0 when a reverse proxy on another host connects in."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=(
            "Bind port for streamable-http and sse "
            f"(default: {_DEFAULT_HTTP_PORT}, or NAUTOBOT_MCP_PORT)."
        ),
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

    host: str | None = None
    port: int | None = None
    if args.transport in _HTTP_TRANSPORTS:
        try:
            host, port = resolve_http_bind(args.host, args.port)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr, flush=True)
            sys.exit(2)

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_async_main(args.transport, host=host, port=port))


if __name__ == "__main__":
    main()
