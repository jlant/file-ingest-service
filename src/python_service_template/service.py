from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from .settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class Service:
    settings: Settings
    started: bool = field(default=False, init=False)

    def start(self) -> None:
        logger.info("starting service", extra={"app_name": self.settings.app_name})
        self.started = True

    def run(self) -> None:
        if not self.started:
            msg = "service must be started before run()"
            raise RuntimeError(msg)

        logger.info(
            "running service",
            extra={
                "app_name": self.settings.app_name,
                "env": self.settings.env,
                "run seconds": self.settings.run_seconds,
            },
        )
        time.sleep(self.settings.run_seconds)

    def stop(self) -> None:
        logger.info("stopping service", extra={"app_name": self.settings.app_name})
        self.started = False
