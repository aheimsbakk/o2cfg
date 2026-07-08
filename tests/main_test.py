"""Integration tests for o2cfg.__main__ (run function and output writer)."""

import json
import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from o2cfg.__main__ import build_config_document, run, write_output
from o2cfg.config import Settings


class TestBuildConfigDocument:
    """Test config document construction."""

    def test_without_api_key(self):
        settings = Settings(
            base_url="http://localhost:8080/v1",
            provider_name="localhost",
            provider_npm="@ai-sdk/openai-compatible",
        )
        models_map = {
            "gpt-4o": {
                "name": "gpt-4o",
                "limit": {"context": 128000, "output": 4096},
            }
        }
        doc = build_config_document(settings, models_map)
        assert doc["$schema"] == "https://opencode.ai/config.json"
        assert "localhost" in doc
        provider = doc["localhost"]
        assert provider["name"] == "localhost"
        assert provider["npm"] == "@ai-sdk/openai-compatible"
        assert provider["options"]["baseURL"] == "http://localhost:8080/v1"
        assert "apiKey" not in provider["options"]
        assert "gpt-4o" in provider["models"]

    def test_with_api_key(self):
        settings = Settings(
            base_url="https://api.example.com/v1",
            api_key="sk-test-123",
            provider_name="my-provider",
            provider_npm="custom-npm",
        )
        models_map = {}
        doc = build_config_document(settings, models_map)
        provider = doc["my-provider"]
        assert provider["options"]["apiKey"] == "sk-test-123"
        assert provider["options"]["baseURL"] == "https://api.example.com/v1"

    def test_provider_name_with_spaces_becomes_key(self):
        settings = Settings(
            base_url="http://localhost:8080/v1",
            provider_name="My Provider",
        )
        doc = build_config_document(settings, {})
        assert "my-provider" in doc
        assert "My Provider" not in doc


class TestWriteOutput:
    """Test output writing to stdout and file."""

    def test_stdout_output(self, capsys):
        doc = {"$schema": "https://opencode.ai/config.json", "test": {}}
        write_output(doc, None)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["$schema"] == "https://opencode.ai/config.json"
        assert parsed["test"] == {}

    def test_file_output(self, temp_output_dir, tmp_path):
        doc = {"$schema": "https://opencode.ai/config.json", "test": {"key": "value"}}
        output_path = os.path.join(temp_output_dir, "config.json")
        write_output(doc, output_path)
        with open(output_path) as f:
            parsed = json.load(f)
        assert parsed["$schema"] == "https://opencode.ai/config.json"
        assert parsed["test"]["key"] == "value"

    def test_file_output_creates_in_existing_dir(self, temp_output_dir, tmp_path):
        doc = {"test": 1}
        output_path = os.path.join(temp_output_dir, "nested", "config.json")
        # Create the directory first (simulating existing directory)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        write_output(doc, output_path)
        with open(output_path) as f:
            assert json.load(f) == {"test": 1}

    def test_file_output_overwrites_existing(self, temp_output_dir, tmp_path):
        output_path = os.path.join(temp_output_dir, "config.json")
        # Write initial content
        with open(output_path, "w") as f:
            f.write('{"old": true}')
        # Overwrite
        write_output({"new": True}, output_path)
        with open(output_path) as f:
            assert json.load(f) == {"new": True}

    def test_file_output_missing_dir_raises(self, tmp_path):
        doc = {"test": 1}
        output_path = os.path.join(str(tmp_path), "nonexistent", "config.json")
        with pytest.raises(OSError, match="Output directory does not exist"):
            write_output(doc, output_path)


