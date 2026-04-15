from pathlib import Path

from file_ingest_service.service import Service
from file_ingest_service.settings import Settings


def test_service_start_run_stop(tmp_path: Path) -> None:
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
