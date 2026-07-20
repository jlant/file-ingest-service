"""Tests for the service orchestration layer.

The service obtains its two boundaries through the _make_source() /
_make_router() factory seam, so a test subclass supplies fakes by overriding
those methods - no mocking, no patching. Tests are grouped by the condition
they exercise and assert on state the fakes recorded.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from file_ingest_service.protocols import FileRouter, FileSource
from file_ingest_service.service import Service
from file_ingest_service.settings import Settings
from tests.conftest import FakeFileRouter, FakeFileSource


class _TestService(Service):
    """Service subclass returning fakes from the factory seams."""

    def __init__(self, settings: Settings, source: FakeFileSource, router: FakeFileRouter) -> None:
        super().__init__(settings)
        self._fake_source = source
        self._fake_router = router

    def _make_source(self) -> FileSource:
        return self._fake_source

    def _make_router(self) -> FileRouter:
        return self._fake_router


def _service(tmp_path: Path, source: FakeFileSource, router: FakeFileRouter) -> _TestService:
    settings = Settings(data_dir=str(tmp_path / "data"))
    svc = _TestService(settings, source, router)
    svc.start()
    return svc


def _real_file(tmp_path: Path, name: str, content: str = "hello") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


class TestCleanRun:
    def test_every_pending_file_is_processed(self, tmp_path: Path) -> None:
        a = _real_file(tmp_path, "a.txt")
        b = _real_file(tmp_path, "b.txt")
        source = FakeFileSource(pending=[a, b])
        router = FakeFileRouter()
        svc = _service(tmp_path, source, router)

        svc.run()

        assert router.processed == [a, b]
        assert router.errored == []


class TestEmptyInbox:
    def test_empty_inbox_is_a_clean_noop(self, tmp_path: Path) -> None:
        source = FakeFileSource(pending=[])
        router = FakeFileRouter()
        svc = _service(tmp_path, source, router)

        svc.run()

        assert router.processed == []
        assert router.errored == []


class TestPerFileFailure:
    def test_one_bad_file_does_not_halt_the_batch(self, tmp_path: Path) -> None:
        good = _real_file(tmp_path, "good.txt")
        bad = _real_file(tmp_path, "bad.txt", content="")  # too small
        other = _real_file(tmp_path, "other.txt")
        source = FakeFileSource(pending=[good, bad, other])
        router = FakeFileRouter()
        svc = _service(tmp_path, source, router)

        svc.run()

        assert router.processed == [good, other]
        assert router.errored == [bad]

    def test_run_does_not_raise_on_failure(self, tmp_path: Path) -> None:
        bad = _real_file(tmp_path, "bad.txt", content="")
        svc = _service(tmp_path, FakeFileSource(pending=[bad]), FakeFileRouter())
        svc.run()  # must not raise


class TestLifecycle:
    def test_run_before_start_raises(self, tmp_path: Path) -> None:
        settings = Settings(data_dir=str(tmp_path / "data"))
        svc = _TestService(settings, FakeFileSource(), FakeFileRouter())
        with pytest.raises(RuntimeError, match="must be started"):
            svc.run()

    def test_start_creates_the_service_directories(self, tmp_path: Path) -> None:
        svc = _service(tmp_path, FakeFileSource(), FakeFileRouter())
        assert svc.paths.inbox.is_dir()
        assert svc.paths.processed.is_dir()
        assert svc.paths.error.is_dir()

    def test_stop_clears_started_flag(self, tmp_path: Path) -> None:
        svc = _service(tmp_path, FakeFileSource(), FakeFileRouter())
        assert svc.started is True
        svc.stop()
        assert svc.started is False

    def test_stop_when_not_started_is_safe(self, tmp_path: Path) -> None:
        settings = Settings(data_dir=str(tmp_path / "data"))
        svc = _TestService(settings, FakeFileSource(), FakeFileRouter())
        svc.stop()  # must not raise
