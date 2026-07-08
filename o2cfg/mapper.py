"""Model Mapper — transform API model objects into opencode schema format."""

from typing import Any


# Known field names that might contain context/output limits in extended model
# objects from compatible servers.
CONTEXT_LIMIT_FIELDS = [
    "max_input_tokens",
    "context_length",
    "max_context_tokens",
    "context_window",
]
OUTPUT_LIMIT_FIELDS = ["max_output_tokens", "max_tokens"]


def _extract_limit(
    model: dict[str, Any], fields: list[str], fallback: int | None
) -> int | None:
    """Extract a token limit from a model object.

    Checks each field name in *fields* in order.  Returns the first integer
    value found, or *fallback* if none is present.

    Parameters
    ----------
    model : dict[str, Any]
        A single model object from the API.
    fields : list[str]
        Field names to check, in priority order.
    fallback : int | None
        Value to return if no field is found in the model object.

    Returns
    -------
    int | None
        The extracted limit, or the fallback value.
    """
    for field in fields:
        value = model.get(field)
        if isinstance(value, int) and value > 0:
            return value
    return fallback


def map_model(
    model: dict[str, Any],
    context_limit: int | None = None,
    output_limit: int | None = None,
) -> dict[str, Any]:
    """Transform a single API model object into opencode schema format.

    Parameters
    ----------
    model : dict[str, Any]
        A model object from the ``/v1/models`` API response.
    context_limit : int | None
        Global override for context token limit.  If the API provides a value,
        it takes precedence; otherwise *context_limit* is used.
    output_limit : int | None
        Global override for output token limit.

    Returns
    -------
    dict[str, Any]
        A dict matching the opencode model schema:
        ``{"name": str, "limit": {"context": int|None, "output": int|None}}``

    Raises
    ------
    ValueError
        If the model object has no ``id`` field.
    """
    model_id = model.get("id")
    if not model_id:
        raise ValueError("Model object missing required 'id' field")

    # Extract context limit: API value first, then global override, then null
    context = _extract_limit(model, CONTEXT_LIMIT_FIELDS, None)
    if context is None:
        context = context_limit

    # Extract output limit: API value first, then global override, then null
    output = _extract_limit(model, OUTPUT_LIMIT_FIELDS, None)
    if output is None:
        output = output_limit

    return {
        "name": model_id,
        "limit": {
            "context": context,
            "output": output,
        },
    }


def map_models(
    models: list[dict[str, Any]],
    context_limit: int | None = None,
    output_limit: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Transform a list of API model objects into an opencode models map.

    Parameters
    ----------
    models : list[dict[str, Any]]
        List of model objects from the API.
    context_limit : int | None
        Global override for context token limit.
    output_limit : int | None
        Global override for output token limit.

    Returns
    -------
    dict[str, dict[str, Any]]
        A mapping of ``{model_id: mapped_model}``.
    """
    result = {}
    for model in models:
        try:
            mapped = map_model(model, context_limit, output_limit)
            result[mapped["name"]] = mapped
        except ValueError:
            # Skip models without an id
            pass
    return result
