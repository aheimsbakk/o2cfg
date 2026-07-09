"""Tests for o2cfg CLI argument parsing."""

import pytest
from o2cfg.cli import build_parser, parse_args, resolve_verbosity, get_verbosity_label


class TestBuildParser:
    """Test that the argument parser is configured correctly."""

    def test_parser_has_version(self):
        parser = build_parser()
        # Should not raise
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--version"])
        assert exc.value.code == 0

    def test_parser_has_help(self):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0

    def test_parser_has_url_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--url", "http://localhost:8080/v1"])
        assert args.url == "http://localhost:8080/v1"

    def test_parser_has_api_key_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--api-key", "test-key-123"])
        assert args.api_key == "test-key-123"

    def test_parser_has_output_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--output", "/tmp/config.json"])
        assert args.output == "/tmp/config.json"

    def test_parser_has_provider_name_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--provider-name", "My Provider"])
        assert args.provider_name == "My Provider"

    def test_parser_has_provider_provider_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--provider-provider", "custom-provider"])
        assert args.provider_provider == "custom-provider"

    def test_parser_has_timeout_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--timeout", "60"])
        assert args.timeout == 60

    def test_parser_has_model_context_limit_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--model-context-limit", "100000"])
        assert args.model_context_limit == 100000

    def test_parser_has_short_model_context_limit_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-C", "100000"])
        assert args.model_context_limit == 100000

    def test_parser_has_model_output_limit_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--model-output-limit", "32000"])
        assert args.model_output_limit == 32000

    def test_parser_has_short_model_output_limit_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-O", "32000"])
        assert args.model_output_limit == 32000

    def test_parser_has_allowlist_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--allowlist", "gpt-4o,gpt-3.5-turbo"])
        assert args.allowlist == "gpt-4o,gpt-3.5-turbo"

    def test_parser_has_denylist_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--denylist", "text-davinci-001"])
        assert args.denylist == "text-davinci-001"

    def test_short_flags(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "-u",
                "http://localhost:8080/v1",
                "-k",
                "my-key",
                "-o",
                "/tmp/out.json",
                "-n",
                "Test",
                "-t",
                "10",
                "-C",
                "100000",
                "-O",
                "32000",
                "-a",
                "model-a",
                "-d",
                "model-b",
            ]
        )
        assert args.url == "http://localhost:8080/v1"
        assert args.api_key == "my-key"
        assert args.output == "/tmp/out.json"
        assert args.provider_name == "Test"
        assert args.timeout == 10
        assert args.model_context_limit == 100000
        assert args.model_output_limit == 32000
        assert args.allowlist == "model-a"
        assert args.denylist == "model-b"


class TestParseArgs:
    """Test the parse_args wrapper function."""

    def test_parses_with_url(self):
        args = parse_args(["--url", "http://localhost:8080/v1"])
        assert args.url == "http://localhost:8080/v1"

    def test_default_verbosity_is_zero(self):
        args = parse_args(["--url", "http://localhost:8080/v1"])
        assert args.verbosity == 0

    def test_multiple_v_flags_raw_value(self):
        args = parse_args(["-vvvv", "--url", "http://localhost:8080/v1"])
        assert args.verbosity == 4  # default=0 + 4 v flags; resolve_verbosity caps at 3

    def test_multiple_v_flags_resolved(self):
        args = parse_args(["-vvvv", "--url", "http://localhost:8080/v1"])
        assert resolve_verbosity(args) == 3


class TestResolveVerbosity:
    """Test verbosity level resolution."""

    def test_default_is_error(self):
        args = type("Args", (), {"verbosity": 0})()
        assert resolve_verbosity(args) == 0

    def test_single_v_is_warning(self):
        args = type("Args", (), {"verbosity": 1})()
        assert resolve_verbosity(args) == 1

    def test_single_v_is_not_default(self):
        """No flags (0) and -v (1) produce different levels."""
        args_no_flag = type("Args", (), {"verbosity": 0})()
        args_v = type("Args", (), {"verbosity": 1})()
        assert resolve_verbosity(args_no_flag) != resolve_verbosity(args_v)

    def test_info_level(self):
        args = type("Args", (), {"verbosity": 2})()
        assert resolve_verbosity(args) == 2

    def test_debug_level(self):
        args = type("Args", (), {"verbosity": 3})()
        assert resolve_verbosity(args) == 3

    def test_capped_at_three(self):
        args = type("Args", (), {"verbosity": 10})()
        assert resolve_verbosity(args) == 3


class TestGetVerbosityLabel:
    """Test verbosity label resolution."""

    def test_default_is_error(self):
        assert get_verbosity_label(0) == "error"

    def test_warning(self):
        assert get_verbosity_label(1) == "warning"

    def test_info(self):
        assert get_verbosity_label(2) == "info"

    def test_debug(self):
        assert get_verbosity_label(3) == "debug"

    def test_unknown_returns_warning(self):
        assert get_verbosity_label(99) == "warning"
