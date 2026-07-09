"""Integration tests for the main run pipeline — overrides and custom providers."""

import json
import os

import pytest

from o2cfg.__main__ import run


class TestRunOverrides:
    """Test override and customization scenarios in the run pipeline."""

    def test_run_with_model_limits_override(self, monkeypatch, temp_output_dir):
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
        assert (
            doc["provider"]["localhost"]["models"]["basic-model"]["limit"]["context"]
            == 100000
        )
        assert (
            doc["provider"]["localhost"]["models"]["basic-model"]["limit"]["output"]
            == 32000
        )

    def test_run_with_denylist(self, monkeypatch, temp_output_dir):
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
        models = doc["provider"]["localhost"]["models"]
        assert "gpt-4o" in models
        assert "claude-3" in models
        assert "gpt-3.5-turbo" not in models

    def test_run_custom_provider_name(self, monkeypatch, temp_output_dir):
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
        assert "my-custom-provider" in doc["provider"]
        assert doc["provider"]["my-custom-provider"]["name"] == "My Custom Provider"

    def test_run_custom_provider_provider(self, monkeypatch, temp_output_dir):
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
        assert doc["provider"]["localhost"]["npm"] == "custom-npm-package"
