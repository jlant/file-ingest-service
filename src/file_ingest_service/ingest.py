from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from .paths import ServicePaths

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileProcessResult:
    source: Path
    destination: Path
    success: bool
    reason: str


def iter_input_files(inbox: Path, allowed_suffixes: tuple[str, ...]) -> list[Path]:
    files = [p for p in inbox.iterdir() if p.is_file()]
    if allowed_suffixes:
        files = [p for p in files if p.suffix.lower() in allowed_suffixes]
    return sorted(files)


def validate_file(path: Path, min_size_bytes: int) -> None:
    if not path.exists():
        msg = f"file does not exist: {path}"
        raise FileNotFoundError(msg)

    if path.stat().st_size < min_size_bytes:
        msg = f"file too small: {path.name}"
        raise ValueError(msg)


def process_file(path: Path) -> None:
    """
    Placeholder for real business logic.

    For v1, 'processing' just reads the file to prove it is accessible.
    """
    _ = path.read_bytes()


def move_file(path: Path, destination_dir: Path) -> Path:
    destination = destination_dir / path.name
    shutil.move(str(path), str(destination))
    return destination


def handle_file(
    path: Path,
    paths: ServicePaths,
    min_size_bytes: int,
) -> FileProcessResult:
    logger.info("handling file: %s", path.name)

    try:
        validate_file(path, min_size_bytes=min_size_bytes)
        process_file(path)
        destination = move_file(path, paths.processed)
        logger.info("processed file successfully: %s", destination.name)
        return FileProcessResult(
            source=path,
            destination=destination,
            success=True,
            reason="processed",
        )
    except Exception as exc:
        logger.exception("failed processing file: %s", path.name)
        destination = move_file(path, paths.error)
        return FileProcessResult(
            source=path,
            destination=destination,
            success=False,
            reason=str(exc),
        )
