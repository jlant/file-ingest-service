from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_APP_NAME = "file-ingest-service"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENV = "dev"
DEFAULT_RUN_SECONDS = 5
DEFAULT_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_DATA_DIR = "data"
DEFAULT_ALLOWED_SUFFIXES = (".txt", ".csv")
DEFAULT_MIN_SIZE_BYTES = 1


@dataclass(frozen=True)
class Settings:
    app_name: str = DEFAULT_APP_NAME
    log_level: str = DEFAULT_LOG_LEVEL
    env: str = DEFAULT_ENV
    run_seconds: int = DEFAULT_RUN_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    data_dir: str = DEFAULT_DATA_DIR
    allowed_suffixes: tuple[str, ...] = DEFAULT_ALLOWED_SUFFIXES
    min_size_bytes: int = DEFAULT_MIN_SIZE_BYTES


def _normalize_suffixes(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return DEFAULT_ALLOWED_SUFFIXES

    suffixes: list[str] = []
    for item in value:
        s = str(item).strip().lower()
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"
        suffixes.append(s)

    return tuple(suffixes) if suffixes else DEFAULT_ALLOWED_SUFFIXES


def load_settings(path: Path) -> Settings:
    """Load settings from defaults -> TOML file -> environment."""
    data: dict[str, object] = {}
    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8"))

    app = data.get("app", {})
    service = data.get("service", {})

    if not isinstance(app, dict):
        app = {}
    if not isinstance(service, dict):
        service = {}

    app_name = str(app.get("name", DEFAULT_APP_NAME))
    log_level = str(app.get("log_level", DEFAULT_LOG_LEVEL))
    env = str(app.get("env", DEFAULT_ENV))
    run_seconds = int(service.get("run_seconds", DEFAULT_RUN_SECONDS))
    poll_interval_seconds = float(
        service.get("poll_interval_seconds", DEFAULT_POLL_INTERVAL_SECONDS)
    )
    data_dir = str(service.get("data_dir", DEFAULT_DATA_DIR))
    allowed_suffixes = _normalize_suffixes(
        service.get("allowed_suffixes", list(DEFAULT_ALLOWED_SUFFIXES))
    )
    min_size_bytes = int(service.get("min_size_bytes", DEFAULT_MIN_SIZE_BYTES))

    app_name = os.getenv("FIS_APP_NAME", app_name)
    log_level = os.getenv("FIS_LOG_LEVEL", log_level)
    env = os.getenv("FIS_ENV", env)
    run_seconds = int(os.getenv("FIS_RUN_SECONDS", str(run_seconds)))
    poll_interval_seconds = float(
        os.getenv("FIS_POLL_INTERVAL_SECONDS", str(poll_interval_seconds))
    )
    data_dir = os.getenv("FIS_DATA_DIR", data_dir)
    min_size_bytes = int(os.getenv("FIS_MIN_SIZE_BYTES", str(min_size_bytes)))

    return Settings(
        app_name=app_name,
        log_level=log_level,
        env=env,
        run_seconds=run_seconds,
        poll_interval_seconds=poll_interval_seconds,
        data_dir=data_dir,
        allowed_suffixes=allowed_suffixes,
        min_size_bytes=min_size_bytes,
    )
