# Repository Guidelines

## Project Structure & Organization

Keep source code, tests, and local tooling separated by purpose. Runtime package code should live under `agent/`, with domain integrations under subpackages such as `agent/client/` and shared helpers under `agent/utils/`. Tests should live under `tests/` and may be organized by functional area, for example `tests/client/` for client integration utilities. Local scripts and generated support files belong under `artifacts/` or another clearly named tooling directory.

Do not edit generated directories such as `.venv/` or `*.egg-info/` by hand. Update source configuration or setup scripts instead.

## Development Commands

Use the repository setup script to prepare the local environment:

```sh
bash artifacts/local/init_dev_env.sh
```

Run tests through the project virtual environment:

```sh
.venv/bin/python -m pytest
```

Run lint checks with:

```sh
.venv/bin/ruff check .
```

## Coding Style & Naming

Use Python 3.12 syntax, 4-space indentation, and clear names. Use `snake_case` for functions, methods, and variables; use `PascalCase` for classes. Prefer explicit imports and small modules with one clear responsibility.

Keep configuration in `pyproject.toml` where possible. Avoid broad packaging rules that accidentally include local tooling, generated files, or test artifacts.

## Testing Guidelines

Use `pytest` for tests. Name test files `test_*.py` and test functions `test_*`. Keep unit tests deterministic and avoid requiring external services unless the test is explicitly marked or documented as an integration test.

When adding behavior, add or update focused tests close to the changed area. Include the exact test command in handoff notes or pull request descriptions.

## Commit & Pull Request Guidelines

Use short, imperative commit messages, for example `Update MongoDB utility tests` or `Fix environment setup script`. Keep commits scoped to one logical change.

Pull requests should include a brief summary, verification commands, and any required environment variables or service assumptions. Call out skipped tests and explain why they were skipped.

## Configuration & Secrets

Keep secrets out of version control. Store local values in `.env` or the execution environment. Do not commit credentials, tokens, private URLs, or machine-specific virtual environment files.
