"""Shared helpers for tool modules."""

from __future__ import annotations

from typing import Any

from ..client import NautobotClient
from ..runtime import get_client


def client() -> NautobotClient:
    """Return the active Nautobot client."""
    return get_client()


def clean_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    """Drop None and empty strings so they are not sent as query params."""
    if not filters:
        return {}
    return {k: v for k, v in filters.items() if v is not None and v != ""}


async def lookup_id_or_name(
    endpoint: str,
    identifier: str,
    *,
    name_field: str = "name",
) -> dict[str, Any]:
    """Object by UUID, or by name when the id lookup is a 404."""
    import httpx

    cli = client()
    try:
        return await cli.rest_get_object(endpoint, identifier)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise

    page = await cli.rest_get(endpoint, params={name_field: identifier, "limit": 2})
    results = (page or {}).get("results") or []
    if not results:
        raise ValueError(
            f"No object found at {endpoint} with id or {name_field}={identifier!r}"
        )
    if len(results) > 1:
        raise ValueError(
            f"Ambiguous lookup at {endpoint}: multiple objects matched "
            f"{name_field}={identifier!r}"
        )
    return results[0]
