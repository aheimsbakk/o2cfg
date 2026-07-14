"""Tests for o2cfg OpenAI Client."""

import pytest
from o2cfg.client import fetch_models, DiscoveryError, redact_api_key


class TestRedactApiKey:
    """Test API key redaction."""

    def test_redacts_bearer_token(self):
        assert redact_api_key("Bearer sk-secret-key") == "Bearer sk-****"

    def test_empty_string(self):
        assert redact_api_key("") == ""

    def test_none(self):
        assert redact_api_key(None) == ""

    def test_non_bearer_scheme(self):
        assert redact_api_key("Basic dXNlcjpwYXNz") == "Basic dXNlcjpwYXNz"


class TestFetchModels:
    """Test the fetch_models HTTP client function."""

    def test_success_with_models(self, mock_urlopen_success):
        models = fetch_models("http://localhost:8080/v1")
        assert len(models) == 3
        assert models[0]["id"] == "gpt-4o"
        mock_urlopen_success.assert_called_once()

    def test_success_without_api_key(self, mock_urlopen_success):
        models = fetch_models("http://localhost:8080/v1")
        assert len(models) == 3

    def test_success_with_api_key(self, mock_urlopen_success):
        models = fetch_models("http://localhost:8080/v1", api_key="sk-test-123")
        assert len(models) == 3
        call_args = mock_urlopen_success.call_args
        req = call_args[0][0]
        assert req.get_header("Authorization") == "Bearer sk-test-123"

    def test_empty_models_list(self, mock_urlopen_empty):
        models = fetch_models("http://localhost:8080/v1")
        assert models == []

    def test_http_401_error(self, mock_urlopen_http_error):
        with pytest.raises(DiscoveryError) as exc_info:
            fetch_models("http://localhost:8080/v1", api_key="bad-key")
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    def test_http_timeout(self, mock_urlopen_timeout):
        with pytest.raises(DiscoveryError) as exc_info:
            fetch_models("http://localhost:8080/v1", timeout=5)
        assert "timed out" in str(exc_info.value).lower()
        assert exc_info.value.status_code is None

    def test_invalid_json_response(self, mock_urlopen_invalid_json):
        with pytest.raises(DiscoveryError) as exc_info:
            fetch_models("http://localhost:8080/v1")
        assert "Invalid JSON" in str(exc_info.value)

    def test_timeout_parameter_used(self, mock_urlopen_success):
        fetch_models("http://localhost:8080/v1", timeout=42)
        call_args = mock_urlopen_success.call_args
        assert call_args[1]["timeout"] == 42

    def test_url_construction(self, mock_urlopen_success):
        fetch_models("http://localhost:8080/v1")
        call_args = mock_urlopen_success.call_args
        req = call_args[0][0]
        assert req.full_url == "http://localhost:8080/v1/models"

    def test_no_auth_header_without_key(self, mock_urlopen_success):
        fetch_models("http://localhost:8080/v1", api_key=None)
        call_args = mock_urlopen_success.call_args
        req = call_args[0][0]
        assert req.get_header("Authorization") is None
