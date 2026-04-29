from pathlib import Path

import pytest

from file_ingest_service.service import Service
from file_ingest_service.settings import Settings


def test_service_start_sets_started_flag(tmp_path: Path) -> None:
    settings = Settings(data_dir=str(tmp_path / "data"))
    service = Service(settings)
    assert service.started is False
    service.start()
    assert service.started is True


def test_service_stop_clears_started_flag(tmp_path: Path) -> None:
    settings = Settings(data_dir=str(tmp_path / "data"))
    service = Service(settings)
    service.start()
    service.stop()
    assert service.started is False


def test_service_stop_when_not_started_is_safe(tmp_path: Path) -> None:
    """stop() on an unstarted service should not raise."""
    settings = Settings(data_dir=str(tmp_path / "data"))
    service = Service(settings)
    service.stop()  # should not raise


def test_service_run_with_empty_inbox(tmp_path: Path) -> None:
    """run() with no files in inbox completes without error."""
    settings = Settings(
        data_dir=str(tmp_path / "data"),
        run_seconds=0,
        poll_interval_seconds=0.0,
    )
    service = Service(settings)
    service.start()
    service.run()  # inbox is empty - should complete cleanly


def test_service_run_ignores_disallowed_suffixes(tmp_path: Path) -> None:
    inbox = tmp_path / "data" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "sample.csv").write_text("hello", encoding="utf-8")

    settings = Settings(
        data_dir=str(tmp_path / "data"),
        run_seconds=0,
        poll_interval_seconds=0.0,
        allowed_suffixes=(".txt",),
    )
    service = Service(settings)
    service.start()
    service.run()

    # CSV file should remain in inbox untouched
    assert (inbox / "sample.csv").exists()


def test_service_full_lifecycle_processes_file(tmp_path: Path) -> None:
    """Integration test: file placed in inbox is processed end-to-end."""
    inbox = tmp_path / "data" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "sample.txt").write_text("hello", encoding="utf-8")

    settings = Settings(
        run_seconds=0,
        poll_interval_seconds=0.0,
        data_dir=str(tmp_path / "data"),
    )
    service = Service(settings)

    assert service.started is False

    service.start()
    assert service.started is True

    service.run()

    processed = tmp_path / "data" / "processed" / "sample.txt"
    assert processed.exists()

    service.stop()
    assert service.started is False


def test_service_run_raises_if_not_started() -> None:
    """Service.run() should raise RuntimeError if start() was never called."""
    settings = Settings(run_seconds=0)
    service = Service(settings)
    with pytest.raises(RuntimeError, match="must be started"):
        service.run()
