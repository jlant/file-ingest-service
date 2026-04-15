# File Ingest Service

A directory watcher ingestion service that detects new files, validates them, moves them through an inbox/processed/error steps, and logs each step.

Essentially, a small polling service that:

- watches an inbox/ directory
- discovers new files
- validates basic rules
- processes each file
- moves it to processed/ or error/
- logs every step


The service maps well to industrial/manufacturing processes where a lot of integration work starts with “something drops files somewhere, and we need to process them reliably.”

## Development workflow

```bash
uv lock
uv sync --all-extras --dev
pre-commit install

# Format
uv run nox -s fmt

# Lint + type check
uv run nox -s lint

# Run tests
uv run nox -s tests

# Create a sample file
uv run pst seed --filename sample.txt --content "hello world"

# Check that read-config command works
uv run fis read-config

# Check that run command works
uv run pst run

```
## Quick start

```bash
# Create a sample file
uv run pst seed --filename sample.txt --content "hello world"

# Check that read-config command works
uv run fis read-config

# Check that run command works
uv run pst run
```

After running, you should see:
```
data/
  inbox/
  processed/
    sample.txt
  error/
```
