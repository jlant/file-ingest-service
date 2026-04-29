from pathlib import Path

from typer.testing import CliRunner

from file_ingest_service.cli import app

runner = CliRunner()


def write_config(path: Path, data_dir: Path) -> None:
    path.write_text(
        f"""
[app]
name = "test-service"
log_level = "INFO"
env = "TEST"

[service]
run_seconds = 0
poll_interval_seconds = 0.0
data_dir = "{data_dir}"
allowed_suffixes = [".txt", ".csv"]
min_size_bytes = 1
""".strip(),
        encoding="utf-8",
    )


def test_version_flag_works() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "fis" in result.stdout


def test_read_config_prints_resolved_settings(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    result = runner.invoke(app, ["read-config", "--config", str(config)])

    assert result.exit_code == 0
    assert "app_name='test-service'" in result.stdout
    assert "env='TEST'" in result.stdout
    assert f"data_dir='{data_dir}'" in result.stdout


def test_seed_creates_file_in_inbox(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    result = runner.invoke(
        app,
        [
            "seed",
            "--filename",
            "sample.txt",
            "--content",
            "hello world",
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0
    target = data_dir / "inbox" / "sample.txt"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello world"


def test_run_processes_seeded_file(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    inbox = data_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "sample.txt").write_text("hello", encoding="utf-8")

    result = runner.invoke(app, ["run", "--config", str(config)])

    assert result.exit_code == 0
    assert not (data_dir / "inbox" / "sample.txt").exists()
    assert (data_dir / "processed" / "sample.txt").exists()


def test_run_moves_invalid_file_to_error(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    inbox = data_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "empty.txt").write_text("", encoding="utf-8")

    result = runner.invoke(app, ["run", "--config", str(config)])

    assert result.exit_code == 0
    assert not (data_dir / "inbox" / "empty.txt").exists()
    assert (data_dir / "error" / "empty.txt").exists()
