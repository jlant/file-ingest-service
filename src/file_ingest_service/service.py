from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from .ingest import get_input_files, handle_file
from .paths import ServicePaths, build_service_paths
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

    def _run_cycle(self) -> None:
        files = get_input_files(
            self.paths.inbox,
            allowed_suffixes=self.settings.allowed_suffixes,
        )

        if files:
            logger.info("found %s file(s) to process", len(files))

        for path in files:
            result = handle_file(
                path=path,
                paths=self.paths,
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

        logger.info(
            "running service app=%s env=%s run_seconds=%s",
            self.settings.app_name,
            self.settings.env,
            self.settings.run_seconds,
        )

        # Set the deadline
        deadline = time.monotonic() + self.settings.run_seconds

        # Run the service until deadline is exceeded and perform at least one run cycle
        while True:
            self._run_cycle()
            if time.monotonic() >= deadline:
                break
            time.sleep(self.settings.poll_interval_seconds)

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
