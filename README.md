# File Ingest Service

A directory watcher ingestion service that detects new files, validates them, moves them through an inbox/processed/error steps, and logs each step.

## Tools

- [uv](https://docs.astral.sh/uv/) — package and environment management
- [ruff](https://docs.astral.sh/ruff/) — linting and formatting
- [pyright](https://github.com/microsoft/pyright) — static type checking
- [pytest](https://pytest.org) — testing with coverage enforcement
- [nox](https://nox.thea.codes) — session automation
- [pre-commit](https://pre-commit.com) — git hook management
- [Typer](https://typer.tiangolo.com) — CLI interface
- TOML as the default config format
- YAML only for multi-step orchestration
- `src/` layout

## Quick start

```bash
uv run fis --help
uv run fis hello
uv run fis hello -n Jeremiah
uv run fis read-config
uv run fis run
APP_LOG_LEVEL=DEBUG APP_RUN_SECONDS=0 uv run fis run
```

## Development workflow

```bash
uv lock
uv sync --all-extras --dev
pre-commit install

# Format
uv run nox -s fmt

# Lint + type check
uv run nox -s lint

# Run tests
uv run nox -s tests

# Check template reads config file
uv run fis read-config

# Check template runs service
uv run fis run
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details on the development workflow and
guidelines for contributors.
