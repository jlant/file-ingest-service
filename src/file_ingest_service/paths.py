from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServicePaths:
    inbox: Path
    processed: Path
    error: Path


def build_service_paths(base_dir: Path) -> ServicePaths:
    return ServicePaths(
        inbox=base_dir / "inbox",
        processed=base_dir / "processed",
        error=base_dir / "error",
    )


def ensure_directories(paths: ServicePaths) -> None:
    paths.inbox.mkdir(parents=True, exist_ok=True)
    paths.processed.mkdir(parents=True, exist_ok=True)
    paths.error.mkdir(parents=True, exist_ok=True)
