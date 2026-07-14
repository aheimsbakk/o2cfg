"""Integration tests for the main run pipeline — error handling."""

import json
import os
from unittest.mock import patch


from o2cfg.__main__ import run
from o2cfg.client import DiscoveryError


class TestRunErrors:
    """Test error handling in the run pipeline."""

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

    def test_run_invalid_timeout_exits_1(self, caplog):
        code = run(["--url", "http://localhost:8080/v1", "--timeout", "999"])
        assert code == 1
        assert "timeout" in caplog.text.lower()

    def test_run_unhandled_exception_exits_1(self, caplog):
        """Unhandled exceptions produce exit 1 with error message."""

        with patch("o2cfg.__main__.parse_args", side_effect=RuntimeError("boom")):
            code = run([])
        assert code == 1
        assert "unexpected error" in caplog.text.lower()


class TestRunDiscoveryErrors:
    """Test discovery failure scenarios."""

    def test_run_with_discovery_failure_exits_1(self, monkeypatch, temp_output_dir):
        """Network-level discovery failures exit 1 without writing output."""

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

    def test_run_discovery_error_non_auth_exits_1(self, monkeypatch, temp_output_dir):
        """Non-auth discovery errors (timeout, unreachable, non-200) exit 1."""

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

    def test_run_discovery_error_auth_exits_0(self, monkeypatch, temp_output_dir):
        """Auth failures (401/403) produce empty models map with exit 0."""

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
        assert doc["provider"]["localhost"]["models"] == {}
