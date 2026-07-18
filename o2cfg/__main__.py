"""Entry point for o2cfg — argparse dispatch, discovery pipeline, and output."""

import logging
import sys
from typing import Any

from o2cfg.cli import parse_args, resolve_verbosity
from o2cfg.client import DiscoveryError, fetch_models
from o2cfg.config import resolve_settings
from o2cfg.filter import filter_models
from o2cfg.mapper import map_models
from o2cfg.output import build_config_document, write_output


def setup_logging(verbosity: int) -> None:
    """Configure the root logger based on the verbosity level.

    Parameters
    ----------
    verbosity : int
        Integer level (0-3): 0=error, 1=warning, 2=info, 3=debug.
    """
    level_map = {
        0: logging.ERROR,
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
            vision=args.vision,
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
    if settings.denylist or settings.allowlist is not None:
        logger.info(
            "Applying filters: denylist=%s, allowlist=%s",
            settings.denylist,
            settings.allowlist,
        )
    filtered = filter_models(
        models_list,
        denylist=settings.denylist,
        allowlist=settings.allowlist,
    )
    if settings.denylist or settings.allowlist is not None:
        removed = len(models_list) - len(filtered)
        if removed > 0:
            logger.info("Removed %d models after filtering", removed)
        if not filtered:
            logger.info("No models remain after filtering")

    # Map models to opencode schema
    models_map = map_models(
        filtered,
        context_limit=settings.model_context_limit,
        output_limit=settings.model_output_limit,
        vision_patterns=settings.vision,
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

    if settings.output_file_path:
        logger.info("Config written to %s", settings.output_file_path)
    else:
        logger.info("Config written to stdout")

    return 0


def main() -> None:
    """Entry point called by the console script."""
    sys.exit(run())


if __name__ == "__main__":
    main()
