"""Helpers for the app tools. Most of those apps run as Nautobot Jobs."""

from __future__ import annotations

from typing import Any

from .._helpers import client


async def list_jobs_matching(q: str | None = None) -> Any:
    """Installed jobs. q is Nautobot's free-text filter."""
    filters: dict[str, Any] = {}
    if q:
        filters["q"] = q
    return await client().rest_list(
        "/api/extras/jobs/", filters=filters, paginate=True
    )


async def run_job_by_name_or_id(
    job_name_or_id: str,
    data: dict[str, Any] | None = None,
    *,
    commit: bool = True,
    schedule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a job by UUID or name.

    This POST skips the MCP write lock. Nautobot still checks the job permission.
    """
    from .._helpers import lookup_id_or_name

    job = await lookup_id_or_name("/api/extras/jobs/", job_name_or_id)
    payload: dict[str, Any] = {"data": data or {}, "commit": commit}
    if schedule:
        payload["schedule"] = schedule
    cli = client()
    resp = await cli._client.post(
        f"/api/extras/jobs/{job['id']}/run/", json=payload
    )
    resp.raise_for_status()
    return resp.json()


async def plugin_rest_list(
    app_url: str,
    resource: str,
    filters: dict[str, Any] | None = None,
    *,
    paginate: bool = False,
) -> Any:
    """List a resource under ``/api/plugins/<app_url>/<resource>/``."""
    endpoint = f"/api/plugins/{app_url.strip('/')}/{resource.strip('/')}/"
    return await client().rest_list(endpoint, filters=filters, paginate=paginate)
