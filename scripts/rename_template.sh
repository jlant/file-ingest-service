#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/rename_template.sh new_pkg_name new_cli_name new_project_name
#
# Example:
#   ./scripts/rename_template.sh my_service mst "My Service Template"
#
# This produces:
#   package/import name: my_service
#   CLI name: mst
#   distribution/app name: my-service

NEW_PKG="${1:?new package/import name (e.g. my_service)}"
NEW_CLI="${2:?new cli command (e.g. mst)}"
NEW_PROJ="${3:?new project display name (e.g. My Service)}"

OLD_PKG="python_service_template"
OLD_CLI="pst"
OLD_DIST="python-service-template"

# Derive a normalized distribution/app name from the package name.
# This keeps packaging names valid and predictable.
NEW_DIST="${NEW_PKG//_/-}"

# Rename package directory
if [[ -d "src/${OLD_PKG}" ]]; then
  git mv "src/${OLD_PKG}" "src/${NEW_PKG}" 2>/dev/null || mv "src/${OLD_PKG}" "src/${NEW_PKG}"
fi

# Replace strings (simple heuristic)
python - "$NEW_PKG" "$NEW_CLI" "$NEW_PROJ" "$OLD_PKG" "$OLD_CLI" "$OLD_DIST" "$NEW_DIST" <<'PY'
import pathlib
import sys

NEW_PKG = sys.argv[1]
NEW_CLI = sys.argv[2]
NEW_PROJ = sys.argv[3]
OLD_PKG = sys.argv[4]
OLD_CLI = sys.argv[5]
OLD_DIST = sys.argv[6]
NEW_DIST = sys.argv[7]

SKIP_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
    ".pyright",
}

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".pyc",
}

for p in pathlib.Path(".").rglob("*"):
    if p.is_dir():
        continue

    if any(part in SKIP_DIRS for part in p.parts):
        continue

    if p.suffix.lower() in SKIP_SUFFIXES:
        continue

    if p.name == "uv.lock":
        continue

    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue

    txt2 = txt

    # Project / distribution metadata
    txt2 = txt2.replace(f'name = "{OLD_DIST}"', f'name = "{NEW_DIST}"')
    txt2 = txt2.replace(f'DIST_NAME = "{OLD_DIST}"', f'DIST_NAME = "{NEW_DIST}"')
    txt2 = txt2.replace(f'DEFAULT_APP_NAME = "{OLD_DIST}"', f'DEFAULT_APP_NAME = "{NEW_DIST}"')

    # Package / import paths
    txt2 = txt2.replace(f"from {OLD_PKG}.", f"from {NEW_PKG}.")
    txt2 = txt2.replace(f'"{OLD_PKG}.', f'"{NEW_PKG}.')
    txt2 = txt2.replace(f"src/{OLD_PKG}", f"src/{NEW_PKG}")

    # Console script entrypoint
    txt2 = txt2.replace(
        f'{OLD_CLI} = "{OLD_PKG}.cli:app"',
        f'{NEW_CLI} = "{NEW_PKG}.cli:app"',
    )

    # Human-facing CLI label in code/help output
    txt2 = txt2.replace(f'CLI_NAME = "{OLD_CLI}"', f'CLI_NAME = "{NEW_CLI}"')

    # README/project title
    txt2 = txt2.replace("# File Ingest Service", f"# {NEW_PROJ}")

    if txt2 != txt:
        p.write_text(txt2, encoding="utf-8")
PY

echo "Renamed package to '${NEW_PKG}', CLI to '${NEW_CLI}', project to '${NEW_PROJ}'."
echo "Derived distribution/app name: '${NEW_DIST}'"
echo "Next steps:"
echo "  uv lock"
echo "  uv sync --all-extras --dev"
echo "  pre-commit install"
echo "  uv run nox -s lint"
echo "  uv run nox -s tests"
