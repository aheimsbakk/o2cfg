"""Argument parsing for the o2cfg CLI."""

import argparse
import os
import sys


VERSION = "0.1.0"

DEFAULT_PROVIDER = "@ai-sdk/openai-compatible"
DEFAULT_TIMEOUT = 30
MIN_TIMEOUT = 1
MAX_TIMEOUT = 300

VERBOSITY_MAP = {
    0: "warning",
    1: "warning",
    2: "info",
    3: "debug",
}


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns an ArgumentParser configured with all CLI flags described in the
    blueprint.  The parser does not parse anything — callers must invoke
    ``parse_args`` or ``parse_known_args`` themselves.
    """
    parser = argparse.ArgumentParser(
        prog="o2cfg",
        description="Auto-discover models from OpenAI-compatible API endpoints and generate opencode provider configurations.",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=VERSION,
    )

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="Set verbosity: -v (warning), -vv (info), -vvv (debug). Default: warning.",
    )

    parser.add_argument(
        "-u",
        "--url",
        type=str,
        default=os.environ.get("OPENAI_BASE_URL"),
        help="Base URL of the OpenAI-compatible endpoint (e.g. http://localhost:8080/v1). Falls back to OPENAI_BASE_URL env var.",
    )

    parser.add_argument(
        "-k",
        "--api-key",
        type=str,
        default=os.environ.get("OPENAI_API_KEY"),
        help="Bearer token for authenticated endpoints. Falls back to OPENAI_API_KEY env var.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="File path to write the generated config. Defaults to stdout.",
    )

    parser.add_argument(
        "-n",
        "--provider-name",
        type=str,
        default=None,
        help="Display name for the provider entry. Defaults to auto-resolution from URL hostname.",
    )

    parser.add_argument(
        "-p",
        "--provider-provider",
        type=str,
        default=DEFAULT_PROVIDER,
        help=f"npm package name for the provider adapter. Default: {DEFAULT_PROVIDER}",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP request timeout in seconds ({MIN_TIMEOUT}-{MAX_TIMEOUT}). Default: {DEFAULT_TIMEOUT}",
    )

    parser.add_argument(
        "-C",
        "--model-context-limit",
        type=int,
        default=None,
        help="Global override for context token limit when API returns no value.",
    )

    parser.add_argument(
        "-O",
        "--model-output-limit",
        type=int,
        default=None,
        help="Global override for output token limit when API returns no value.",
    )

    parser.add_argument(
        "-a",
        "--allowlist",
        type=str,
        default=None,
        help="Comma-separated list of model IDs to keep. Discovered models not in this list are excluded.",
    )

    parser.add_argument(
        "-d",
        "--denylist",
        type=str,
        default=None,
        help="Comma-separated list of model IDs to exclude, even if they were discovered.",
    )

    return parser


def parse_args(argv=None):
    """Parse command-line arguments and return the parsed namespace.

    Parameters
    ----------
    argv : list[str] | None
        Argument list to parse.  If ``None``, ``sys.argv[1:]`` is used.

    Returns
    -------
    argparse.Namespace
        The parsed arguments.
    """
    parser = build_parser()
    return parser.parse_args(argv)


def resolve_verbosity(args) -> int:
    """Return an integer verbosity level (0-3) from parsed args.

    The ``-v`` / ``--verbosity`` flag uses ``action="count"``, so each
    occurrence increments the counter.  The default (0) maps to warning (1)
    so that no flags and a single ``-v`` both produce warning-level output.
    Values above 3 are capped at 3.
    """
    level = args.verbosity
    if level == 0:
        return 1
    return min(level, 3)


def get_verbosity_label(level: int) -> str:
    """Return a human-readable verbosity label for the given integer level."""
    return VERBOSITY_MAP.get(level, "warning")
