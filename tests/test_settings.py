"""Tests for settings resolution and validation.

Pure logic, no fakes needed: resolution precedence (env > toml > default),
suffix normalization on every construction path, and fail-fast PROD validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from file_ingest_service.settings import (
    DEFAULT_ALLOWED_SUFFIXES,
    DEFAULT_APP_NAME,
    DEFAULT_DATA_DIR,
    DEFAULT_ENV,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MIN_SIZE_BYTES,
    ENV_PREFIX,
    Settings,
    _normalize_suffixes,  # pyright: ignore[reportPrivateUsage]
    load_settings,
)


class TestDefaults:
    def test_defaults_are_applied(self) -> None:
        s = Settings()
        assert s.app_name == DEFAULT_APP_NAME
        assert s.log_level == DEFAULT_LOG_LEVEL
        assert s.env == DEFAULT_ENV
        assert s.data_dir == DEFAULT_DATA_DIR
        assert s.allowed_suffixes == DEFAULT_ALLOWED_SUFFIXES
        assert s.min_size_bytes == DEFAULT_MIN_SIZE_BYTES


class TestValidation:
    def test_invalid_log_level_rejected(self) -> None:
        with pytest.raises(ValueError, match="log_level"):
            Settings(log_level="CHATTY")

    def test_invalid_env_rejected(self) -> None:
        with pytest.raises(ValueError, match="env"):
            Settings(env="STAGING")

    def test_zero_min_size_bytes_rejected(self) -> None:
        with pytest.raises(ValueError, match="min_size_bytes"):
            Settings(min_size_bytes=0)


class TestSuffixNormalization:
    def test_normalized_on_construction(self) -> None:
        """Direct construction must normalize the same way load_settings does."""
        s = Settings(allowed_suffixes=("CSV", ".TXT ", ""))
        assert s.allowed_suffixes == (".csv", ".txt")

    def test_adds_leading_dot(self) -> None:
        assert _normalize_suffixes(["csv", "txt"]) == (".csv", ".txt")

    def test_lowercases(self) -> None:
        assert _normalize_suffixes([".CSV", ".TXT"]) == (".csv", ".txt")

    def test_skips_blanks(self) -> None:
        assert _normalize_suffixes([".csv", "", "  ", ".txt"]) == (".csv", ".txt")

    def test_empty_input_falls_back_to_default(self) -> None:
        assert _normalize_suffixes([]) == DEFAULT_ALLOWED_SUFFIXES


class TestProdValidation:
    def test_prod_with_blank_required_field_fails_fast(self) -> None:
        with pytest.raises(ValueError, match="required in PROD"):
            Settings(env="PROD", data_dir="")

    def test_prod_error_names_the_missing_field(self) -> None:
        with pytest.raises(ValueError) as exc:
            Settings(env="PROD", data_dir="   ")
        assert "data_dir" in str(exc.value)

    def test_fully_configured_prod_is_valid(self) -> None:
        assert Settings(env="PROD", data_dir="data").env == "PROD"

    def test_dev_stays_lenient(self) -> None:
        Settings(env="DEV", data_dir="")  # must not raise


class TestResolution:
    def test_loads_from_toml(self, tmp_path: Path) -> None:
        path = tmp_path / "app.toml"
        path.write_text(
            """
[app]
name = "test-service"
log_level = "DEBUG"
env = "TEST"

[service]
data_dir = "data"
allowed_suffixes = [".csv", ".txt"]
min_size_bytes = 3
""".strip(),
            encoding="utf-8",
        )

        s = load_settings(path)

        assert s.app_name == "test-service"
        assert s.log_level == "DEBUG"
        assert s.env == "TEST"
        assert s.allowed_suffixes == (".csv", ".txt")
        assert s.min_size_bytes == 3

    def test_missing_toml_uses_defaults(self, tmp_path: Path) -> None:
        assert load_settings(tmp_path / "missing.toml") == Settings()

    def test_partial_toml_uses_defaults_for_the_rest(self, tmp_path: Path) -> None:
        path = tmp_path / "app.toml"
        path.write_text('[app]\nname = "partial"\n', encoding="utf-8")

        s = load_settings(path)

        assert s.app_name == "partial"
        assert s.log_level == DEFAULT_LOG_LEVEL
        assert s.data_dir == DEFAULT_DATA_DIR

    def test_env_overrides_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        path = tmp_path / "app.toml"
        path.write_text('[app]\nlog_level = "INFO"\n', encoding="utf-8")
        monkeypatch.setenv(f"{ENV_PREFIX}_LOG_LEVEL", "WARNING")

        assert load_settings(path).log_level == "WARNING"

    def test_env_suffixes_are_split_and_normalized(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(f"{ENV_PREFIX}_ALLOWED_SUFFIXES", ".CSV, txt")

        assert load_settings(tmp_path / "missing.toml").allowed_suffixes == (".csv", ".txt")
