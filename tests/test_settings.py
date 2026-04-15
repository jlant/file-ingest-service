from pathlib import Path

from file_ingest_service.settings import load_settings


def test_load_settings_from_toml_file(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "demo-app"
log_level = "DEBUG"
env = "test"

[service]
run_seconds = 5
poll_interval_seconds = 0.5
data_dir = "demo-data"
allowed_suffixes = [".txt", ".dat"]
min_size_bytes = 3
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == "demo-app"
    assert settings.log_level == "DEBUG"
    assert settings.env == "test"
    assert settings.run_seconds == 5
    assert settings.poll_interval_seconds == 0.5
    assert settings.data_dir == "demo-data"
    assert settings.allowed_suffixes == (".txt", ".dat")
    assert settings.min_size_bytes == 3


def test_load_settings_missing_toml_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml")
    assert settings.app_name == "file-ingest-service"
    assert settings.log_level == "INFO"
    assert settings.env == "dev"
    assert settings.run_seconds == 5
    assert settings.poll_interval_seconds == 1.0
    assert settings.data_dir == "data"
    assert settings.allowed_suffixes == (".txt", ".csv")
    assert settings.min_size_bytes == 1


def test_load_settings_without_app_table(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[other]
value = 1
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == "file-ingest-service"
    assert settings.log_level == "INFO"
    assert settings.env == "dev"
    assert settings.run_seconds == 5
    assert settings.poll_interval_seconds == 1.0
    assert settings.data_dir == "data"
    assert settings.allowed_suffixes == (".txt", ".csv")
    assert settings.min_size_bytes == 1


def test_environment_overrides(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        """
[app]
name = "demo-app"
log_level = "INFO"
env = "dev"

[service]
run_seconds = 1
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("FIS_APP_NAME", "env-app")
    monkeypatch.setenv("FIS_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("FIS_ENV", "prod")
    monkeypatch.setenv("FIS_RUN_SECONDS", "0")
    monkeypatch.setenv("FIS_POLL_INTERVAL_SECONDS", "0.5")
    monkeypatch.setenv("FIS_DATA_DIR", "env-data")
    monkeypatch.setenv("FIS_MIN_SIZE_BYTES", "5")

    settings = load_settings(path)

    assert settings.app_name == "env-app"
    assert settings.log_level == "WARNING"
    assert settings.env == "prod"
    assert settings.run_seconds == 0
    assert settings.poll_interval_seconds == 0.5
    assert settings.data_dir == "env-data"
    assert settings.allowed_suffixes == (".txt", ".csv")
    assert settings.min_size_bytes == 5
