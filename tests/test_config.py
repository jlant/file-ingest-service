"""Tests for the config entry point.

resolve_settings is a thin wrapper over load_settings (defaulting the path), so
these tests cover only that wrapper behavior; resolution itself is covered in
test_settings.py.
"""

from __future__ import annotations

from pathlib import Path

from file_ingest_service.config import resolve_settings
from file_ingest_service.settings import DEFAULT_APP_NAME


def test_missing_path_falls_back_to_defaults() -> None:
    settings = resolve_settings(Path("nonexistent_config_for_testing.toml"))
    assert settings.app_name == DEFAULT_APP_NAME
    assert settings.env == "DEV"


def test_explicit_path_is_used(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text('[app]\nname = "config-test-app"\nlog_level = "DEBUG"\n', encoding="utf-8")

    settings = resolve_settings(path)

    assert settings.app_name == "config-test-app"
    assert settings.log_level == "DEBUG"
