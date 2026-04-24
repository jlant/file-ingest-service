import logging

import pytest

from file_ingest_service.logging import configure_logging
from file_ingest_service.settings import Settings


def test_configure_logging_sets_level(monkeypatch: pytest.MonkeyPatch) -> None:
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    monkeypatch.setattr(root, "level", logging.WARNING)

    settings = Settings(log_level="DEBUG")
    configure_logging(settings)

    assert root.level == logging.DEBUG


def test_configure_logging_defaults_to_info_for_unknown_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    monkeypatch.setattr(root, "level", logging.WARNING)

    settings = Settings(log_level="NOTAREALLEVEL")
    configure_logging(settings)

    assert root.level == logging.INFO
