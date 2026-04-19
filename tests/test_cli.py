"""Tests for CLI configuration and validation functions."""

from unittest.mock import patch

import pytest


class TestLoadConfigSafely:
    """Tests for load_config_safely function."""

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid JSON config file."""
        from kwaras.cli import load_config_safely

        result = load_config_safely(str(temp_config_file))

        assert result == {
            "EAFL_DIR": "lexicons/Mixtec",
            "LIFT": "lexicons/Mixtec/Mixtec.lift",
        }

    def test_load_missing_file_raises(self):
        """Test that missing file raises FileNotFoundError."""
        from kwaras.cli import load_config_safely

        with pytest.raises(FileNotFoundError):
            load_config_safely("nonexistent.cfg")

    def test_load_invalid_json_raises(self, temp_invalid_json_config):
        """Test that invalid JSON raises ValueError."""
        from kwaras.cli import load_config_safely

        with pytest.raises(ValueError):
            load_config_safely(str(temp_invalid_json_config))

    def test_load_empty_file_returns_empty_dict(self, temp_empty_config):
        """Test that empty file returns empty dict."""
        from kwaras.cli import load_config_safely

        result = load_config_safely(str(temp_empty_config))

        assert result == {}


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_missing_keys_raises(self):
        """Test that missing required keys raise ValueError."""
        from kwaras.cli import validate_config

        config = {"EAFL_DIR": "some/path"}
        required_keys = ["EAFL_DIR", "LIFT"]

        with pytest.raises(ValueError) as exc_info:
            validate_config(config, required_keys)

        assert "LIFT" in str(exc_info.value)

    def test_validate_all_keys_present(self, valid_lexicon_config):
        """Test that config with all required keys passes."""
        from kwaras.cli import validate_config

        # Should not raise
        validate_config(valid_lexicon_config, ["EAFL_DIR", "LIFT"])

    def test_validate_empty_config_missing_all_keys(self):
        """Test that empty config with required keys raises."""
        from kwaras.cli import validate_config

        with pytest.raises(ValueError):
            validate_config({}, ["EAFL_DIR", "LIFT"])


class TestValidateDependencies:
    """Tests for validate_dependencies function."""

    def test_validate_openpyxl_present(self):
        """Test that openpyxl is detected as present."""
        from kwaras.cli import validate_dependencies

        missing = validate_dependencies()

        assert "openpyxl" not in missing

    def test_validate_missing_dep(self):
        """Test that missing dependency is detected."""
        from kwaras.cli import validate_dependencies

        missing = validate_dependencies()

        # Should return list (may be empty)
        assert isinstance(missing, list)


class TestCheckInstall:
    """Tests for check_install_cli function."""

    def test_check_install_returns_int(self):
        """Test that check_install returns an integer."""
        from kwaras.cli import check_install_cli

        result = check_install_cli()

        assert isinstance(result, int)

    def test_check_install_imports_package(self):
        """Test that kwaras package can be imported."""
        import kwaras

        assert kwaras.__version__ == "3.0.0"


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parse_default_args(self):
        """Test parsing default arguments."""
        with patch("sys.argv", ["kwaras"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.verbose is False

    def test_parse_verbose_flag(self):
        """Test parsing verbose flag."""
        with patch("sys.argv", ["kwaras", "-v"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.verbose is True

    def test_parse_convert_lexicon_command(self):
        """Test parsing convert-lexicon subcommand."""
        with patch("sys.argv", ["kwaras", "convert-lexicon", "--config", "test.cfg"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.command == "convert-lexicon"
            assert args.config == "test.cfg"

    def test_parse_export_corpus_command(self):
        """Test parsing export-corpus subcommand."""
        with patch("sys.argv", ["kwaras", "export-corpus", "--config", "test.cfg"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.command == "export-corpus"
            assert args.config == "test.cfg"

    def test_parse_check_install_command(self):
        """Test parsing check-install subcommand."""
        with patch("sys.argv", ["kwaras", "check-install"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.command == "check-install"


class TestIsHeadless:
    """Tests for is_headless function."""

    def test_is_headless_returns_bool(self):
        """Test that is_headless returns a boolean."""
        from kwaras.cli import is_headless

        result = is_headless()

        assert isinstance(result, bool)


class TestEntryPoints:
    """Tests for console_scripts entry points."""

    def test_convert_lexicon_cmd_exists(self):
        """Test convert_lexicon_cmd entry point exists."""
        from kwaras.cli import convert_lexicon_cmd

        assert callable(convert_lexicon_cmd)

    def test_export_corpus_cmd_exists(self):
        """Test export_corpus_cmd entry point exists."""
        from kwaras.cli import export_corpus_cmd

        assert callable(export_corpus_cmd)

    def test_check_install_cmd_exists(self):
        """Test check_install_cmd entry point exists."""
        from kwaras.cli import check_install_cmd

        assert callable(check_install_cmd)

    def test_main_exists(self):
        """Test main entry point exists."""
        from kwaras.cli import main

        assert callable(main)


class TestLegacyFlags:
    """Tests for legacy GUI compatibility flags."""

    def test_parse_convert_lexicon_legacy_flag(self):
        """Test parsing legacy --convert-lexicon flag."""
        with patch("sys.argv", ["kwaras", "--convert-lexicon"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.convert_lexicon is True

    def test_parse_export_corpus_legacy_flag(self):
        """Test parsing legacy --export-corpus flag."""
        with patch("sys.argv", ["kwaras", "--export-corpus"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.export_corpus is True

    def test_parse_select_action_legacy_flag(self):
        """Test parsing legacy --select-action flag."""
        with patch("sys.argv", ["kwaras", "--select-action"]):
            from kwaras.cli import parse_args

            args = parse_args()
            assert args.select_action is True


class TestExitCodes:
    """Tests for proper exit codes from CLI commands."""

    def test_check_install_returns_0_when_installed(self):
        """Test check_install returns 0 when package is installed."""
        from kwaras.cli import check_install_cli

        result = check_install_cli()

        assert result == 0

    def test_convert_lexicon_returns_1_on_missing_config(self):
        """Test convert_lexicon returns 1 on missing config."""
        from kwaras.cli import convert_lexicon_cli

        result = convert_lexicon_cli("nonexistent.cfg")

        assert result == 1

    def test_export_corpus_returns_1_on_missing_config(self):
        """Test export_corpus returns 1 on missing config."""
        from kwaras.cli import export_corpus_cli

        result = export_corpus_cli("nonexistent.cfg")

        assert result == 1


class TestConfigValidationErrors:
    """Tests for clear error messages from config validation."""

    def test_missing_required_key_error_message(self):
        """Test that missing required key produces clear error."""
        from kwaras.cli import validate_config

        config = {"EAFL_DIR": "some/path"}
        required_keys = ["EAFL_DIR", "LIFT"]

        with pytest.raises(ValueError) as exc_info:
            validate_config(config, required_keys)

        assert "LIFT" in str(exc_info.value)
        assert "missing" in str(exc_info.value).lower()

    def test_missing_file_error_message(self):
        """Test that missing config file produces clear error."""
        from kwaras.cli import load_config_safely

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config_safely("nonexistent.cfg")

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_json_error_message(self, temp_invalid_json_config):
        """Test that invalid JSON produces clear error."""
        from kwaras.cli import load_config_safely

        with pytest.raises(ValueError) as exc_info:
            load_config_safely(str(temp_invalid_json_config))

        assert "invalid" in str(exc_info.value).lower() or "json" in str(exc_info.value).lower()
