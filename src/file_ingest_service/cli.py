from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import typer
from rich import print

from .config import resolve_settings
from .logging import configure_logging
from .paths import build_service_paths
from .service import Service
from .settings import Settings

DIST_NAME = "file-ingest-service"
CLI_NAME = "fis"

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",  # Allows for help text to use [bold], [green], etc.
    epilog="Made with :heart:  by [blue]Jeremiah Lant[/blue]",  # Footer text
)


def version_callback(value: bool):
    if value:
        try:
            v = version(DIST_NAME)
        except PackageNotFoundError:
            v = "0.0.0"
        print(f"{CLI_NAME} {v}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version_opt: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show app version and exit.",
    ),
):
    """
    [green] File Ingest Service (FIS) CLI Tool[/green] :rocket:

    A directory watcher ingestion service that detects new files,
    validates them, moves them through an inbox/processed/error steps,
    and logs each step.
    """
    _ = ctx
    _ = version_opt


@app.command()
def read_config(
    config: Annotated[Path, typer.Option("--config", "-c", exists=False)] = Path("config/app.toml"),
) -> None:
    """Read config and print resolved settings"""
    settings: Settings = resolve_settings(config)
    print(f"app_name={settings.app_name!r}")
    print(f"log_level={settings.log_level!r}")
    print(f"env={settings.env!r}")
    print(f"run_seconds={settings.run_seconds!r}")
    print(f"poll_interval_seconds={settings.poll_interval_seconds!r}")
    print(f"data_dir={settings.data_dir!r}")
    print(f"allowed_suffixes={settings.allowed_suffixes!r}")
    print(f"min_size_bytes={settings.min_size_bytes!r}")


@app.command()
def seed(
    filename: str = typer.Option("sample.txt", "--filename"),
    content: str = typer.Option("hello from file ingest service (fis)", "--content"),
    config: Annotated[Path, typer.Option("--config", "-c", exists=False)] = Path("config/app.toml"),
) -> None:
    """Create a sample input file in the inbox directory."""
    settings = resolve_settings(config)
    paths = build_service_paths(Path(settings.data_dir))
    paths.ensure_directories()

    target = paths.inbox / filename
    target.write_text(content, encoding="utf-8")

    print(f"created sample file: {target}")


@app.command()
def run(
    config: Annotated[Path, typer.Option("--config", "-c", exists=False)] = Path("config/app.toml"),
) -> None:
    """Run the service lifecycle."""
    settings = resolve_settings(config)
    configure_logging(settings)

    service = Service(settings)
    service.start()
    try:
        service.run()
    finally:
        service.stop()
