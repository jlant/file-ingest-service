from pathlib import Path

import pytest

from file_ingest_service.paths import build_service_paths

# --- build_service_paths ---


def test_build_service_paths_returns_correct_structure(tmp_path: Path) -> None:
    """Paths are constructed relative to base_dir."""
    paths = build_service_paths(tmp_path)

    assert paths.inbox == tmp_path.resolve() / "inbox"
    assert paths.processed == tmp_path.resolve() / "processed"
    assert paths.error == tmp_path.resolve() / "error"


def test_build_service_paths_resolves_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative base_dir is resolved to an absolute path."""
    monkeypatch.chdir(tmp_path)
    paths = build_service_paths(Path())

    assert paths.inbox.is_absolute()


def test_build_service_paths_accepts_string(tmp_path: Path) -> None:
    """A string base_dir is accepted and normalized to a Path."""
    paths = build_service_paths(str(tmp_path))

    assert paths.inbox == tmp_path.resolve() / "inbox"


def test_build_service_paths_raises_when_base_dir_is_a_file(tmp_path: Path) -> None:
    """If base_dir points to an existing file, raises ValueError."""
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("oops")

    with pytest.raises(ValueError, match="not a directory"):
        build_service_paths(file_path)


def test_build_service_paths_accepts_nonexistent_base_dir(tmp_path: Path) -> None:
    """base_dir does not need to exist yet - directories are created later."""
    new_dir = tmp_path / "brand" / "new" / "dir"
    paths = build_service_paths(new_dir)

    assert paths.inbox == new_dir.resolve() / "inbox"


# --- ServicePaths.ensure_directories ---


def test_ensure_directories_creates_all_directories(tmp_path: Path) -> None:
    """ensure_directories creates inbox, processed, and error dirs."""
    paths = build_service_paths(tmp_path / "data")
    paths.ensure_directories()

    assert paths.inbox.is_dir()
    assert paths.processed.is_dir()
    assert paths.error.is_dir()


def test_ensure_directories_is_idempotent(tmp_path: Path) -> None:
    """Calling ensure_directories twice does not raise."""
    paths = build_service_paths(tmp_path / "data")
    paths.ensure_directories()
    paths.ensure_directories()  # should not raise


def test_ensure_directories_creates_nested_parents(tmp_path: Path) -> None:
    """ensure_directories creates all intermediate parent directories."""
    paths = build_service_paths(tmp_path / "deeply" / "nested" / "data")
    paths.ensure_directories()

    assert paths.inbox.is_dir()
