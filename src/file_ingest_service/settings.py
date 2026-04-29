from __future__ import annotations

import logging
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_APP_NAME = "file-ingest-service"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENV = "DEV"
DEFAULT_RUN_SECONDS = 5
DEFAULT_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_DATA_DIR = "data"
DEFAULT_ALLOWED_SUFFIXES = (".csv", ".dat", ".txt")
DEFAULT_MIN_SIZE_BYTES = 1

ENV_PREFIX = "APP"

VALID_LOG_LEVELS: frozenset[str] = frozenset(logging.getLevelNamesMapping().keys())
VALID_ENVS: frozenset[str] = frozenset({"DEV", "TEST", "PROD"})


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

    def __post_init__(self) -> None:
        if self.log_level not in VALID_LOG_LEVELS:
            msg = f"log_level must be one of {VALID_LOG_LEVELS}, got {self.log_level}"
            raise ValueError(msg)
        if self.env not in VALID_ENVS:
            msg = f"env must be one of {VALID_ENVS}, got {self.env}"
            raise ValueError(msg)
        if self.run_seconds < 0:
            msg = f"run_seconds must be >= 0, got {self.run_seconds}"
            raise ValueError(msg)
        if self.poll_interval_seconds < 0:
            msg = f"poll_interval_seconds must be >= 0, got {self.poll_interval_seconds}"
            raise ValueError(msg)
        if self.min_size_bytes < 1:
            msg = f"min_size_bytes must be >= 1, got {self.min_size_bytes}"
            raise ValueError(msg)


def _normalize_suffixes(value: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    suffixes: list[str] = []
    for item in value:
        s = str(item).strip().lower()
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"

        suffixes.append(s)

    return tuple(suffixes) if suffixes else DEFAULT_ALLOWED_SUFFIXES


def _settings_from_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _settings_from_env() -> dict[str, Any]:
    """Collect only env vars that are explicitly set."""
    result: dict[str, Any] = {}
    mapping = {
        "app_name": f"{ENV_PREFIX}_NAME",
        "log_level": f"{ENV_PREFIX}_LOG_LEVEL",
        "env": f"{ENV_PREFIX}_ENV",
        "run_seconds": f"{ENV_PREFIX}_RUN_SECONDS",
        "poll_interval_seconds": f"{ENV_PREFIX}_POLL_INTERVAL_SECONDS",
        "data_dir": f"{ENV_PREFIX}_DATA_DIR",
        "allowed_suffixes": f"{ENV_PREFIX}_ALLOWED_SUFFIXES",
        "min_size_bytes": f"{ENV_PREFIX}_MIN_SIZE_BYTES",
    }
    for key, env_var in mapping.items():
        value = os.getenv(env_var)
        if value is not None:
            result[key] = value

    return result


def _resolve(env_val: Any, toml_val: Any, default: Any) -> Any:
    """Return the first non-None value in priority order: env > toml > default."""
    if env_val is not None:
        return env_val
    if toml_val is not None:
        return toml_val
    return default


def load_settings(path: Path) -> Settings:
    toml_data = _settings_from_toml(path)
    toml_app = toml_data.get("app", {})
    toml_svc = toml_data.get("service", {})
    env_data = _settings_from_env()

    raw_suffixes = env_data.get("allowed_suffixes")
    if raw_suffixes is not None:
        allowed_suffixes = _normalize_suffixes(re.split(r"[,;\s]+", raw_suffixes))
    else:
        allowed_suffixes = _normalize_suffixes(
            list(toml_svc.get("allowed_suffixes", DEFAULT_ALLOWED_SUFFIXES))
        )

    return Settings(
        app_name=str(_resolve(env_data.get("app_name"), toml_app.get("name"), DEFAULT_APP_NAME)),
        log_level=str(
            _resolve(env_data.get("log_level"), toml_app.get("log_level"), DEFAULT_LOG_LEVEL)
        ).upper(),
        env=str(_resolve(env_data.get("env"), toml_app.get("env"), DEFAULT_ENV)).upper(),
        run_seconds=int(
            _resolve(env_data.get("run_seconds"), toml_svc.get("run_seconds"), DEFAULT_RUN_SECONDS)
        ),
        poll_interval_seconds=float(
            _resolve(
                env_data.get("poll_interval_seconds"),
                toml_svc.get("poll_interval_seconds"),
                DEFAULT_POLL_INTERVAL_SECONDS,
            )
        ),
        data_dir=str(
            _resolve(env_data.get("data_dir"), toml_svc.get("data_dir"), DEFAULT_DATA_DIR)
        ),
        allowed_suffixes=allowed_suffixes,
        min_size_bytes=int(
            _resolve(
                env_data.get("min_size_bytes"),
                toml_svc.get("min_size_bytes"),
                DEFAULT_MIN_SIZE_BYTES,
            )
        ),
    )
