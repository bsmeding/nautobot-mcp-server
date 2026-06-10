"""Tools for the Nautobot SSoT app (``nautobot-ssot``).

SSoT (Single Source of Truth) synchronizes data between Nautobot and
external systems via DiffSync-based Jobs. Each run is recorded as a "Sync"
with associated log entries. These tools list/inspect sync history and run
SSoT data source/target jobs.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import list_jobs_matching, plugin_rest_list, run_job_by_name_or_id

KEY = "ssot"
DIST_PACKAGES: tuple[str, ...] = ("nautobot_ssot",)
APP_URL = "ssot"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_ssot_jobs() -> Any:
        """List installed SSoT data source/target jobs."""
        return await list_jobs_matching("sync")

    @mcp.tool()
    async def list_ssot_syncs(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List recorded SSoT syncs (run history).

        Endpoint: ``/api/plugins/ssot/sync/``. If your SSoT version does not
        expose REST sync records, fall back to ``list_recent_job_results``.
        """
        return await plugin_rest_list(
            APP_URL, "sync", filters=filters, paginate=paginate
        )

    @mcp.tool()
    async def list_ssot_sync_logs(
        filters: dict[str, Any] | None = None,
        paginate: bool = True,
    ) -> Any:
        """List SSoT sync log entries. Filter by ``sync`` (sync UUID).

        Endpoint: ``/api/plugins/ssot/sync-log-entries/``.
        """
        return await plugin_rest_list(
            APP_URL, "sync-log-entries", filters=filters, paginate=paginate
        )

    @mcp.tool()
    async def run_ssot_sync(
        job_name_or_id: str,
        data: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Run an SSoT sync job (data source or target) and return the result.

        Args:
            job_name_or_id: SSoT job UUID or class-path name (use
                ``list_ssot_jobs`` to discover it).
            data: Job inputs (often includes ``dry_run`` and a credentials /
                config selection -- inspect with ``get_job`` first).
            commit: Whether the job should commit changes.
        """
        return await run_job_by_name_or_id(job_name_or_id, data, commit=commit)
