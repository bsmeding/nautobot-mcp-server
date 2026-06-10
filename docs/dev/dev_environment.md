# Development Environment

A Docker-based Nautobot environment is provided under `development/`, driven by
[invoke](https://www.pyinvoke.org/) tasks (`tasks.py`).

## Prerequisites

- Docker + Docker Compose
- `pip install -e ".[dev]"` (provides `invoke`, `ruff`, `pytest`)

## First run

```bash
cp development/creds.example.env development/creds.env   # then edit secrets
invoke build
invoke start
invoke migrate
invoke createsuperuser   # if not auto-created via creds.env
```

Nautobot is then available at <http://localhost:8080> with this app enabled.
The repository is mounted into the container, so code changes reload live.

## Common tasks

| Task | Description |
| --- | --- |
| `invoke build` | Build the dev image with the app installed editable. |
| `invoke start` / `invoke stop` | Start / stop the stack (detached). |
| `invoke debug` | Start in the foreground with logs. |
| `invoke destroy` | Remove containers and volumes. |
| `invoke nbshell` | Open a `nautobot-server` shell. |
| `invoke cli` | Bash shell in the nautobot container. |
| `invoke lint` / `invoke format` | Ruff check / autoformat. |
| `invoke unittest` / `invoke tests` | Run pytest / lint+pytest. |

## Files

- `development/Dockerfile` — Nautobot dev image with the app installed.
- `development/docker-compose.*.yml` — base + redis + postgres + dev overlays.
- `development/development.env` — non-secret settings (committed).
- `development/creds.example.env` — template for secrets (copy to `creds.env`).
- `development/nautobot_config.py` — Nautobot config enabling the app.
