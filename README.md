---
title: OmniHub
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
python_version: 3.12
suggested_hardware: cpu-basic
suggested_storage: medium
pinned: false
---

# CustomerAgent(OmniHub)

CustomerAgent is a Python 3.12 project containing agent runtime utilities and local development tooling.

## Project Layout

- `agent/`: installable runtime package code, including `agent/client/` integrations and shared `agent/utils/` helpers.
- `tests/`: pytest test suite, organized by functional area such as `tests/client/`.
- `artifacts/local/`: local development scripts.
- `pyproject.toml`: project metadata, runtime dependencies, dev dependencies, and package discovery.
- `.env`: local environment variables. Keep this file out of committed secrets.

Generated paths such as `.venv/` and `CustomerAgent.egg-info/` are created by development tooling and should not be edited directly.

## Development Setup

Create or update the local virtual environment:

```sh
bash artifacts/local/init_dev_env.sh
```

The script creates `.venv` with Python 3.12 and installs the project in editable mode with the `dev` extra:

```sh
uv pip install --python .venv/bin/python3 -e ".[dev]"
```

## Common Commands

Run all tests:

```sh
.venv/bin/python -m pytest
```

Run client tests:

```sh
.venv/bin/python -m pytest tests/client
```

Run lint checks:

```sh
.venv/bin/ruff check .
```

## Dependencies

Runtime dependencies are listed under `[project].dependencies` in `pyproject.toml`. Development tools are listed under `[project.optional-dependencies].dev` and currently include `pytest`, `ruff`, and `pre-commit`.

## Configuration

Runtime configuration is environment-driven. Use `.env` for local values and avoid committing secrets. When adding new configuration, document the variable name, expected format, and whether it is required.