class TestRun:
    """Test the main run function."""

    def test_run_missing_url_exits_2(self, caplog):
        code = run([])
        assert code == 2
        assert "Missing base URL" in caplog.text

    def test_run_missing_url_env_var_exits_2(self, monkeypatch):
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        def mock_fetch(*args, **kwargs):
            return [{"id": "gpt-4o"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)
        code = run(["--url", "http://localhost:8080/v1"])
        assert code == 0  # URL provided via flag

    def test_run_with_mocked_discovery(self, monkeypatch, temp_output_dir, tmp_path):
        """Test a full run with mocked client."""
        from o2cfg.client import fetch_models

        def mock_fetch(*args, **kwargs):
            return [
                {"id": "gpt-4o", "max_input_tokens": 128000, "max_output_tokens": 4096},
                {
                    "id": "gpt-3.5-turbo",
                    "max_input_tokens": 16385,
                    "max_output_tokens": 4096,
                },
            ]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            ["--url", "http://localhost:8080/v1", "--output", output_path, "-vv"]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        assert "localhost" in doc
        assert "gpt-4o" in doc["localhost"]["models"]
        assert "gpt-3.5-turbo" in doc["localhost"]["models"]
        assert doc["localhost"]["models"]["gpt-4o"]["limit"]["context"] == 128000

    def test_run_with_api_key_writes_to_output(
        self, monkeypatch, temp_output_dir, tmp_path
    ):
        def mock_fetch(*args, **kwargs):
            return [{"id": "gpt-4o"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            [
                "--url",
                "http://localhost:8080/v1",
                "--api-key",
                "sk-test-123",
                "--output",
                output_path,
            ]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        assert doc["localhost"]["options"]["apiKey"] == "sk-test-123"

    def test_run_stdout_output(self, monkeypatch, capsys):
        def mock_fetch(*args, **kwargs):
            return [{"id": "gpt-4o"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        code = run(["--url", "http://localhost:8080/v1"])
        assert code == 0
        captured = capsys.readouterr()
        doc = json.loads(captured.out)
        assert "localhost" in doc

    def test_run_with_discovery_failure_produces_empty_models(
        self, monkeypatch, temp_output_dir, tmp_path
    ):
        """Network-level discovery failures exit 1 (not 0)."""
        from o2cfg.client import DiscoveryError

        def mock_fetch(*args, **kwargs):
            raise DiscoveryError(
                "Connection refused", url="http://localhost:8080/v1/models"
            )

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            ["--url", "http://localhost:8080/v1", "--output", output_path, "-vv"]
        )
        assert code == 1

    def test_run_with_allowlist(self, monkeypatch, temp_output_dir, tmp_path):
        def mock_fetch(*args, **kwargs):
            return [
                {"id": "gpt-4o"},
                {"id": "gpt-3.5-turbo"},
                {"id": "claude-3"},
            ]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            [
                "--url",
                "http://localhost:8080/v1",
                "--output",
                output_path,
                "--allowlist",
                "gpt-4o,claude-3",
            ]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        models = doc["localhost"]["models"]
        assert "gpt-4o" in models
        assert "claude-3" in models
        assert "gpt-3.5-turbo" not in models

    def test_run_with_denylist(self, monkeypatch, temp_output_dir, tmp_path):
        def mock_fetch(*args, **kwargs):
            return [
                {"id": "gpt-4o"},
                {"id": "gpt-3.5-turbo"},
                {"id": "claude-3"},
            ]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            [
                "--url",
                "http://localhost:8080/v1",
                "--output",
                output_path,
                "--denylist",
                "gpt-3.5-turbo",
            ]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        models = doc["localhost"]["models"]
        assert "gpt-4o" in models
        assert "claude-3" in models
        assert "gpt-3.5-turbo" not in models

    def test_run_with_model_limits_override(
        self, monkeypatch, temp_output_dir, tmp_path
    ):
        def mock_fetch(*args, **kwargs):
            return [{"id": "basic-model"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            [
                "--url",
                "http://localhost:8080/v1",
                "--output",
                output_path,
                "--model-context-limit",
                "100000",
                "--model-output-limit",
                "32000",
            ]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        assert doc["localhost"]["models"]["basic-model"]["limit"]["context"] == 100000
        assert doc["localhost"]["models"]["basic-model"]["limit"]["output"] == 32000

    def test_run_invalid_timeout_exits_1(self, caplog):
        code = run(["--url", "http://localhost:8080/v1", "--timeout", "999"])
        assert code == 1
        assert "timeout" in caplog.text.lower()

    def test_run_custom_provider_name(self, monkeypatch, temp_output_dir, tmp_path):
        def mock_fetch(*args, **kwargs):
            return [{"id": "gpt-4o"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            [
                "--url",
                "http://localhost:8080/v1",
                "--output",
                output_path,
                "--provider-name",
                "My Custom Provider",
            ]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        assert "my-custom-provider" in doc
        assert doc["my-custom-provider"]["name"] == "My Custom Provider"

    def test_run_custom_provider_provider(self, monkeypatch, temp_output_dir, tmp_path):
        def mock_fetch(*args, **kwargs):
            return [{"id": "gpt-4o"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            [
                "--url",
                "http://localhost:8080/v1",
                "--output",
                output_path,
                "--provider-provider",
                "custom-npm-package",
            ]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        assert doc["localhost"]["npm"] == "custom-npm-package"

    def test_run_discovery_error_non_auth_exits_1(
        self, monkeypatch, temp_output_dir, tmp_path
    ):
        """Non-auth discovery errors (timeout, unreachable, non-200) exit 1."""
        from o2cfg.client import DiscoveryError

        def mock_fetch(*args, **kwargs):
            raise DiscoveryError(
                "Connection refused",
                status_code=500,
                url="http://localhost:8080/v1/models",
            )

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            ["--url", "http://localhost:8080/v1", "--output", output_path, "-vv"]
        )
        assert code == 1

    def test_run_discovery_error_auth_exits_0(
        self, monkeypatch, temp_output_dir, tmp_path
    ):
        """Auth failures (401/403) produce empty models map with exit 0."""
        from o2cfg.client import DiscoveryError

        def mock_fetch(*args, **kwargs):
            raise DiscoveryError(
                "Unauthorized",
                status_code=401,
                url="http://localhost:8080/v1/models",
            )

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        output_path = os.path.join(temp_output_dir, "config.json")
        code = run(
            ["--url", "http://localhost:8080/v1", "--output", output_path, "-vv"]
        )
        assert code == 0
        with open(output_path) as f:
            doc = json.load(f)
        assert doc["localhost"]["models"] == {}

    def test_run_unhandled_exception_exits_1(self, caplog):
        """Unhandled exceptions produce exit 1 with error message."""
        from unittest.mock import patch

        with patch("o2cfg.__main__.parse_args", side_effect=RuntimeError("boom")):
            code = run([])
        assert code == 1
        assert "unexpected error" in caplog.text.lower()
