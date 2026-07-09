"""Config Resolver — merges CLI args + environment variables into resolved settings."""

import logging
import urllib.parse
from typing import Optional

from o2cfg.provider_name import derive_provider_name


logger = logging.getLogger(__name__)


class Settings:
    """Holds all resolved configuration values for a single invocation."""

    __slots__ = (
        "base_url",
        "api_key",
        "output_file_path",
        "provider_name",
        "provider_npm",
        "timeout",
        "model_context_limit",
        "model_output_limit",
        "allowlist",
        "denylist",
        "verbosity",
    )

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        output_file_path: Optional[str] = None,
        provider_name: Optional[str] = None,
        provider_npm: str = "@ai-sdk/openai-compatible",
        timeout: int = 30,
        model_context_limit: Optional[int] = None,
        model_output_limit: Optional[int] = None,
        allowlist: Optional[list[str]] = None,
        denylist: Optional[list[str]] = None,
        verbosity: int = 1,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.output_file_path = output_file_path
        self.provider_name = provider_name
        self.provider_npm = provider_npm
        self.timeout = timeout
        self.model_context_limit = model_context_limit
        self.model_output_limit = model_output_limit
        self.allowlist = allowlist
        self.denylist = denylist
        self.verbosity = verbosity


def _parse_comma_list(value: Optional[str]) -> Optional[list[str]]:
    """Parse a comma-separated string into a list of stripped, non-empty strings.

    Returns ``None`` when *value* is ``None``.  Returns an empty list when the
    string is empty or contains only whitespace / commas.
    """
    if value is None:
        return None
    parts = [p.strip() for p in value.split(",")]
    result = [p for p in parts if p]
    return result if result else []


def resolve_settings(
    base_url: Optional[str],
    api_key: Optional[str] = None,
    output_file_path: Optional[str] = None,
    provider_name: Optional[str] = None,
    provider_npm: str = "@ai-sdk/openai-compatible",
    timeout: int = 30,
    model_context_limit: Optional[int] = None,
    model_output_limit: Optional[int] = None,
    allowlist: Optional[str] = None,
    denylist: Optional[str] = None,
    verbosity: int = 1,
) -> Settings:
    """Merge CLI arguments and environment variables into a ``Settings`` object.

    Parameters
    ----------
    base_url : str | None
        The base URL from the CLI flag or ``OPENAI_BASE_URL`` env var.
    api_key : str | None
        The API key from the CLI flag or ``OPENAI_API_KEY`` env var.
    output_file_path : str | None
        Path from ``--output``, or ``None`` for stdout.
    provider_name : str | None
        Display name from ``--provider-name``, or ``None`` for auto-resolution.
    provider_npm : str
        npm package name for the provider adapter.
    timeout : int
        HTTP timeout in seconds.
    model_context_limit : int | None
        Global context limit override.
    model_output_limit : int | None
        Global output limit override.
    allowlist : str | None
        Comma-separated model IDs to keep.
    denylist : str | None
        Comma-separated model IDs to exclude.
    verbosity : int
        Integer verbosity level (0-3).

    Returns
    -------
    Settings
        Resolved configuration object.

    Raises
    ------
    ValueError
        When *base_url* is ``None`` or empty.
    """
    if not base_url:
        raise ValueError(
            "Missing base URL. Provide --url <URL> or set OPENAI_BASE_URL environment variable."
        )

    # Validate scheme: only http and https are allowed
    parsed_url = urllib.parse.urlparse(base_url)
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError(
            f"Invalid URL scheme '{parsed_url.scheme}'. Only 'http' and 'https' are allowed."
        )

    # Derive provider name if not explicitly provided
    if not provider_name:
        provider_name = derive_provider_name(base_url)

    # Parse allowlist and denylist
    allow_list = _parse_comma_list(allowlist)
    deny_list = _parse_comma_list(denylist)

    # Normalize base_url: ensure it ends with /v1 (the prefix for the models endpoint).
    # The client appends /models, so the full URL is base_url + "/models".
    # If the URL already ends with /v1/models, strip /models first.
    if base_url.endswith("/v1/models"):
        base_url = base_url[: -len("/models")]
    # Ensure base URL ends with /v1.
    if not base_url.endswith("/v1"):
        if base_url.endswith("/"):
            base_url = base_url + "v1"
        else:
            base_url = base_url + "/v1"

    return Settings(
        base_url=base_url,
        api_key=api_key,
        output_file_path=output_file_path,
        provider_name=provider_name,
        provider_npm=provider_npm,
        timeout=timeout,
        model_context_limit=model_context_limit,
        model_output_limit=model_output_limit,
        allowlist=allow_list,
        denylist=deny_list,
        verbosity=verbosity,
    )
