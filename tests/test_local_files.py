"""Tests for the concrete filesystem boundaries (local_files).

The filesystem is cheap and safe to use for real, so these tests do not fake it:
LocalFileSource lists real files and LocalFileRouter moves them, and we assert on
what actually happened on disk. Faking here would test nothing - the whole point
of these classes is their filesystem behavior.
"""

from __future__ import annotations

from pathlib import Path

from file_ingest_service.local_files import LocalFileRouter, LocalFileSource
from file_ingest_service.paths import build_service_paths


def _setup(tmp_path: Path) -> tuple[LocalFileSource, LocalFileRouter, Path]:
    paths = build_service_paths(tmp_path / "data")
    paths.ensure_directories()
    source = LocalFileSource(paths.inbox, allowed_suffixes=(".txt", ".csv"))
    router = LocalFileRouter(paths)
    return source, router, paths.inbox


class TestLocalFileSource:
    def test_lists_files_with_allowed_suffixes(self, tmp_path: Path) -> None:
        source, _, inbox = _setup(tmp_path)
        (inbox / "a.txt").write_text("x", encoding="utf-8")
        (inbox / "b.csv").write_text("x", encoding="utf-8")
        (inbox / "c.md").write_text("x", encoding="utf-8")

        names = [p.name for p in source.list_pending()]

        assert names == ["a.txt", "b.csv"] or names == ["b.csv", "a.txt"]
        assert "c.md" not in names

    def test_results_are_sorted(self, tmp_path: Path) -> None:
        source, _, inbox = _setup(tmp_path)
        for name in ("c.txt", "a.txt", "b.txt"):
            (inbox / name).write_text("x", encoding="utf-8")

        assert [p.name for p in source.list_pending()] == ["a.txt", "b.txt", "c.txt"]

    def test_suffix_match_is_case_insensitive(self, tmp_path: Path) -> None:
        source, _, inbox = _setup(tmp_path)
        (inbox / "UPPER.TXT").write_text("x", encoding="utf-8")

        assert [p.name for p in source.list_pending()] == ["UPPER.TXT"]

    def test_directories_are_skipped(self, tmp_path: Path) -> None:
        source, _, inbox = _setup(tmp_path)
        (inbox / "file.txt").write_text("x", encoding="utf-8")
        (inbox / "subdir.txt").mkdir()

        results = source.list_pending()

        assert all(p.is_file() for p in results)
        assert [p.name for p in results] == ["file.txt"]

    def test_empty_inbox_returns_empty_list(self, tmp_path: Path) -> None:
        source, _, _ = _setup(tmp_path)
        assert source.list_pending() == []

    def test_no_suffix_filter_returns_everything(self, tmp_path: Path) -> None:
        paths = build_service_paths(tmp_path / "data")
        paths.ensure_directories()
        source = LocalFileSource(paths.inbox, allowed_suffixes=())
        (paths.inbox / "a.txt").write_text("x", encoding="utf-8")
        (paths.inbox / "b.md").write_text("x", encoding="utf-8")

        assert len(source.list_pending()) == 2


class TestLocalFileRouter:
    def test_route_processed_moves_the_file(self, tmp_path: Path) -> None:
        _, router, inbox = _setup(tmp_path)
        path = inbox / "sample.txt"
        path.write_text("hello", encoding="utf-8")

        destination = router.route_processed(path)

        assert destination.exists()
        assert destination.read_text(encoding="utf-8") == "hello"
        assert not path.exists()  # moved, not copied

    def test_route_error_moves_the_file(self, tmp_path: Path) -> None:
        _, router, inbox = _setup(tmp_path)
        path = inbox / "bad.txt"
        path.write_text("oops", encoding="utf-8")

        destination = router.route_error(path)

        assert destination.exists()
        assert not path.exists()

    def test_routing_leaves_the_inbox_empty(self, tmp_path: Path) -> None:
        """The invariant that matters: a routed file is no longer pending."""
        source, router, inbox = _setup(tmp_path)
        path = inbox / "sample.txt"
        path.write_text("hello", encoding="utf-8")

        router.route_processed(path)

        assert source.list_pending() == []
