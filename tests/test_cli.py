"""Tests for src/cli.py — argument parsing."""

import pytest

from src.cli import build_parser, parse_args
from src.render.theme import AVAILABLE_THEMES

# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------


class TestBuildParser:
    def test_returns_parser(self):
        import argparse

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_description(self):
        parser = build_parser()
        assert parser.description is not None


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestParseArgsDefaults:
    def test_no_args_dry_run_false(self):
        args = parse_args([])
        assert args.dry_run is False

    def test_no_args_dummy_false(self):
        args = parse_args([])
        assert args.dummy is False

    def test_no_args_force_full_refresh_false(self):
        args = parse_args([])
        assert args.force_full_refresh is False

    def test_no_args_ignore_breakers_false(self):
        args = parse_args([])
        assert args.ignore_breakers is False

    def test_no_args_check_config_false(self):
        args = parse_args([])
        assert args.check_config is False

    def test_no_args_date_none(self):
        args = parse_args([])
        assert args.date is None

    def test_no_args_theme_none(self):
        args = parse_args([])
        assert args.theme is None

    def test_no_args_config_default(self):
        args = parse_args([])
        assert args.config == "config/config.yaml"


# ---------------------------------------------------------------------------
# Individual flags
# ---------------------------------------------------------------------------


class TestParseArgsSingleFlags:
    def test_dry_run_flag(self):
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_dummy_flag(self):
        args = parse_args(["--dummy"])
        assert args.dummy is True

    def test_force_full_refresh_flag(self):
        args = parse_args(["--force-full-refresh"])
        assert args.force_full_refresh is True

    def test_ignore_breakers_flag(self):
        args = parse_args(["--ignore-breakers"])
        assert args.ignore_breakers is True

    def test_check_config_flag(self):
        args = parse_args(["--check-config"])
        assert args.check_config is True

    def test_custom_config_path(self):
        args = parse_args(["--config", "/tmp/my_config.yaml"])
        assert args.config == "/tmp/my_config.yaml"


# ---------------------------------------------------------------------------
# --theme
# ---------------------------------------------------------------------------


class TestParseArgsTheme:
    def test_valid_theme_default(self):
        args = parse_args(["--theme", "default"])
        assert args.theme == "default"

    def test_valid_theme_terminal(self):
        args = parse_args(["--theme", "terminal"])
        assert args.theme == "terminal"

    def test_valid_theme_weather(self):
        args = parse_args(["--theme", "weather"])
        assert args.theme == "weather"

    def test_all_available_themes_accepted(self):
        for theme in AVAILABLE_THEMES:
            args = parse_args(["--theme", theme])
            assert args.theme == theme

    def test_invalid_theme_raises_system_exit(self):
        with pytest.raises(SystemExit):
            parse_args(["--theme", "totally_fake_theme_xyz"])


# ---------------------------------------------------------------------------
# --date validation
# ---------------------------------------------------------------------------


class TestParseArgsDate:
    def test_valid_date_with_dry_run(self):
        args = parse_args(["--dry-run", "--date", "2025-12-25"])
        assert args.date == "2025-12-25"
        assert args.dry_run is True

    def test_date_without_dry_run_raises_system_exit(self):
        with pytest.raises(SystemExit):
            parse_args(["--date", "2025-12-25"])

    def test_invalid_date_format_raises_system_exit(self):
        with pytest.raises(SystemExit):
            parse_args(["--dry-run", "--date", "25-12-2025"])

    def test_invalid_date_not_iso_raises_system_exit(self):
        with pytest.raises(SystemExit):
            parse_args(["--dry-run", "--date", "December 25 2025"])

    def test_invalid_date_partial_raises_system_exit(self):
        with pytest.raises(SystemExit):
            parse_args(["--dry-run", "--date", "2025-13"])

    def test_valid_date_boundary_new_year(self):
        args = parse_args(["--dry-run", "--date", "2025-01-01"])
        assert args.date == "2025-01-01"

    def test_valid_date_leap_day(self):
        args = parse_args(["--dry-run", "--date", "2024-02-29"])
        assert args.date == "2024-02-29"

    def test_invalid_leap_day_non_leap_year_raises(self):
        with pytest.raises(SystemExit):
            parse_args(["--dry-run", "--date", "2025-02-29"])


# ---------------------------------------------------------------------------
# --version
# ---------------------------------------------------------------------------


class TestParseArgsVersion:
    def test_version_exits_with_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_version_output_contains_version_string(self, capsys):
        with pytest.raises(SystemExit):
            parse_args(["--version"])
        captured = capsys.readouterr()
        # Version should appear in stdout
        assert any(char.isdigit() for char in captured.out)


# ---------------------------------------------------------------------------
# Flag combinations
# ---------------------------------------------------------------------------


class TestParseArgsCombinations:
    def test_dry_run_and_dummy(self):
        args = parse_args(["--dry-run", "--dummy"])
        assert args.dry_run is True
        assert args.dummy is True

    def test_dry_run_dummy_and_theme(self):
        args = parse_args(["--dry-run", "--dummy", "--theme", "default"])
        assert args.dry_run is True
        assert args.dummy is True
        assert args.theme == "default"

    def test_dry_run_with_date_and_theme(self):
        args = parse_args(["--dry-run", "--date", "2025-06-15", "--theme", "weather"])
        assert args.dry_run is True
        assert args.date == "2025-06-15"
        assert args.theme == "weather"

    def test_force_full_refresh_and_ignore_breakers(self):
        args = parse_args(["--force-full-refresh", "--ignore-breakers"])
        assert args.force_full_refresh is True
        assert args.ignore_breakers is True

    def test_all_non_conflicting_flags(self):
        args = parse_args(
            [
                "--dry-run",
                "--dummy",
                "--force-full-refresh",
                "--ignore-breakers",
                "--check-config",
                "--config",
                "custom.yaml",
            ]
        )
        assert args.dry_run is True
        assert args.dummy is True
        assert args.force_full_refresh is True
        assert args.ignore_breakers is True
        assert args.check_config is True
        assert args.config == "custom.yaml"
