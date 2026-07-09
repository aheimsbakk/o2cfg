"""Tests for o2cfg Config Resolver."""

import os
import pytest
from o2cfg.config import (
    resolve_settings,
    Settings,
    _parse_comma_list,
)
from o2cfg.provider_name import derive_provider_name


class TestParseCommaList:
    """Test comma-separated list parsing."""

    def test_none_returns_none(self):
        assert _parse_comma_list(None) is None

    def test_empty_string_returns_empty_list(self):
        assert _parse_comma_list("") == []

    def test_single_value(self):
        assert _parse_comma_list("gpt-4o") == ["gpt-4o"]

    def test_multiple_values(self):
        result = _parse_comma_list("gpt-4o,gpt-3.5-turbo,claude-3")
        assert result == ["gpt-4o", "gpt-3.5-turbo", "claude-3"]

    def test_strips_whitespace(self):
        result = _parse_comma_list(" gpt-4o , gpt-3.5-turbo ")
        assert result == ["gpt-4o", "gpt-3.5-turbo"]

    def test_only_commas_returns_empty(self):
        assert _parse_comma_list(",,,") == []


class TestDeriveProviderName:
    """Test provider name derivation from URL."""

    def test_localhost(self):
        assert derive_provider_name("http://localhost:8080/v1") == "localhost"

    def test_subdomain(self):
        assert derive_provider_name("https://api.anthropic.com/v1/") == "anthropic"

    def test_two_labels(self):
        assert derive_provider_name("http://vllm.internal:8000/v1") == "vllm"

    def test_hyphens_in_second_to_last_label(self):
        assert derive_provider_name("http://my-server.com/v1") == "my server"

    def test_underscores_in_second_to_last_label(self):
        assert derive_provider_name("http://my_server.com/v1") == "my server"

    def test_empty_hostname(self):
        assert derive_provider_name("http:///v1") == "OpenAI-compatible"

    def test_no_scheme(self):
        assert derive_provider_name("localhost:8080/v1") == "localhost"

    def test_default_fallback_on_error(self):
        assert derive_provider_name("") == "OpenAI-compatible"


class TestResolveSettings:
    """Test settings resolution from CLI args and env vars."""

    def test_minimal_settings(self):
        settings = resolve_settings(base_url="http://localhost:8080/v1")
        assert settings.base_url == "http://localhost:8080/v1"
        assert settings.api_key is None
        assert settings.output_file_path is None
        assert settings.provider_name == "localhost"
        assert settings.provider_npm == "@ai-sdk/openai-compatible"
        assert settings.timeout == 30
        assert settings.model_context_limit is None
        assert settings.model_output_limit is None
        assert settings.allowlist is None
        assert settings.denylist is None
        assert settings.verbosity == 1

    def test_all_options(self):
        settings = resolve_settings(
            base_url="http://localhost:8080/v1",
            api_key="sk-test-123",
            output_file_path="/tmp/config.json",
            provider_name="My Provider",
            provider_npm="custom-npm",
            timeout=60,
            model_context_limit=100000,
            model_output_limit=32000,
            allowlist="gpt-4o,gpt-3.5",
            denylist="old-model",
            verbosity=3,
        )
        assert settings.api_key == "sk-test-123"
        assert settings.output_file_path == "/tmp/config.json"
        assert settings.provider_name == "My Provider"
        assert settings.provider_npm == "custom-npm"
        assert settings.timeout == 60
        assert settings.model_context_limit == 100000
        assert settings.model_output_limit == 32000
        assert settings.allowlist == ["gpt-4o", "gpt-3.5"]
        assert settings.denylist == ["old-model"]
        assert settings.verbosity == 3

    def test_missing_base_url_raises(self):
        with pytest.raises(ValueError, match="Missing base URL"):
            resolve_settings(base_url=None)

    def test_empty_base_url_raises(self):
        with pytest.raises(ValueError, match="Missing base URL"):
            resolve_settings(base_url="")

    def test_provider_name_auto_derived(self):
        settings = resolve_settings(base_url="https://api.example.com/v1")
        assert settings.provider_name == "example"

    def test_provider_name_explicit_overrides(self):
        settings = resolve_settings(
            base_url="http://localhost:8080/v1",
            provider_name="Custom Name",
        )
        assert settings.provider_name == "Custom Name"

    def test_base_url_normalization_trailing_slash(self):
        settings = resolve_settings(base_url="http://localhost:8080")
        assert settings.base_url == "http://localhost:8080/v1"

    def test_base_url_already_has_v1_unchanged(self):
        settings = resolve_settings(base_url="http://localhost:8080/v1")
        assert settings.base_url == "http://localhost:8080/v1"

    def test_base_url_has_v1_models_strips_models(self):
        settings = resolve_settings(base_url="http://localhost:8080/v1/models")
        assert settings.base_url == "http://localhost:8080/v1"

    def test_base_url_with_path_and_v1_models_strips_models(self):
        settings = resolve_settings(base_url="http://localhost:8080/api/v1/models")
        assert settings.base_url == "http://localhost:8080/api/v1"

    def test_base_url_with_path_appends_v1(self):
        settings = resolve_settings(base_url="http://localhost:8080/api")
        assert settings.base_url == "http://localhost:8080/api/v1"

    def test_http_scheme_accepted(self):
        settings = resolve_settings(base_url="http://localhost:8080/v1")
        assert settings.base_url == "http://localhost:8080/v1"

    def test_https_scheme_accepted(self):
        settings = resolve_settings(base_url="https://api.example.com/v1")
        assert settings.base_url == "https://api.example.com/v1"

    def test_invalid_scheme_raises(self):
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            resolve_settings(base_url="ftp://localhost:8080/v1")

    def test_empty_allowlist(self):
        settings = resolve_settings(
            base_url="http://localhost:8080/v1",
            allowlist="",
        )
        assert settings.allowlist == []

    def test_empty_denylist(self):
        settings = resolve_settings(
            base_url="http://localhost:8080/v1",
            denylist="",
        )
        assert settings.denylist == []


class TestSettingsClass:
    """Test the Settings data container."""

    def test_slots_exist(self):
        settings = Settings(base_url="http://test/v1")
        assert hasattr(settings, "base_url")
        assert hasattr(settings, "api_key")
        assert hasattr(settings, "output_file_path")
        assert hasattr(settings, "provider_name")
        assert hasattr(settings, "provider_npm")
        assert hasattr(settings, "timeout")
        assert hasattr(settings, "model_context_limit")
        assert hasattr(settings, "model_output_limit")
        assert hasattr(settings, "allowlist")
        assert hasattr(settings, "denylist")
        assert hasattr(settings, "verbosity")

    def test_default_values(self):
        settings = Settings(base_url="http://test/v1")
        assert settings.api_key is None
        assert settings.output_file_path is None
        assert settings.provider_name is None
        assert settings.provider_npm == "@ai-sdk/openai-compatible"
        assert settings.timeout == 30
        assert settings.model_context_limit is None
        assert settings.model_output_limit is None
        assert settings.allowlist is None
        assert settings.denylist is None
        assert settings.verbosity == 1
