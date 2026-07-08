"""Model Filter — apply denylist first, then allowlist to narrow the set."""

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

    Parameters
    ----------
    models : list[dict[str, Any]]
        The list of model objects from the API response.
    denylist : list[str] | None
        Model IDs to exclude.  Applied first.
    allowlist : list[str] | None
        Model IDs to keep.  Applied after denylist.

    Returns
    -------
    list[dict[str, Any]]
        The filtered list of model objects.
    """
    result = models

    # Apply denylist first
    if denylist:
        deny_set = set(denylist)
        result = [m for m in result if m.get("id") not in deny_set]
        if result:
            removed = len(models) - len(result)
            if removed > 0:
                pass  # logging handled by caller

    # Apply allowlist second
    if allowlist is not None:
        # Empty allowlist means zero models
        allow_set = set(allowlist)
        result = [m for m in result if m.get("id") in allow_set]

    return result
