"""Tests for logging configuration.

The isolate_root_logger autouse fixture restores root logger state after each
test, so no manual handler reset is needed here.
"""

from __future__ import annotations

import logging
from pathlib import Path

from file_ingest_service.logging import configure_logging
from file_ingest_service.settings import Settings


def test_sets_the_configured_level(tmp_path: Path) -> None:
    configure_logging(Settings(log_level="DEBUG", log_file=str(tmp_path / "app.log")))
    assert logging.getLogger().level == logging.DEBUG


def test_is_repeatable_without_stacking_handlers(tmp_path: Path) -> None:
    """Unlike basicConfig, repeated calls rebuild rather than accumulate."""
    log_file = str(tmp_path / "app.log")
    configure_logging(Settings(log_level="INFO", log_file=log_file))
    first = len(logging.getLogger().handlers)

    configure_logging(Settings(log_level="WARNING", log_file=log_file))

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == first  # not doubled


def test_creates_the_log_file_directory(tmp_path: Path) -> None:
    log_file = tmp_path / "nested" / "dir" / "app.log"
    configure_logging(Settings(log_file=str(log_file)))
    assert log_file.parent.is_dir()
