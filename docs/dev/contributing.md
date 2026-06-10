# Contributing

## Setup

```bash
pip install -e ".[dev]"
```

## Quality gates

```bash
ruff check nautobot_mcp_server tests   # or: invoke lint
ruff format nautobot_mcp_server tests  # or: invoke format
pytest -v                              # or: invoke unittest
```

`invoke tests` runs lint then the unit tests.

## Conventions

- Code targets Python 3.10+ and is type-annotated (`from __future__ import
  annotations`).
- Ruff enforces style and import order (`E`, `F`, `I`, `UP`, `B`, `SIM`,
  `RUF`).
- Tests use `pytest` + `respx` to mock Nautobot's HTTP API; no live Nautobot is
  required for the unit suite.
- New tools live under `nautobot_mcp_server/tools/`; each module exposes a
  `register(mcp)` function. Plugin integrations go under `tools/plugins/` and
  self-gate via `DIST_PACKAGES` (see
  [Plugin Integrations](../user/plugins.md)).

## Building docs

```bash
pip install -e ".[docs]"
mkdocs serve
```
