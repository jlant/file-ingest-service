"""Shared test fakes and fixtures.

The fakes are the payoff of the boundary design. Because the ingest logic and
the service depend on the FileSource / FileRouter Protocols rather than on the
filesystem directly, these in-memory fakes let the real logic run with no disk
I/O and no mocking - tests assert on what the fakes RECORDED happening, not on
which internal function was called.

The two autouse fixtures isolate global process state (the environment and the
root logger) so tests never depend on ambient values. Keep them: they are the
mechanism that stops "passes locally, fails on the server."
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from file_ingest_service.settings import ENV_PREFIX


@dataclass
class FakeFileSource:
    """In-memory stand-in for the inbound boundary (FileSource).

    Holds the list of pending files it will report. Satisfies FileSource.
    """

    pending: list[Path] = field(default_factory=list[Path])

    def list_pending(self) -> list[Path]:
        return list(self.pending)


@dataclass
class FakeFileRouter:
    """In-memory stand-in for the outbound boundary (FileRouter).

    Records which files were routed where. fail_processed / fail_error inject
    routing failures by filename so the fallback paths can be exercised without
    a real filesystem.
    """

    processed: list[Path] = field(default_factory=list[Path])
    errored: list[Path] = field(default_factory=list[Path])
    fail_processed: set[str] = field(default_factory=set[str])
    fail_error: set[str] = field(default_factory=set[str])

    def route_processed(self, path: Path) -> Path:
        if path.name in self.fail_processed:
            msg = f"simulated processed-route failure for {path.name}"
            raise OSError(msg)
        self.processed.append(path)
        return Path("/processed") / path.name

    def route_error(self, path: Path) -> Path:
        if path.name in self.fail_error:
            msg = f"simulated error-route failure for {path.name}"
            raise OSError(msg)
        self.errored.append(path)
        return Path("/error") / path.name


@pytest.fixture
def source() -> FakeFileSource:
    return FakeFileSource()


@pytest.fixture
def router() -> FakeFileRouter:
    return FakeFileRouter()


@pytest.fixture(autouse=True)
def clean_app_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every APP_* variable from the environment before each test.

    Settings resolution reads APP_* environment variables, so any set in the
    ambient process environment would leak into every test - and on a deployment
    server, machine-scoped values guarantee they are set. This makes the
    environment deterministic. A test that WANTS one still sets it with
    monkeypatch.setenv, which runs after this fixture and therefore still works.
    """
    for name in [key for key in os.environ if key.startswith(f"{ENV_PREFIX}_")]:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def isolate_root_logger() -> Generator[None]:
    """Snapshot and restore the root logger around every test.

    configure_logging() attaches handlers to the root logger, which is global
    process state: once a test attaches a file handler pointing at a real path,
    every later test's log calls write to that file - which is how test output
    ends up in a production log. Handlers added during a test are closed so no
    file handle is left open (on Windows an open handle blocks tmp cleanup).
    """
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    try:
        yield
    finally:
        for handler in root.handlers[:]:
            if handler not in saved_handlers:
                handler.close()
                root.removeHandler(handler)
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)
