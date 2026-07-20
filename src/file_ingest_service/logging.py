from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .settings import Settings

logger = logging.getLogger(__name__)

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 5


def configure_logging(settings: Settings) -> None:
    """Configure application logging once at startup.

    Attaches a console handler and a rotating file handler to the root logger.
    Unlike logging.basicConfig - which silently does nothing if the root logger
    already has handlers - this clears and rebuilds them, so the call is always
    effective and repeated calls do not stack duplicates.

    Note this mutates the ROOT logger, which is global process state. Tests must
    isolate it (see the isolate_root_logger fixture in tests/conftest.py) so a
    handler attached in one test does not leak into the next - and so test output
    never lands in the real application log.
    """
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = logging.Formatter(_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logger.info(
        "logging configured log_level=%s log_file=%s", settings.log_level, settings.log_file
    )
