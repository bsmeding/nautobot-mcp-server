"""Caller's Nautobot token for one MCP request.

A shared server token makes every caller the same Nautobot user.
HTTP clients send X-Nautobot-Token (or Authorization: Token).
Stdio has no headers — NAUTOBOT_TOKEN is that person's token.
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
    """Token from the MCP HTTP headers.

    X-Nautobot-Token wins. Authorization: Token is accepted.
    Authorization: Bearer is ignored — that is for the MCP endpoint, not Nautobot.
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
    """Token for this MCP message, or None."""
    return _CLIENT_TOKEN.get()


def http_request_active() -> bool:
    """True while an HTTP MCP message is running."""
    return _HTTP_REQUEST.get()


def bind_http_headers(headers: Mapping[str, str]) -> tuple[Token[str | None], Token[bool]]:
    """Store the header token on this task. Returns the reset tokens."""
    return (
        _CLIENT_TOKEN.set(token_from_headers(headers)),
        _HTTP_REQUEST.set(True),
    )


def reset_http_headers(tokens: tuple[Token[str | None], Token[bool]]) -> None:
    """Put the context vars back. tokens come from bind_http_headers."""
    _CLIENT_TOKEN.reset(tokens[0])
    _HTTP_REQUEST.reset(tokens[1])


class ClientTokenMiddleware:
    """Copy the caller's token onto the task that runs the tool."""

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
