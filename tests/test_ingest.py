"""Tests for the per-file ingest rule (ingest.handle_file) and its validation.

These tests encode the routing invariant the design exists to protect:

    every handled file LEAVES the inbox - to processed on success, to error on
    failure - so a permanently bad file is quarantined once rather than retried
    forever.

handle_file depends on the FileRouter Protocol, so the routing outcomes are
asserted against an in-memory fake (what it recorded) rather than by patching
shutil. validate_file is pure logic and is tested directly against tmp_path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from file_ingest_service.ingest import handle_file, validate_file
from tests.conftest import FakeFileRouter


def _file(tmp_path: Path, name: str, content: str = "hello") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


class TestValidateFile:
    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="file does not exist"):
            validate_file(tmp_path / "ghost.txt", min_size_bytes=1)

    def test_raises_when_file_too_small(self, tmp_path: Path) -> None:
        empty = _file(tmp_path, "tiny.txt", content="")
        with pytest.raises(ValueError, match="file is too small"):
            validate_file(empty, min_size_bytes=1)

    def test_passes_for_valid_file(self, tmp_path: Path) -> None:
        valid = _file(tmp_path, "ok.txt", content="enough content")
        validate_file(valid, min_size_bytes=1)  # must not raise


class TestSuccessfulHandling:
    def test_valid_file_is_routed_to_processed(self, tmp_path: Path) -> None:
        path = _file(tmp_path, "sample.txt")
        router = FakeFileRouter()

        result = handle_file(path, router=router, min_size_bytes=1)

        assert result.success is True
        assert result.reason == "processed"
        assert router.processed == [path]
        assert router.errored == []

    def test_result_carries_source_and_destination(self, tmp_path: Path) -> None:
        path = _file(tmp_path, "sample.txt")
        router = FakeFileRouter()

        result = handle_file(path, router=router, min_size_bytes=1)

        assert result.source == path
        assert result.destination.name == "sample.txt"


class TestQuarantineInvariant:
    """A file that cannot be processed is routed to error, never left behind."""

    def test_invalid_file_is_routed_to_error(self, tmp_path: Path) -> None:
        path = _file(tmp_path, "empty.txt", content="")
        router = FakeFileRouter()

        result = handle_file(path, router=router, min_size_bytes=1)

        assert result.success is False
        assert "too small" in result.reason
        assert router.errored == [path]
        assert router.processed == []

    def test_missing_file_is_routed_to_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "ghost.txt"
        router = FakeFileRouter()

        result = handle_file(missing, router=router, min_size_bytes=1)

        assert result.success is False
        assert router.errored == [missing]

    def test_processed_route_failure_falls_back_to_error(self, tmp_path: Path) -> None:
        """The file validates and processes, but the processed route fails.
        It must still leave the inbox - via the error route."""
        path = _file(tmp_path, "sample.txt")
        router = FakeFileRouter(fail_processed={"sample.txt"})

        result = handle_file(path, router=router, min_size_bytes=1)

        assert result.success is False
        assert "processed-route failure" in result.reason
        assert router.errored == [path]


class TestTotalFailure:
    def test_both_routes_failing_still_returns_a_result(self, tmp_path: Path) -> None:
        """If even the error route fails, handle_file reports it rather than
        raising - one unroutable file must not halt the batch."""
        path = _file(tmp_path, "sample.txt")
        router = FakeFileRouter(fail_processed={"sample.txt"}, fail_error={"sample.txt"})

        result = handle_file(path, router=router, min_size_bytes=1)

        assert result.success is False
        assert result.source == path
        assert result.destination == path  # falls back to the original path
        assert "error-route failure" in result.reason

    def test_failure_returns_result_does_not_raise(self, tmp_path: Path) -> None:
        path = _file(tmp_path, "empty.txt", content="")
        router = FakeFileRouter(fail_error={"empty.txt"})
        result = handle_file(path, router=router, min_size_bytes=1)  # must not raise
        assert result.success is False
