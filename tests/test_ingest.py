from pathlib import Path

from file_ingest_service.ingest import handle_file
from file_ingest_service.paths import build_service_paths, ensure_directories


def test_handle_file_success(tmp_path: Path) -> None:
    paths = build_service_paths(tmp_path)
    ensure_directories(paths)

    source = paths.inbox / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    result = handle_file(
        path=source,
        paths=paths,
        min_size_bytes=1,
    )

    assert result.success is True
    assert result.destination == paths.processed / "sample.txt"
    assert result.destination.exists()
    assert not source.exists()


def test_handle_file_failure_moves_to_error(tmp_path: Path) -> None:
    paths = build_service_paths(tmp_path)
    ensure_directories(paths)

    source = paths.inbox / "empty.txt"
    source.write_text("", encoding="utf-8")

    result = handle_file(
        path=source,
        paths=paths,
        min_size_bytes=1,
    )

    assert result.success is False
    assert result.destination == paths.error / "empty.txt"
    assert result.destination.exists()
    assert not source.exists()
