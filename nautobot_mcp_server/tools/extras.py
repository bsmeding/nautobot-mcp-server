"""Extras tools: jobs, job results, statuses, tags, custom fields, etc."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._helpers import clean_filters, client, lookup_id_or_name


def register(mcp: FastMCP) -> None:
    # ---- jobs ---------------------------------------------------------

    @mcp.tool()
    async def list_jobs(
        filters: dict[str, Any] | None = None,
        paginate: bool = True,
    ) -> Any:
        """List installed jobs. Filters: ``enabled``, ``installed``,
        ``has_sensitive_variables``, ``q`` (free-text)."""
        return await client().rest_list(
            "/api/extras/jobs/",
            filters=clean_filters(filters),
            paginate=paginate,
        )

    @mcp.tool()
    async def get_job(name_or_id: str) -> dict[str, Any]:
        """Fetch a job by UUID or by ``name``."""
        return await lookup_id_or_name("/api/extras/jobs/", name_or_id)

    @mcp.tool()
    async def run_job(
        job_name_or_id: str,
        data: dict[str, Any] | None = None,
        commit: bool = True,
        schedule: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger a Nautobot job. Returns the created job result.

        Args:
            job_name_or_id: Job UUID or job name (class path).
            data: Input variables for the job.
            commit: Whether the job should commit DB changes (Nautobot 2.x
                ignores this for read-only jobs).
            schedule: Optional schedule dict (``{"interval": "future",
                "start_time": "..."}``) to defer the run.

        Note: even though this triggers a mutation, Nautobot job runs are
        always exposed via POST regardless of read-only mode. Each job
        enforces its own permissions, so the MCP write-gate does **not**
        block job runs by default — but jobs that mutate Nautobot data
        will still fail if the configured token lacks write permission.
        """
        job = await lookup_id_or_name("/api/extras/jobs/", job_name_or_id)
        payload: dict[str, Any] = {"data": data or {}, "commit": commit}
        if schedule:
            payload["schedule"] = schedule
        # Job execution is a legitimate POST that is gated by Nautobot's
        # own per-job permissions, so we route it through the underlying
        # httpx client instead of the write-gated _request().
        cli = client()
        resp = await cli._client.post(
            f"/api/extras/jobs/{job['id']}/run/", json=payload
        )
        resp.raise_for_status()
        return resp.json()

    @mcp.tool()
    async def get_job_result(result_id: str) -> dict[str, Any]:
        """Fetch a single job result by UUID."""
        return await client().rest_get_object(
            "/api/extras/job-results/", result_id
        )

    @mcp.tool()
    async def list_recent_job_results(
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> Any:
        """List recent job results, newest first. Filters: ``status``,
        ``job_model``, ``user``."""
        merged = clean_filters(filters)
        merged.setdefault("ordering", "-created")
        return await client().rest_list(
            "/api/extras/job-results/",
            filters=merged,
            limit=limit,
            paginate=False,
        )

    @mcp.tool()
    async def get_job_logs(result_id: str, paginate: bool = True) -> Any:
        """Return the log entries for a job result."""
        return await client().rest_list(
            "/api/extras/job-log-entries/",
            filters={"job_result": result_id},
            paginate=paginate,
        )

    # ---- statuses, tags, roles ---------------------------------------

    @mcp.tool()
    async def list_statuses(
        content_type: str | None = None,
    ) -> Any:
        """List status objects. Optionally filter to a content type
        (e.g. ``dcim.device``)."""
        filters: dict[str, Any] = {}
        if content_type:
            filters["content_types"] = content_type
        return await client().rest_list(
            "/api/extras/statuses/", filters=filters, paginate=True
        )

    @mcp.tool()
    async def list_tags(
        content_type: str | None = None,
    ) -> Any:
        """List tags. Optionally scope to a content type."""
        filters: dict[str, Any] = {}
        if content_type:
            filters["content_types"] = content_type
        return await client().rest_list(
            "/api/extras/tags/", filters=filters, paginate=True
        )

    @mcp.tool()
    async def list_roles(
        content_type: str | None = None,
    ) -> Any:
        """List roles (Nautobot 2.x unified Role model)."""
        filters: dict[str, Any] = {}
        if content_type:
            filters["content_types"] = content_type
        return await client().rest_list(
            "/api/extras/roles/", filters=filters, paginate=True
        )

    # ---- custom fields, relationships, computed fields ---------------

    @mcp.tool()
    async def list_custom_fields(
        content_type: str | None = None,
    ) -> Any:
        """List custom field definitions, optionally scoped by content type."""
        filters: dict[str, Any] = {}
        if content_type:
            filters["content_types"] = content_type
        return await client().rest_list(
            "/api/extras/custom-fields/", filters=filters, paginate=True
        )

    @mcp.tool()
    async def list_relationships() -> Any:
        """List relationship definitions."""
        return await client().rest_list(
            "/api/extras/relationships/", paginate=True
        )

    @mcp.tool()
    async def list_computed_fields(
        content_type: str | None = None,
    ) -> Any:
        """List computed field definitions."""
        filters: dict[str, Any] = {}
        if content_type:
            filters["content_type"] = content_type
        return await client().rest_list(
            "/api/extras/computed-fields/", filters=filters, paginate=True
        )

    @mcp.tool()
    async def list_config_contexts(
        filters: dict[str, Any] | None = None,
    ) -> Any:
        """List config contexts."""
        return await client().rest_list(
            "/api/extras/config-contexts/",
            filters=clean_filters(filters),
            paginate=True,
        )

    # ---- webhooks, secrets (metadata only) ---------------------------

    @mcp.tool()
    async def list_webhooks() -> Any:
        """List webhook definitions."""
        return await client().rest_list(
            "/api/extras/webhooks/", paginate=True
        )

    @mcp.tool()
    async def list_secrets_groups() -> Any:
        """List secrets groups (does not return secret values)."""
        return await client().rest_list(
            "/api/extras/secrets-groups/", paginate=True
        )
