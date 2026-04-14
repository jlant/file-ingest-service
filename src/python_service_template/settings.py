from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_APP_NAME = "python-service-template"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENV = "dev"
DEFAULT_RUN_SECONDS = 1


@dataclass(frozen=True)
class Settings:
    app_name: str = DEFAULT_APP_NAME
    log_level: str = DEFAULT_LOG_LEVEL
    env: str = DEFAULT_ENV
    run_seconds: int = DEFAULT_RUN_SECONDS


def load_settings(path: Path) -> Settings:
    """Load settings from defaults -> TOML file -> environment.

    Expected TOML shape:

    [app]
    name = "..."
    log_level = "..."
    env = "dev"

    [service]
    run_seconds = 5

    Supported environment overrides:
      PST_APP_NAME
      PST_LOG_LEVEL
      PST_ENV
      PST_RUN_SECONDS
    """
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

    app_name = os.getenv("PST_APP_NAME", app_name)
    log_level = os.getenv("PST_LOG_LEVEL", log_level)
    env = os.getenv("PST_ENV", env)
    run_seconds = int(os.getenv("PST_RUN_SECONDS", str(run_seconds)))

    return Settings(
        app_name=app_name,
        log_level=log_level,
        env=env,
        run_seconds=run_seconds,
    )
