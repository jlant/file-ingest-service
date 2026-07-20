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
DEFAULT_LOG_FILE = "logs/file_ingest_service.log"
DEFAULT_DATA_DIR = "data"
DEFAULT_ALLOWED_SUFFIXES = (".csv", ".dat", ".txt")
DEFAULT_MIN_SIZE_BYTES = 1

ENV_PREFIX = "APP"

VALID_LOG_LEVELS: frozenset[str] = frozenset(logging.getLevelNamesMapping().keys())
VALID_ENVS: frozenset[str] = frozenset({"DEV", "TEST", "PROD"})

# Fields that must be non-empty when running in PROD. A misconfigured production
# deploy should fail loudly at startup naming what is missing, rather than
# failing later with a confusing error deep in the run.
REQUIRED_IN_PROD: tuple[str, ...] = ("data_dir",)


def _normalize_suffixes(value: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Return suffixes lowercased, dot-prefixed, and blanks removed."""
    suffixes: list[str] = []
    for item in value:
        s = str(item).strip().lower()
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"
        suffixes.append(s)

    return tuple(suffixes) if suffixes else DEFAULT_ALLOWED_SUFFIXES


@dataclass(frozen=True)
class Settings:
    app_name: str = DEFAULT_APP_NAME
    log_level: str = DEFAULT_LOG_LEVEL
    env: str = DEFAULT_ENV
    log_file: str = DEFAULT_LOG_FILE
    data_dir: str = DEFAULT_DATA_DIR
    allowed_suffixes: tuple[str, ...] = DEFAULT_ALLOWED_SUFFIXES
    min_size_bytes: int = DEFAULT_MIN_SIZE_BYTES

    def __post_init__(self) -> None:
        if self.log_level not in VALID_LOG_LEVELS:
            msg = f"log_level must be one of {sorted(VALID_LOG_LEVELS)}, got {self.log_level!r}"
            raise ValueError(msg)
        if self.env not in VALID_ENVS:
            msg = f"env must be one of {sorted(VALID_ENVS)}, got {self.env!r}"
            raise ValueError(msg)
        if self.min_size_bytes < 1:
            msg = f"min_size_bytes must be >= 1, got {self.min_size_bytes}"
            raise ValueError(msg)

        # Normalize on EVERY construction path (not just load_settings), so the
        # field is always a lowercased, dot-prefixed tuple however Settings was
        # built. Frozen dataclass, so assign via object.__setattr__.
        object.__setattr__(self, "allowed_suffixes", _normalize_suffixes(self.allowed_suffixes))

        # Fail fast in PROD if any required field is blank.
        if self.env == "PROD":
            missing = [name for name in REQUIRED_IN_PROD if not str(getattr(self, name)).strip()]
            if missing:
                msg = (
                    "the following settings are required in PROD but are empty: "
                    f"{', '.join(missing)}"
                )
                raise ValueError(msg)


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
        "log_file": f"{ENV_PREFIX}_LOG_FILE",
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
        log_file=str(
            _resolve(env_data.get("log_file"), toml_app.get("log_file"), DEFAULT_LOG_FILE)
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
