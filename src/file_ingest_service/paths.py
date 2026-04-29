from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServicePaths:
    inbox: Path
    processed: Path
    error: Path

    def ensure_directories(self) -> None:
        """Create all service directories, including any missing parents."""
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.processed.mkdir(parents=True, exist_ok=True)
        self.error.mkdir(parents=True, exist_ok=True)


def build_service_paths(base_dir: Path | str) -> ServicePaths:
    """Build the ServicePaths directories."""
    if isinstance(base_dir, str):
        base_dir = Path(base_dir)

    base_dir = base_dir.resolve()

    if base_dir.exists() and not base_dir.is_dir():
        msg = f"base_dir exists but is not a directory: {base_dir}"
        raise ValueError(msg)

    return ServicePaths(
        inbox=base_dir / "inbox",
        processed=base_dir / "processed",
        error=base_dir / "error",
    )
