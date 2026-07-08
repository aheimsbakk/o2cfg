"""Entry point for o2cfg — argparse dispatch, discovery pipeline, and output."""

import argparse
import json
import logging
import os
import sys
import tempfile
from typing import Any

from o2cfg import __version__
from o2cfg.cli import parse_args, resolve_verbosity, get_verbosity_label
from o2cfg.config import resolve_settings, Settings
from o2cfg.client import fetch_models, DiscoveryError
from o2cfg.filter import filter_models
from o2cfg.mapper import map_models


def setup_logging(verbosity: int) -> None:
    """Configure the root logger based on the verbosity level.

    Parameters
    ----------
    verbosity : int
        Integer level (0-3): 0=error, 1=warning, 2=info, 3=debug.
    """
    level_map = {
        0: logging.WARNING,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }
    level = level_map.get(verbosity, logging.WARNING)
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def build_config_document(
    settings: Settings,
    models_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build the final opencode configuration document.

    Parameters
    ----------
    settings : Settings
        Resolved configuration.
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
        # Resolve and validate output path to prevent path traversal
        resolved = os.path.realpath(output_file_path)
        parent = os.path.dirname(resolved)
        if parent and not os.path.isdir(parent):
            raise OSError(f"Output directory does not exist: {parent}")

        # Atomic write: tempfile + rename
        dir_name = os.path.dirname(output_file_path) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(json_str)
            os.replace(tmp_path, output_file_path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def run(argv: list[str] | None = None) -> int:
    """Main entry point for o2cfg.

    Parameters
    ----------
    argv : list[str] | None
        Command-line arguments.  If ``None``, uses ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on error, 2 on missing required args.
    """
    try:
        return _run(argv)
    except Exception:
        logger = logging.getLogger(__name__)
        if logger.level == logging.DEBUG:
            logger.exception("Fatal internal error")
        else:
            logger.error("An unexpected error occurred. Run with -vvv for details.")
        return 1


def _run(argv: list[str] | None = None) -> int:
    """Internal implementation of the run pipeline."""
    # Parse arguments
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse calls sys.exit on --help or version; propagate the code
        return exc.code if isinstance(exc.code, int) else 1

    # Setup logging
    verbosity = resolve_verbosity(args)
    setup_logging(verbosity)
    logger = logging.getLogger(__name__)

    # Resolve settings
    try:
        settings = resolve_settings(
            base_url=args.url,
            api_key=args.api_key,
            output_file_path=args.output,
            provider_name=args.provider_name,
            provider_npm=args.provider_provider,
            timeout=args.timeout,
            model_context_limit=args.model_context_limit,
            model_output_limit=args.model_output_limit,
            allowlist=args.allowlist,
            denylist=args.denylist,
            verbosity=verbosity,
        )
    except ValueError as exc:
        logger.error("%s", exc)
        return 2

    # Validate timeout range
    if settings.timeout < 1 or settings.timeout > 300:
        logger.error("Timeout must be between 1 and 300 seconds.")
        return 1

    # Fetch models from API
    models_list: list[dict[str, Any]] = []
    discovery_error: DiscoveryError | None = None

    try:
        models_list = fetch_models(
            base_url=settings.base_url,
            api_key=settings.api_key,
            timeout=settings.timeout,
        )
    except DiscoveryError as exc:
        discovery_error = exc
        logger.warning("Model discovery failed: %s", exc)
        # Auth failures (401/403) produce empty models map with exit 0.
        # All other failures (timeout, unreachable, non-200, invalid JSON) exit 1.
        if exc.status_code not in (401, 403):
            return 1

    # Filter models
    filtered = filter_models(
        models_list,
        denylist=settings.denylist,
        allowlist=settings.allowlist,
    )

    # Map models to opencode schema
    models_map = map_models(
        filtered,
        context_limit=settings.model_context_limit,
        output_limit=settings.model_output_limit,
    )

    if discovery_error and not models_map:
        logger.info("No models discovered; output will have an empty models map.")

    # Build config document
    document = build_config_document(settings, models_map)

    # Write output
    try:
        write_output(document, settings.output_file_path)
    except OSError as exc:
        logger.error("Failed to write output: %s", exc)
        return 1

    return 0


def main() -> None:
    """Entry point called by the console script."""
    sys.exit(run())


if __name__ == "__main__":
    main()
