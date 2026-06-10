"""Invoke tasks for the nautobot-mcp-server development environment.

Usage examples::

    invoke build              # build the dev image
    invoke start              # start Nautobot + db + redis (detached)
    invoke debug              # start in the foreground with logs
    invoke stop               # stop containers
    invoke destroy            # stop and remove containers + volumes
    invoke migrate            # run database migrations
    invoke createsuperuser    # create the dev superuser
    invoke nbshell            # open a nautobot-server shell
    invoke cli                # open a bash shell in the nautobot container
    invoke lint               # ruff check
    invoke format             # ruff format + autofix
    invoke unittest           # run pytest (standalone, no containers)
    invoke tests              # lint + unittest

The container tasks shell out to docker compose using the development/ files.
Standalone tasks (lint, format, unittest) run locally without containers.
"""

from __future__ import annotations

import os

from invoke import task

NAUTOBOT_VER = os.getenv("NAUTOBOT_VER", "2.4")
PYTHON_VER = os.getenv("PYTHON_VER", "3.12")

COMPOSE_DIR = "development"
COMPOSE_FILES = [
    "docker-compose.base.yml",
    "docker-compose.redis.yml",
    "docker-compose.postgres.yml",
    "docker-compose.dev.yml",
]


def _compose_cmd() -> str:
    files = " ".join(f"-f {f}" for f in COMPOSE_FILES)
    return f"docker compose --project-name nautobot_mcp_server {files}"


def _run_compose(context, command: str, **kwargs) -> None:
    with context.cd(COMPOSE_DIR):
        env = {"NAUTOBOT_VER": NAUTOBOT_VER, "PYTHON_VER": PYTHON_VER}
        context.run(f"{_compose_cmd()} {command}", env=env, pty=True, **kwargs)


def _exec_nautobot(context, command: str) -> None:
    _run_compose(context, f'exec nautobot bash -c "{command}"')


# ---- container lifecycle ----------------------------------------------


@task
def build(context):
    """Build the Nautobot development image with the app installed."""
    _run_compose(context, "build")


@task
def start(context):
    """Start the development environment (detached)."""
    _run_compose(context, "up -d")


@task
def debug(context):
    """Start the development environment in the foreground with logs."""
    _run_compose(context, "up")


@task
def stop(context):
    """Stop the development environment."""
    _run_compose(context, "down")


@task
def destroy(context):
    """Stop and remove containers and volumes."""
    _run_compose(context, "down --volumes")


@task
def logs(context):
    """Tail logs from the nautobot container."""
    _run_compose(context, "logs -f nautobot")


# ---- nautobot management ----------------------------------------------


@task
def migrate(context):
    """Run database migrations."""
    _exec_nautobot(context, "nautobot-server migrate")


@task
def createsuperuser(context):
    """Create the development superuser."""
    _exec_nautobot(context, "nautobot-server createsuperuser")


@task
def nbshell(context):
    """Open a nautobot-server shell."""
    _run_compose(context, "exec nautobot nautobot-server nbshell")


@task
def cli(context):
    """Open a bash shell inside the nautobot container."""
    _run_compose(context, "exec nautobot bash")


# ---- quality (run locally, no containers) -----------------------------


@task
def lint(context):
    """Run ruff lint checks."""
    context.run("ruff check nautobot_mcp_server tests", pty=True)


@task
def format(context):  # matches NTC task naming
    """Auto-format and apply safe lint fixes with ruff."""
    context.run("ruff format nautobot_mcp_server tests", pty=True)
    context.run("ruff check --fix nautobot_mcp_server tests", pty=True)


@task
def unittest(context):
    """Run the standalone test suite with pytest."""
    context.run("pytest -v", pty=True)


@task
def tests(context):
    """Run lint then the unit tests."""
    lint(context)
    unittest(context)
