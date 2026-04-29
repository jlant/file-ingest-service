from pathlib import Path

from file_ingest_service.config import resolve_settings
from file_ingest_service.settings import DEFAULT_APP_NAME


def test_resolve_settings_with_no_path_uses_default() -> None:
    # No config file exists at the default path in the test environment,
    # so we expect defaults to be returned without raising.
    settings = resolve_settings(Path("nonexistent_config_for_testing.toml"))
    assert settings.app_name == DEFAULT_APP_NAME
    assert settings.log_level == "INFO"
    assert settings.env == "DEV"
    assert settings.run_seconds == 5
    assert settings.poll_interval_seconds == 1.0
    assert settings.data_dir == "data"
    assert settings.allowed_suffixes == (".csv", ".dat", ".txt")
    assert settings.min_size_bytes == 1


def test_resolve_settings_with_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "test-service"
log_level = "DEBUG"
env = "DEV"

[service]
run_seconds = 0
poll_interval_seconds = 0.0
data_dir = "data"
allowed_suffixes = [".csv", ".dat", ".txt"]
min_size_bytes = 1
""".strip(),
        encoding="utf-8",
    )

    settings = resolve_settings(path)

    assert settings.app_name == "test-service"
    assert settings.log_level == "DEBUG"
    assert settings.env == "DEV"
    assert settings.run_seconds == 0
    assert settings.poll_interval_seconds == 0.0
    assert settings.data_dir == "data"
    assert settings.allowed_suffixes == (".csv", ".dat", ".txt")
    assert settings.min_size_bytes == 1
