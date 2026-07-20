"""Tests for the CLI surface.

Typer's CliRunner invokes commands as a user would. These are end-to-end through
the real filesystem (cheap and safe), proving the CLI wiring, exit codes, and the
inbox -> processed | error routing.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from file_ingest_service.cli import app

runner = CliRunner()


def write_config(path: Path, data_dir: Path) -> None:
    """Write a minimal valid config for CLI tests.

    Path values are normalized to forward slashes: on Windows a raw path like
    C:\\Users\\... written into a TOML basic string would treat the backslashes
    as escapes, and `\\U` fails with "Invalid hex value". Forward slashes are
    accepted by TOML, Python, and Windows alike.

    log_file points into the test's own tmp dir so CLI runs never write into the
    real application log.
    """
    data = str(data_dir).replace("\\", "/")
    log_file = str(path.parent / "test.log").replace("\\", "/")
    path.write_text(
        f"""
[app]
name = "test-service"
log_level = "INFO"
env = "TEST"
log_file = "{log_file}"

[service]
data_dir = "{data}"
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


def test_seed_creates_file_in_inbox(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    result = runner.invoke(
        app,
        ["seed", "--filename", "sample.txt", "--content", "hello world", "--config", str(config)],
    )

    assert result.exit_code == 0
    target = data_dir / "inbox" / "sample.txt"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello world"


def test_run_processes_a_valid_file(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    inbox = data_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "sample.txt").write_text("hello", encoding="utf-8")

    result = runner.invoke(app, ["run", "--config", str(config)])

    assert result.exit_code == 0
    assert not (inbox / "sample.txt").exists()
    assert (data_dir / "processed" / "sample.txt").exists()


def test_run_quarantines_an_invalid_file(tmp_path: Path) -> None:
    config = tmp_path / "app.toml"
    data_dir = tmp_path / "data"
    write_config(config, data_dir)

    inbox = data_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "empty.txt").write_text("", encoding="utf-8")

    result = runner.invoke(app, ["run", "--config", str(config)])

    assert result.exit_code == 0
    assert not (inbox / "empty.txt").exists()
    assert (data_dir / "error" / "empty.txt").exists()
