from pathlib import Path

import pytest

from file_ingest_service.settings import (
    DEFAULT_ALLOWED_SUFFIXES,
    DEFAULT_APP_NAME,
    DEFAULT_DATA_DIR,
    DEFAULT_ENV,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MIN_SIZE_BYTES,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_RUN_SECONDS,
    ENV_PREFIX,
    Settings,
    _normalize_suffixes,  # type: ignore
    load_settings,
)


def test_load_settings_from_valid_toml_file(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "test-service"
log_level = "DEBUG"
env = "TEST"

[service]
run_seconds = 5
poll_interval_seconds = 0.5
data_dir = "data"
allowed_suffixes = [".csv", ".dat", ".txt"]
min_size_bytes = 3
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == "test-service"
    assert settings.log_level == "DEBUG"
    assert settings.env == "TEST"
    assert settings.run_seconds == 5
    assert settings.poll_interval_seconds == 0.5
    assert settings.data_dir == "data"
    assert settings.allowed_suffixes == (".csv", ".dat", ".txt")
    assert settings.min_size_bytes == 3


def test_load_settings_from_missing_toml_file_uses_defaults(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml")
    assert settings == Settings()  # all defaults


def test_load_settings_with_partial_tables_uses_defaults(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "test-service"

[service]
run_seconds = 10
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == "test-service"
    assert settings.log_level == DEFAULT_LOG_LEVEL
    assert settings.env == DEFAULT_ENV
    assert settings.run_seconds == 10
    assert settings.poll_interval_seconds == DEFAULT_POLL_INTERVAL_SECONDS
    assert settings.data_dir == DEFAULT_DATA_DIR
    assert settings.allowed_suffixes == DEFAULT_ALLOWED_SUFFIXES
    assert settings.min_size_bytes == DEFAULT_MIN_SIZE_BYTES


def test_load_settings_without_app_table_uses_defaults(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[service]
run_seconds = 5
poll_interval_seconds = 0.5
data_dir = "data"
allowed_suffixes = [".csv", ".dat", ".txt"]
min_size_bytes = 3
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == DEFAULT_APP_NAME
    assert settings.log_level == DEFAULT_LOG_LEVEL
    assert settings.env == DEFAULT_ENV


def test_load_settings_without_service_table_uses_defaults(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "test-service"
log_level = "DEBUG"
env = "TEST"
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == "test-service"
    assert settings.log_level == "DEBUG"
    assert settings.env == "TEST"
    assert settings.run_seconds == DEFAULT_RUN_SECONDS
    assert settings.poll_interval_seconds == DEFAULT_POLL_INTERVAL_SECONDS
    assert settings.data_dir == DEFAULT_DATA_DIR
    assert settings.allowed_suffixes == DEFAULT_ALLOWED_SUFFIXES
    assert settings.min_size_bytes == DEFAULT_MIN_SIZE_BYTES


def test_load_settings_with_environment_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "test-service"
log_level = "INFO"
env = "dev"

[service]
run_seconds = 1
poll_interval_seconds = 0.5
data_dir = "data"
allowed_suffixes = [".csv", ".dat", ".txt"]
min_size_bytes = 3
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(f"{ENV_PREFIX}_NAME", "env-service")
    monkeypatch.setenv(f"{ENV_PREFIX}_LOG_LEVEL", "WARNING")
    monkeypatch.setenv(f"{ENV_PREFIX}_ENV", "PROD")
    monkeypatch.setenv(f"{ENV_PREFIX}_RUN_SECONDS", "0")
    monkeypatch.setenv(f"{ENV_PREFIX}_POLL_INTERVAL_SECONDS", "1.0")
    monkeypatch.setenv(f"{ENV_PREFIX}_DATA_DIR", "env-data")
    monkeypatch.setenv(f"{ENV_PREFIX}_ALLOWED_SUFFIXES", ".csv, .txt")
    monkeypatch.setenv(f"{ENV_PREFIX}_MIN_SIZE_BYTES", "2")

    settings = load_settings(path)

    assert settings.app_name == "env-service"
    assert settings.log_level == "WARNING"
    assert settings.env == "PROD"
    assert settings.run_seconds == 0
    assert settings.poll_interval_seconds == 1.0
    assert settings.data_dir == "env-data"
    assert settings.allowed_suffixes == (".csv", ".txt")
    assert settings.min_size_bytes == 2


def test_settings_raises_for_invalid_log_level() -> None:
    with pytest.raises(ValueError, match="log_level"):
        Settings(log_level="INVALID_LOG_LEVEL")


def test_settings_raises_for_invalid_env() -> None:
    with pytest.raises(ValueError, match="env"):
        Settings(env="INVALID_ENV")


def test_settings_raises_for_negative_run_seconds() -> None:
    with pytest.raises(ValueError, match="run_seconds"):
        Settings(run_seconds=-1)


def test_settings_raises_for_negative_poll_interval_seconds() -> None:
    with pytest.raises(ValueError, match="poll_interval_seconds"):
        Settings(poll_interval_seconds=-0.1)


def test_settings_raises_for_zero_min_size_bytes() -> None:
    with pytest.raises(ValueError, match="min_size_bytes"):
        Settings(min_size_bytes=0)


def test_normalize_suffixes_adds_leading_dot() -> None:
    """Suffixes without a leading dot get one added."""
    result = _normalize_suffixes(["csv", "txt"])
    assert result == (".csv", ".txt")


def test_normalize_suffixes_skips_empty_strings() -> None:
    """Empty strings after stripping are ignored."""
    result = _normalize_suffixes([".csv", "", "  ", ".txt"])
    assert result == (".csv", ".txt")


def test_normalize_suffixes_returns_default_when_empty() -> None:
    """An empty input falls back to the default suffixes."""
    result = _normalize_suffixes([])
    assert result == DEFAULT_ALLOWED_SUFFIXES


def test_normalize_suffixes_lowercases_suffixes() -> None:
    result = _normalize_suffixes([".CSV", ".TXT"])
    assert result == (".csv", ".txt")
