"""Provider name derivation from base URL."""

DEFAULT_PROVIDER_NAME = "OpenAI-compatible"


def derive_provider_name(base_url: str) -> str:
    """Derive a provider display name from the base URL hostname.

    Resolution chain:
    1. Parse the hostname from *base_url* (strip scheme and port).
    2. Split into labels by dot.
    3. Take the second-to-last label (the domain name before the TLD).
       If there is only one label, use it as-is.
    4. Lowercase it.
    5. Replace hyphens and underscores with spaces for readability.
    6. If the hostname is empty or unparseable, return the hardcoded default.

    Parameters
    ----------
    base_url : str
        The base URL to derive a name from.

    Returns
    -------
    str
        A human-readable provider name.
    """
    try:
        # Strip scheme
        url = base_url
        if "://" in url:
            url = url.split("://", 1)[1]
        # Strip path
        if "/" in url:
            url = url.split("/", 1)[0]
        # Strip port
        if ":" in url:
            url = url.rsplit(":", 1)[0]

        if not url:
            return DEFAULT_PROVIDER_NAME

        # Split into labels
        labels = url.split(".")

        # Take the second-to-last label, or the only label if there's just one
        if len(labels) >= 2:
            hostname = labels[-2]
        else:
            hostname = labels[0]

        if not hostname:
            return DEFAULT_PROVIDER_NAME

        # Lowercase and replace separators
        name = hostname.lower().replace("-", " ").replace("_", " ")
        return name
    except Exception:
        return DEFAULT_PROVIDER_NAME
