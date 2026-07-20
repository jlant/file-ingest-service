# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Architecture rework: the ingest logic now depends on boundary Protocols rather
than the filesystem directly, the service runs a single pass, and the test suite
is behavior-based with no mocking. This turns the project into a worked
reference implementation of the pattern.

### Added

- `FileSource` and `FileRouter` boundary Protocols, with `LocalFileSource` and
  `LocalFileRouter` as the filesystem implementations.
- A factory-method seam on `Service` (`_make_source`, `_make_router`) so tests
  supply fakes by subclassing instead of patching.
- `tests/conftest.py` with in-memory fakes and two autouse fixtures:
  `clean_app_environment` (strips `APP_*` before each test) and
  `isolate_root_logger` (snapshots and restores the root logger), so tests never
  depend on ambient state.
- Fail-fast PROD validation via `REQUIRED_IN_PROD` in `settings.py`.
- A `log_file` setting with rotating file logging.
- Architecture and runtime-flow diagrams in `docs/`, referenced from the README.

### Changed

- `Service.run` performs a single pass and returns; when an external scheduler
  drives the service, the scheduler is the loop.
- `handle_file` takes a `FileRouter` rather than reaching for `shutil` directly,
  and routes to the error area whenever processing or the processed-route fails.
- `configure_logging` manages the root logger's handlers explicitly and is safe
  to call more than once, replacing `logging.basicConfig`.
- `allowed_suffixes` is normalized on every construction path, not only when
  loaded from TOML.
- Tests rewritten around fakes and grouped by the property each guards; all
  `unittest.mock` patching removed.

### Removed

- The `run_seconds` and `poll_interval_seconds` settings and the polling loop.
- The optional `pipeline.py` module, its tests, and the `yaml` extra.
- Leftover project-template infrastructure references.

## [0.1.0] - 2026-04-24

### Added

- Initial commit with minor changes to files to remove artifacts from the
  [Python Standard Template](https://github.com/jlant/python-service-template)


[Unreleased]: https://github.com/jlant/file-ingest-service/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jlant/file-ingest-service/releases/tag/v0.1.0
