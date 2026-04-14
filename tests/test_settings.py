from pathlib import Path

from python_service_template.settings import load_settings


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
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.app_name == "demo-app"
    assert settings.log_level == "DEBUG"
    assert settings.env == "test"
    assert settings.run_seconds == 5


def test_load_settings_missing_toml_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml")
    assert settings.app_name == "python-service-template"
    assert settings.log_level == "INFO"
    assert settings.env == "dev"
    assert settings.run_seconds == 1


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

    assert settings.app_name == "python-service-template"
    assert settings.log_level == "INFO"
    assert settings.env == "dev"
    assert settings.run_seconds == 1


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

    monkeypatch.setenv("PST_APP_NAME", "env-app")
    monkeypatch.setenv("PST_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("PST_ENV", "prod")
    monkeypatch.setenv("PST_RUN_SECONDS", "0")

    settings = load_settings(path)

    assert settings.app_name == "env-app"
    assert settings.log_level == "WARNING"
    assert settings.env == "prod"
    assert settings.run_seconds == 0
