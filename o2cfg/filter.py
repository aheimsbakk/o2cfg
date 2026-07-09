"""Model Filter — apply denylist first, then allowlist to narrow the set."""

import fnmatch
from typing import Any


def filter_models(
    models: list[dict[str, Any]],
    denylist: list[str] | None = None,
    allowlist: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Filter a list of model objects by denylist and allowlist.

    The denylist is applied first, then the allowlist.  When neither list is
    provided, all models pass through unchanged.  An empty allowlist results in
    zero models included.

    Each entry is treated as a glob pattern matched against model IDs using
    Unix shell-style wildcards (``*``, ``?``, ``[seq]``, ``[!seq]``).  For
    example, ``gpt-*`` matches ``gpt-4o``, ``gpt-3.5-turbo``, etc.

    Parameters
    ----------
    models : list[dict[str, Any]]
        The list of model objects from the API response.
    denylist : list[str] | None
        Glob patterns for model IDs to exclude.  Applied first.
    allowlist : list[str] | None
        Glob patterns for model IDs to keep.  Applied after denylist.

    Returns
    -------
    list[dict[str, Any]]
        The filtered list of model objects.
    """
    result = models

    # Apply denylist first
    if denylist:
        result = [
            m
            for m in result
            if not any(fnmatch.fnmatch(m.get("id") or "", pat) for pat in denylist)
        ]

    # Apply allowlist second
    if allowlist is not None:
        # Empty allowlist means zero models
        if not allowlist:
            return []
        result = [
            m
            for m in result
            if any(fnmatch.fnmatch(m.get("id") or "", pat) for pat in allowlist)
        ]

    return result
