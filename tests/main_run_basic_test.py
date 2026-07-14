"""Integration tests for the main run pipeline — happy path (basic)."""

import json
import os


from o2cfg.__main__ import run


class TestRunBasic:
    """Test the main run function with mocked discovery."""

    def test_run_with_mocked_discovery(self, monkeypatch, temp_output_dir):
        """Test a full run with mocked client."""

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
        assert "localhost" in doc["provider"]
        assert "gpt-4o" in doc["provider"]["localhost"]["models"]
        assert "gpt-3.5-turbo" in doc["provider"]["localhost"]["models"]
        assert (
            doc["provider"]["localhost"]["models"]["gpt-4o"]["limit"]["context"]
            == 128000
        )

    def test_run_with_api_key_writes_to_output(self, monkeypatch, temp_output_dir):
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
        assert doc["provider"]["localhost"]["options"]["apiKey"] == "sk-test-123"

    def test_run_stdout_output(self, monkeypatch, capsys):
        def mock_fetch(*args, **kwargs):
            return [{"id": "gpt-4o"}]

        monkeypatch.setattr("o2cfg.__main__.fetch_models", mock_fetch)

        code = run(["--url", "http://localhost:8080/v1"])
        assert code == 0
        captured = capsys.readouterr()
        doc = json.loads(captured.out)
        assert "localhost" in doc["provider"]

    def test_run_with_allowlist(self, monkeypatch, temp_output_dir):
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
        models = doc["provider"]["localhost"]["models"]
        assert "gpt-4o" in models
        assert "claude-3" in models
        assert "gpt-3.5-turbo" not in models
