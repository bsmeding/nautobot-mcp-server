"""Per-client Nautobot API token for one MCP request.

A shared server token makes every caller look like the same Nautobot user.
HTTP transports (streamable HTTP and SSE) carry the caller's token on the
request. The middleware below stores it in a context variable for the
duration of that message, and :class:`nautobot_mcp.client.NautobotClient`
sends it as ``Authorization: Token …``. Nautobot then attributes the API
call — including the change log — to that token's user.

Stdio has no request headers. There the process ``NAUTOBOT_TOKEN`` is the
caller's token, which is already one identity per local MCP client.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar, Token
from typing import Any

_CLIENT_TOKEN: ContextVar[str | None] = ContextVar(
    "nautobot_mcp_client_token", default=None
)
_HTTP_REQUEST: ContextVar[bool] = ContextVar(
    "nautobot_mcp_http_request", default=False
)

_TOKEN_HEADER = "x-nautobot-token"


def token_from_headers(headers: Mapping[str, str] | None) -> str | None:
    """Return the caller's Nautobot token from MCP HTTP headers.

    ``X-Nautobot-Token`` wins. ``Authorization: Token <key>`` is also
    accepted. ``Authorization: Bearer`` is left alone so an OAuth token
    used to reach the MCP endpoint is not forwarded to Nautobot.
    """
    if not headers:
        return None

    found: dict[str, str] = {}
    for key, value in headers.items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            found[str(key).lower()] = text

    explicit = found.get(_TOKEN_HEADER)
    if explicit:
        return explicit

    authorization = found.get("authorization", "")
    scheme, _, rest = authorization.partition(" ")
    if scheme.lower() == "token" and rest.strip():
        return rest.strip()
    return None


def current_client_token() -> str | None:
    """Token bound for the current MCP message, if the caller sent one."""
    return _CLIENT_TOKEN.get()


def http_request_active() -> bool:
    """True while handling an HTTP MCP message (headers were present)."""
    return _HTTP_REQUEST.get()


def bind_http_headers(headers: Mapping[str, str]) -> tuple[Token[str | None], Token[bool]]:
    """Bind the token from ``headers`` for the current task."""
    return (
        _CLIENT_TOKEN.set(token_from_headers(headers)),
        _HTTP_REQUEST.set(True),
    )


def reset_http_headers(tokens: tuple[Token[str | None], Token[bool]]) -> None:
    """Restore the context vars saved by :func:`bind_http_headers`."""
    _CLIENT_TOKEN.reset(tokens[0])
    _HTTP_REQUEST.reset(tokens[1])


class ClientTokenMiddleware:
    """Copy the caller's Nautobot token onto the task that runs the tool."""

    async def __call__(self, ctx: Any, call_next: Any) -> Any:
        request = getattr(ctx, "request", None)
        headers = getattr(request, "headers", None) if request is not None else None
        if headers is None:
            return await call_next(ctx)
        tokens = bind_http_headers(headers)
        try:
            return await call_next(ctx)
        finally:
            reset_http_headers(tokens)
