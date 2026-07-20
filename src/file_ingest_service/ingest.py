from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .protocols import FileRouter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileProcessResult:
    """The outcome of handling one file.

    Returned for every file - success or failure - so the caller can summarize a
    batch without inspecting logs. ``destination`` is where the file ended up; on
    a total failure (both routes failed) it falls back to the original path.
    """

    source: Path
    destination: Path
    success: bool
    reason: str


def validate_file(path: Path, min_size_bytes: int) -> None:
    """Raise if the file is missing or below the minimum size.

    Pure domain logic: no boundary, no I/O beyond a stat, so it is tested
    directly rather than through a fake.
    """
    if not path.exists():
        msg = f"file does not exist: {path}"
        raise FileNotFoundError(msg)

    if path.stat().st_size < min_size_bytes:
        msg = f"file is too small: {path.name}"
        raise ValueError(msg)


def process_file(path: Path) -> None:
    """Placeholder for the real per-file work.

    For now it just reads the file to prove it is accessible. Replace this with
    the actual processing (parse, transform, load) for your use case.
    """
    _ = path.read_bytes()


def handle_file(path: Path, router: FileRouter, min_size_bytes: int) -> FileProcessResult:
    """Validate, process, and route a single file.

    The routing rule: a file that validates and processes goes to the processed
    area; anything else is quarantined in the error area. Either way the file
    LEAVES the inbox, so a permanently bad file is set aside once rather than
    retried forever.

    Failures are returned, never raised, so one bad file cannot halt the batch.
    If even the error route fails, the result still comes back - reporting the
    problem is more useful than crashing the run.
    """
    logger.info("handling file: %s", path.name)

    try:
        validate_file(path, min_size_bytes=min_size_bytes)
        process_file(path)
    except Exception as exc:
        logger.exception("failed processing file: %s reason: %s", path.name, exc)
        try:
            destination = router.route_error(path)
        except Exception as route_exc:
            logger.exception("failed routing file to error area: %s", path.name)
            return FileProcessResult(
                source=path, destination=path, success=False, reason=str(route_exc)
            )
        return FileProcessResult(
            source=path, destination=destination, success=False, reason=str(exc)
        )

    try:
        destination = router.route_processed(path)
    except Exception as exc:
        logger.exception("failed routing file to processed area: %s", path.name)
        try:
            destination = router.route_error(path)
        except Exception as route_exc:
            logger.exception("failed routing file to error area: %s", path.name)
            return FileProcessResult(
                source=path, destination=path, success=False, reason=str(route_exc)
            )
        return FileProcessResult(
            source=path, destination=destination, success=False, reason=str(exc)
        )

    logger.info("processed file successfully: %s", destination.name)
    return FileProcessResult(source=path, destination=destination, success=True, reason="processed")
