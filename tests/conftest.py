"""Shared fixtures for o2cfg tests."""

import json
from unittest.mock import MagicMock, patch

import pytest


SAMPLE_MODELS_RESPONSE = {
    "object": "list",
    "data": [
        {
            "id": "gpt-4o",
            "object": "model",
            "created": 1700000000,
            "owned_by": "openai",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
        },
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": 1700000000,
            "owned_by": "openai",
            "max_input_tokens": 16385,
            "max_output_tokens": 4096,
        },
        {
            "id": "claude-3-opus",
            "object": "model",
            "created": 1700000000,
            "owned_by": "anthropic",
            "context_length": 200000,
        },
    ],
}


SAMPLE_MODELS_RESPONSE_EMPTY = {
    "object": "list",
    "data": [],
}


SAMPLE_MODELS_RESPONSE_WITH_LIMITS = {
    "object": "list",
    "data": [
        {
            "id": "custom-model",
            "object": "model",
            "created": 1700000000,
            "owned_by": "test",
            "max_input_tokens": 256000,
            "max_output_tokens": 64000,
        },
        {
            "id": "no-limits-model",
            "object": "model",
            "created": 1700000000,
            "owned_by": "test",
        },
    ],
}


@pytest.fixture
def sample_models_response():
    """Return the sample /v1/models response dict."""
    return SAMPLE_MODELS_RESPONSE


@pytest.fixture
def sample_models_response_empty():
    """Return an empty /v1/models response dict."""
    return SAMPLE_MODELS_RESPONSE_EMPTY


@pytest.fixture
def sample_models_response_with_limits():
    """Return a /v1/models response with mixed limit fields."""
    return SAMPLE_MODELS_RESPONSE_WITH_LIMITS


@pytest.fixture
def mock_urlopen_success(sample_models_response):
    """Mock urllib.request.urlopen to return a successful JSON response."""
    response = MagicMock()
    response.status = 200
    response.read.return_value = json.dumps(sample_models_response).encode("utf-8")
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch("o2cfg.client.urllib.request.urlopen", return_value=response) as mock:
        yield mock


@pytest.fixture
def mock_urlopen_empty(sample_models_response_empty):
    """Mock urllib.request.urlopen to return an empty models list."""
    response = MagicMock()
    response.status = 200
    response.read.return_value = json.dumps(sample_models_response_empty).encode(
        "utf-8"
    )
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch("o2cfg.client.urllib.request.urlopen", return_value=response) as mock:
        yield mock


@pytest.fixture
def mock_urlopen_http_error():
    """Mock urllib.request.urlopen to raise an HTTPError with a readable body."""
    import urllib.error

    from email.message import Message
    from io import BytesIO

    headers = Message()
    error_body = b'{"error": {"message": "Invalid API key"}}'
    fp = BytesIO(error_body)

    # Create the error and reset fp position so read() works
    error = urllib.error.HTTPError(
        url="http://localhost:8080/v1/models",
        code=401,
        msg="Unauthorized",
        hdrs=headers,
        fp=fp,
    )
    fp.seek(0)

    with patch("o2cfg.client.urllib.request.urlopen", side_effect=error) as mock:
        yield mock


@pytest.fixture
def mock_urlopen_timeout():
    """Mock urllib.request.urlopen to raise a URLError (timeout)."""
    import urllib.error

    error = urllib.error.URLError("timed out")

    with patch("o2cfg.client.urllib.request.urlopen", side_effect=error) as mock:
        yield mock


@pytest.fixture
def mock_urlopen_invalid_json():
    """Mock urllib.request.urlopen to return invalid JSON."""
    response = MagicMock()
    response.status = 200
    response.read.return_value = b"not valid json {{{"
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch("o2cfg.client.urllib.request.urlopen", return_value=response) as mock:
        yield mock


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for output file tests."""
    return str(tmp_path)
