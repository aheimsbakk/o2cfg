"""Integration tests for output writing (stdout and file)."""

import json
import os

import pytest

from o2cfg.output import write_output


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
