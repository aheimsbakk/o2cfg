"""OpenAI Client — HTTP GET /v1/models with timeout, auth header, error handling."""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Optional


logger = logging.getLogger(__name__)


class DiscoveryError(Exception):
    """Raised when the model discovery HTTP request fails."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, url: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


def redact_api_key(header_value: Optional[str]) -> str:
    """Redact the Bearer token portion of an Authorization header value.

    Returns the original string with the token replaced by ``sk-****``.
    """
    if not header_value:
        return ""
    if header_value.startswith("Bearer "):
        return "Bearer sk-****"
    return header_value


def fetch_models(
    base_url: str,
    api_key: Optional[str] = None,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """Fetch the list of models from an OpenAI-compatible API endpoint.

    Parameters
    ----------
    base_url : str
        The base URL (e.g. ``http://localhost:8080/v1``).  The function
        appends ``/models`` to form the full endpoint.
    api_key : str | None
        Bearer token for authenticated endpoints.  If ``None``, the request
        is sent without an ``Authorization`` header.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    list[dict[str, Any]]
        A list of model objects as returned by the API (each is a dict).

    Raises
    ------
    DiscoveryError
        On network errors, timeouts, non-200 responses, or invalid JSON.
    """
    url = base_url + "/models"
    logger.debug("Fetching models from %s (timeout=%ds)", url, timeout)

    req = urllib.request.Request(url)

    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
        logger.debug(
            "Authorization header set (redacted: %s)",
            redact_api_key(req.get_header("Authorization")),
        )
    else:
        logger.info("No API key provided; sending request without authorization")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8")

            if status != 200:
                # Try to parse error body for context
                error_detail = ""
                try:
                    error_body = json.loads(body)
                    error_detail = error_body.get("error", {}).get("message", "")
                except (json.JSONDecodeError, ValueError):
                    error_detail = body[:500] if body else "(empty body)"

                raise DiscoveryError(
                    f"HTTP {status} from {url}: {error_detail}",
                    status_code=status,
                    url=url,
                )

            # Parse the JSON response
            try:
                data = json.loads(body)
            except json.JSONDecodeError as exc:
                raise DiscoveryError(
                    f"Invalid JSON response from {url}: {exc}",
                    status_code=status,
                    url=url,
                )

            # Extract the models list
            models = data.get("data", [])
            if not isinstance(models, list):
                raise DiscoveryError(
                    f"Expected 'data' to be a list in response from {url}, got {type(models).__name__}",
                    status_code=status,
                    url=url,
                )

            logger.info("Discovered %d models from %s", len(models), url)
            return models

    except urllib.error.HTTPError as exc:
        # urllib.error.HTTPError is a subclass of URLError
        status = exc.code if exc.code else None
        error_detail = ""
        try:
            # HTTPError.fp contains the response body
            if exc.fp:
                body_bytes = exc.fp.read()
                body = body_bytes.decode("utf-8", errors="replace")
                try:
                    error_body = json.loads(body)
                    error_detail = error_body.get("error", {}).get("message", "")
                except (json.JSONDecodeError, ValueError):
                    error_detail = body[:500] if body else "(empty body)"
        except Exception:
            # If we can't read the body, keep error_detail empty
            pass

        raise DiscoveryError(
            f"HTTP {status} from {url}: {error_detail}"
            if error_detail
            else f"HTTP error {status} from {url}",
            status_code=status,
            url=url,
        )

    except urllib.error.URLError as exc:
        reason = str(exc.reason) if exc.reason else str(exc)
        if "timed out" in reason.lower():
            raise DiscoveryError(
                f"Request to {url} timed out after {timeout}s",
                status_code=None,
                url=url,
            )
        raise DiscoveryError(
            f"Network error connecting to {url}: {reason}",
            status_code=None,
            url=url,
        )

    except Exception as exc:
        raise DiscoveryError(
            f"Unexpected error fetching models from {url}: {exc}",
            status_code=None,
            url=url,
        )
