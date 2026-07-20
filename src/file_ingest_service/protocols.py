from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileSource(Protocol):
    """The inbound boundary: where files arrive from.

    The ingest logic needs exactly one thing from the source - the list of files
    waiting to be handled. By depending on this Protocol rather than on the
    filesystem directly, the service can be driven by an in-memory fake in tests,
    and a future source (an SFTP server, an object store, a message queue) can be
    substituted without touching the ingest logic.

    This is the Dependency Inversion Principle: the high-level ingest policy
    depends on an abstraction, and the low-level filesystem detail depends on
    that same abstraction by satisfying it.
    """

    def list_pending(self) -> list[Path]:
        """Return the files waiting to be handled, already filtered and sorted."""
        ...


class FileRouter(Protocol):
    """The outbound boundary: where files go after being handled.

    Every file ends in exactly one of two places - processed or error - so the
    router has exactly two methods. Two explicit methods are preferred over a
    single parameterized ``route(path, outcome)`` because the call site reads as
    the decision it is making, and the fake stays trivial.

    Both methods return the destination path and raise on failure; the ingest
    logic decides what a failure means.
    """

    def route_processed(self, path: Path) -> Path:
        """Move a successfully handled file to the processed area."""
        ...

    def route_error(self, path: Path) -> Path:
        """Move a failed file to the error area, quarantining it.

        Quarantining is deliberate: unlike a service that leaves a failed item in
        place to retry, moving the file out of the inbox means a permanently bad
        file is set aside once instead of failing on every run forever.
        """
        ...
