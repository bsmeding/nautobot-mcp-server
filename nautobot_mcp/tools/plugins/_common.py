"""Shared helpers for plugin tool modules.

Most NetworkToCode apps drive their behavior through Nautobot **Jobs**
rather than bespoke REST models, so these helpers make it easy to list
and run an app's jobs, and to hit its ``/api/plugins/<app>/`` namespace
generically.
"""

from __future__ import annotations

from typing import Any

from .._helpers import client


async def list_jobs_matching(q: str | None = None) -> Any:
    """List installed jobs, optionally free-text filtered (Nautobot ``q``)."""
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
    """Trigger a Nautobot job by UUID or name and return the job result.

    Job runs are POSTs gated by Nautobot's own per-job permissions, so this
    deliberately bypasses the MCP write-gate (mirroring ``extras.run_job``).
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
