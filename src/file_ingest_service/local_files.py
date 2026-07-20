from __future__ import annotations

import logging
import shutil
from pathlib import Path

from .paths import ServicePaths

logger = logging.getLogger(__name__)


class LocalFileSource:
    """The inbound boundary, backed by a local inbox directory.

    Satisfies the FileSource Protocol. Owns the suffix filtering and sorting, so
    "what counts as pending" is decided in one place.
    """

    def __init__(self, inbox: Path, allowed_suffixes: tuple[str, ...]) -> None:
        self._inbox = inbox
        self._allowed_suffixes = allowed_suffixes

    def list_pending(self) -> list[Path]:
        files = [p for p in self._inbox.iterdir() if p.is_file()]
        if self._allowed_suffixes:
            files = [p for p in files if p.suffix.lower() in self._allowed_suffixes]
        return sorted(files)


class LocalFileRouter:
    """The outbound boundary, backed by local processed/ and error/ directories.

    Satisfies the FileRouter Protocol. Both operations are moves: a handled file
    leaves the inbox exactly once, so the inbox always reflects work still to do.
    """

    def __init__(self, paths: ServicePaths) -> None:
        self._paths = paths

    def _move(self, path: Path, destination_dir: Path) -> Path:
        destination = destination_dir / path.name
        shutil.move(path, destination)
        logger.info("moved file: %s -> %s", path.name, destination)
        return destination

    def route_processed(self, path: Path) -> Path:
        return self._move(path, self._paths.processed)

    def route_error(self, path: Path) -> Path:
        return self._move(path, self._paths.error)
