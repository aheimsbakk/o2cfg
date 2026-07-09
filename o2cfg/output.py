"""Output writer — build config documents and write to stdout or file."""

import json
import logging
import os
import sys
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


def build_config_document(
    settings: Any,
    models_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build the final opencode configuration document.

    Parameters
    ----------
    settings : Any
        Resolved configuration (needs provider_name, provider_npm, base_url, api_key).
    models_map : dict[str, dict[str, Any]]
        Mapped models from discovery.

    Returns
    -------
    dict[str, Any]
        The configuration document ready for serialization.
    """

    provider_entry: dict[str, Any] = {
        "name": settings.provider_name,
        "npm": settings.provider_npm,
        "options": {
            "baseURL": settings.base_url,
        },
        "models": models_map,
    }

    if settings.api_key:
        provider_entry["options"]["apiKey"] = settings.api_key

    # Use provider_name as the key inside the "provider" object.
    # Replace spaces with hyphens for a valid JSON key.
    key = settings.provider_name.lower().replace(" ", "-")

    document: dict[str, Any] = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            key: provider_entry,
        },
    }

    return document


def write_output(document: dict[str, Any], output_file_path: str | None) -> None:
    """Write the configuration document to stdout or a file.

    When *output_file_path* is ``None``, the JSON is printed to stdout.
    When a path is given, the file is written atomically (tempfile + rename).

    Parameters
    ----------
    document : dict[str, Any]
        The configuration document.
    output_file_path : str | None
        File path to write to, or ``None`` for stdout.

    Raises
    ------
    OSError
        If the file cannot be written.
    """
    json_str = json.dumps(document, indent=2) + "\n"

    if output_file_path is None:
        sys.stdout.write(json_str)
        sys.stdout.flush()
    else:
        _write_file(json_str, output_file_path)


def _write_file(json_str: str, output_file_path: str) -> None:
    """Write JSON string to a file atomically.

    Resolves and validates output path to prevent path traversal.
    Uses tempfile + rename for atomic writes.

    Parameters
    ----------
    json_str : str
        The JSON string to write.
    output_file_path : str
        Path to write the file to.

    Raises
    ------
    OSError
        If the directory does not exist or the file cannot be written.
    """
    resolved = os.path.realpath(output_file_path)
    parent = os.path.dirname(resolved)
    if parent and not os.path.isdir(parent):
        logger.warning("Output directory does not exist: %s", parent)
        raise OSError(f"Output directory does not exist: {parent}")

    dir_name = os.path.dirname(output_file_path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json_str)
        os.replace(tmp_path, output_file_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
