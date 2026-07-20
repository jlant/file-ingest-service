from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .ingest import handle_file
from .local_files import LocalFileRouter, LocalFileSource
from .paths import ServicePaths, build_service_paths
from .protocols import FileRouter, FileSource
from .settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class Service:
    settings: Settings
    started: bool = field(default=False, init=False)
    paths: ServicePaths = field(init=False)

    def __post_init__(self) -> None:
        self.paths = build_service_paths(Path(self.settings.data_dir))

    def start(self) -> None:
        self.paths.ensure_directories()
        logger.info(
            "starting service app=%s env=%s data_dir=%s",
            self.settings.app_name,
            self.settings.env,
            self.settings.data_dir,
        )
        self.started = True

    # --- Boundary factories (overridden in tests to return fakes) ---------
    # These are the seam. _run_cycle is pure orchestration and obtains its two
    # boundaries through these methods, so a test subclasses Service and
    # overrides them to return in-memory fakes - no mocking, no patching.

    def _make_source(self) -> FileSource:
        """Return the inbound boundary."""
        return LocalFileSource(
            inbox=self.paths.inbox,
            allowed_suffixes=self.settings.allowed_suffixes,
        )

    def _make_router(self) -> FileRouter:
        """Return the outbound boundary."""
        return LocalFileRouter(self.paths)

    def _run_cycle(self) -> None:
        source = self._make_source()
        router = self._make_router()

        files = source.list_pending()

        if not files:
            logger.info("no files in inbox")
            return

        logger.info("found %s file(s) to process", len(files))

        for path in files:
            result = handle_file(
                path=path,
                router=router,
                min_size_bytes=self.settings.min_size_bytes,
            )
            logger.info(
                "file result name=%s success=%s reason=%s",
                result.destination.name,
                result.success,
                result.reason,
            )

    def run(self) -> None:
        if not self.started:
            msg = "service must be started before run()"
            raise RuntimeError(msg)

        logger.info("running service app=%s env=%s", self.settings.app_name, self.settings.env)

        # One pass over the inbox, then return. If an external scheduler drives
        # this service, the scheduler is the loop - the service must not loop.
        self._run_cycle()

    def stop(self) -> None:
        if not self.started:
            logger.warning("stop() called but service is not running")
            return
        logger.info(
            "stopping service app=%s env=%s",
            self.settings.app_name,
            self.settings.env,
        )
        self.started = False
