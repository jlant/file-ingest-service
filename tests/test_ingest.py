from pathlib import Path
from unittest.mock import patch

import pytest

from file_ingest_service.ingest import (
    get_input_files,
    handle_file,
    validate_file,
)
from file_ingest_service.paths import build_service_paths


# --- get_input_files ---
def test_get_input_files_no_suffix_filter(tmp_path: Path) -> None:
    """When allowed_suffixes is empty, all files are returned."""
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.csv").write_text("world")

    result = get_input_files(tmp_path, allowed_suffixes=())

    assert len(result) == 2
    assert {p.name for p in result} == {"a.txt", "b.csv"}


def test_get_input_files_with_suffix_filter(tmp_path: Path) -> None:
    """When allowed_suffixes is provided, only matching files are returned."""
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.csv").write_text("world")
    (tmp_path / "c.txt").write_text("again")

    result = get_input_files(tmp_path, allowed_suffixes=(".txt",))

    assert len(result) == 2
    assert all(p.suffix == ".txt" for p in result)


def test_get_input_files_returns_sorted(tmp_path: Path) -> None:
    """Results are returned in sorted order."""
    for name in ("c.txt", "a.txt", "b.txt"):
        (tmp_path / name).write_text("x")

    result = get_input_files(tmp_path, allowed_suffixes=(".txt",))

    assert [p.name for p in result] == ["a.txt", "b.txt", "c.txt"]


def test_get_input_files_skips_directories(tmp_path: Path) -> None:
    """Subdirectories are not included in results."""
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()

    result = get_input_files(tmp_path, allowed_suffixes=())

    assert all(p.is_file() for p in result)
    assert len(result) == 1


# --- validate_file ---
def test_validate_file_raises_when_file_missing(tmp_path: Path) -> None:
    """validate_file raises FileNotFoundError for a non-existent path."""
    missing = tmp_path / "ghost.txt"

    with pytest.raises(FileNotFoundError, match="file does not exist"):
        validate_file(missing, min_size_bytes=1)


def test_validate_file_raises_when_file_too_small(tmp_path: Path) -> None:
    """validate_file raises ValueError when file is below the minimum size."""
    small = tmp_path / "tiny.txt"
    small.write_text("")

    with pytest.raises(ValueError, match="file is too small"):
        validate_file(small, min_size_bytes=1)


def test_validate_file_passes_for_valid_file(tmp_path: Path) -> None:
    """validate_file does not raise for a file that exists and meets the size
    threshold."""
    valid = tmp_path / "ok.txt"
    valid.write_text("enough_content")

    validate_file(valid, min_size_bytes=1)  # should not raise


# --- handle_file ---
def test_handle_file_success(tmp_path: Path) -> None:
    """A valid file processed and moved to the processed directory."""
    paths = build_service_paths(tmp_path)
    paths.ensure_directories()

    source = paths.inbox / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    result = handle_file(path=source, paths=paths, min_size_bytes=1)

    assert result.success is True
    assert result.destination == paths.processed / "sample.txt"
    assert result.destination.exists()
    assert not source.exists()


def test_handle_file_failure_moves_to_error(tmp_path: Path) -> None:
    """A file that fails validation is moved to the error directory."""
    paths = build_service_paths(tmp_path)
    paths.ensure_directories()

    source = paths.inbox / "empty.txt"
    source.write_text("", encoding="utf-8")

    result = handle_file(path=source, paths=paths, min_size_bytes=1)

    assert result.success is False
    assert result.destination == paths.error / "empty.txt"
    assert result.destination.exists()
    assert not source.exists()


def test_handle_file_move_to_processed_fails_falls_back_to_error(tmp_path: Path) -> None:
    """
    If moving to the processed directory raises, the file is moved to the error
    directory instead and the result reflects the failure.
    """
    paths = build_service_paths(tmp_path)
    paths.ensure_directories()

    source = paths.inbox / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    original_move = __import__("shutil").move

    def move_side_effect(src: Path, dst: Path):
        # Fail only when the destination is the processed directory.
        if str(paths.processed) in str(dst):
            raise OSError("disk full")
        return original_move(src, dst)

    with patch("file_ingest_service.ingest.shutil.move", side_effect=move_side_effect):
        result = handle_file(path=source, paths=paths, min_size_bytes=1)

    assert result.success is False
    assert result.destination == paths.error / "sample.txt"
    assert result.destination.exists()


def test_handle_file_both_moves_fail_returns_result(tmp_path: Path) -> None:
    """
    If both the processed-dir and error-dir moves fail, handle_file still returns a
    FileProcessResult rather than raising. The destination falls back to the original
    source path.
    """
    paths = build_service_paths(tmp_path)
    paths.ensure_directories()

    source = paths.inbox / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    with patch("file_ingest_service.ingest.shutil.move", side_effect=OSError("disk_full")):
        result = handle_file(path=source, paths=paths, min_size_bytes=1)

    assert result.success is False
    assert result.source == source
